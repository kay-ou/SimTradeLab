# -*- coding: utf-8 -*-
"""
回测执行器 - 重构版

职责：编排回测流程，协调各组件工作
"""

import numpy as np
import pandas as pd
import signal
import logging
import os

from simtradelab.ptrade.context import Context
from simtradelab.ptrade.object import Global, Portfolio, BacktestContext
from simtradelab.backtest.stats import generate_backtest_report, generate_backtest_charts, print_backtest_report
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.service.data_server import DataServer, load_data_from_hdf5
from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.stats_collector import StatsCollector
from simtradelab.ptrade.strategy_engine import StrategyExecutionEngine
from simtradelab.ptrade.strategy_validator import validate_strategy_file
from simtradelab.utils.perf import timer, get_current_elapsed_time


class BacktestRunner:
    """回测执行器 - 负责编排整个回测流程"""

    def __init__(self, data_path: str = None, use_data_server: bool = True):
        """初始化回测执行器

        Args:
            data_path: 数据文件路径，为None时使用默认路径
            use_data_server: 是否使用数据服务器（常驻内存）
        """
        # 使用统一路径管理
        if data_path is None:
            from simtradelab.utils.paths import DATA_PATH
            data_path = str(DATA_PATH)

        self.data_path = data_path
        self.use_data_server = use_data_server

        # 数据容器（延迟加载）
        self._data_loaded = False
        self.stock_data_dict = None
        self.valuation_dict = None
        self.fundamentals_dict = None
        self.exrights_dict = None
        self.benchmark_data = None
        self.stock_metadata = None
        self.index_constituents = {}
        self.stock_status_history = {}
        self.stock_data_store = None
        self.fundamentals_store = None
        self.adj_pre_cache = None
        self.dividend_cache = None

        # 全局对象
        self.g = Global()
        self.log = None
        self.context = None

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)

    @timer(name="总耗时（含数据加载）")
    def run(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0
    ) -> dict:
        """运行回测

        Args:
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金

        Returns:
            回测报告字典
        """
        # 构建配置
        config = BacktestConfig(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            data_path=self.data_path,
            initial_capital=initial_capital,
            use_data_server=self.use_data_server
        )

        # 先验证策略，避免数据加载后才发现策略错误
        print("检查策略...")
        is_valid, errors = validate_strategy_file(config.strategy_path)
        if not is_valid:
            print("\n策略验证失败:")
            for error in errors:
                print("  - {}".format(error))
            return {}
        print("策略检查通过\n")

        # 分析策略数据依赖
        print("分析策略数据依赖...")
        from simtradelab.ptrade.strategy_data_analyzer import (
            analyze_strategy_data_requirements,
            print_dependencies
        )
        deps = analyze_strategy_data_requirements(config.strategy_path)
        print_dependencies(deps)
        print("")

        # 转换为数据加载参数
        required_data = set()
        if deps.needs_price_data:
            required_data.add('price')
        if deps.needs_valuation:
            required_data.add('valuation')
        if deps.needs_fundamentals:
            required_data.add('fundamentals')
        if deps.needs_exrights:
            required_data.add('exrights')

        try:
            # 加载数据（仅首次或非服务器模式）
            benchmark_df = self._load_data(required_data)

            # 初始化日志
            self._setup_logging(config)

            self.log.info(f"开始运行回测, 策略名称: {strategy_name}")
            self.log.info(f"回测周期: {config.start_date.date()} 至 {config.end_date.date()}")

            # 创建交易日序列
            date_range = self._create_date_range(benchmark_df, config.start_date, config.end_date)

            if len(date_range) == 0:
                self.log.error(f"错误：交易日序列为空！请检查日期范围 {config.start_date.date()} - {config.end_date.date()}")
                self.log.error(f"基准数据范围: {benchmark_df.index.min()} - {benchmark_df.index.max()}")
                return {}

            self.log.info(f"交易日数: {len(date_range)} 天\n")

            # 初始化回测组件
            context, api = self._initialize_context(config, config.start_date)
            stats_collector = StatsCollector()

            # 创建策略执行引擎
            engine = StrategyExecutionEngine(
                context=context,
                api=api,
                stats_collector=stats_collector,
                g=self.g,
                log=self.log
            )

            # 加载策略
            engine.set_strategy_name(strategy_name)
            engine.load_strategy_from_file(config.strategy_path)
            print("✓ 策略加载完成\n")

            # 执行回测
            success = self._execute_backtest(engine, date_range)

            if not success:
                self.log.error("回测中断")
                return {}

            # 生成报告
            return self._generate_reports(
                stats_collector.stats,
                config,
                benchmark_df,
                stats_collector.stats['positions_count'],
                context
            )

        finally:
            self._cleanup()

    @timer(name="数据加载")
    def _load_data(self, required_data=None) -> pd.DataFrame:
        """加载数据（仅首次或非服务器模式）

        Args:
            required_data: 需要加载的数据集合

        Returns:
            基准数据DataFrame
        """
        if self._data_loaded and self.use_data_server:
            # 数据已加载且使用服务器模式，直接返回
            print("数据已在内存中，无需重新加载\n")
            return self.benchmark_data['000300.SS'] # type: ignore

        if self.use_data_server:
            return self._load_data_server_mode(required_data)
        else:
            return self._load_traditional_mode(required_data)

    def _load_data_server_mode(self, required_data=None) -> pd.DataFrame:
        """数据服务器模式加载"""
        data_server = DataServer(self.data_path, required_data)
        self.stock_data_dict = data_server.stock_data_dict
        self.valuation_dict = data_server.valuation_dict
        self.fundamentals_dict = data_server.fundamentals_dict
        self.exrights_dict = data_server.exrights_dict
        self.benchmark_data = data_server.benchmark_data
        self.stock_metadata = data_server.stock_metadata
        self.index_constituents = data_server.index_constituents
        self.stock_status_history = data_server.stock_status_history
        self.stock_data_store = data_server.stock_data_store
        self.fundamentals_store = data_server.fundamentals_store
        self.adj_pre_cache = data_server.adj_pre_cache
        self.dividend_cache = data_server.dividend_cache
        self._data_loaded = True
        return data_server.get_benchmark_data() # type: ignore

    def _load_traditional_mode(self, required_data=None) -> pd.DataFrame:
        """传统模式加载"""

        print("=" * 70)
        print("加载本地数据...")
        print("=" * 70)

        (
            self.stock_data_store, self.fundamentals_store,
            self.stock_data_dict, self.valuation_dict, self.fundamentals_dict, self.exrights_dict,
            self.benchmark_data, self.stock_metadata, self.index_constituents, self.stock_status_history,
            self.adj_pre_cache, self.dividend_cache
        ) = load_data_from_hdf5(self.data_path, required_data)

        self._data_loaded = True
        return self.benchmark_data['000300.SS'] # type: ignore

    def _setup_logging(self, config: BacktestConfig):
        """配置日志系统

        Args:
            config: 回测配置
        """
        import sys

        log_filename = config.get_log_filename()
        os.makedirs(config.log_dir, exist_ok=True)

        print(f"日志文件: {log_filename}")

        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_filename, mode='w', encoding='utf-8')
            ],
            force=True
        )
        self.log = logging.getLogger('backtest')

    def _create_date_range(self, benchmark_df: pd.DataFrame, start_date, end_date):
        """创建交易日序列

        Args:
            benchmark_df: 基准数据
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易日DatetimeIndex
        """
        return benchmark_df.index[
            (benchmark_df.index >= start_date) &
            (benchmark_df.index <= end_date) &
            (benchmark_df['volume'] > 0)
        ]

    def _initialize_context(self, config: BacktestConfig, start_date) -> tuple:
        """初始化上下文和API

        Args:
            config: 回测配置
            start_date: 开始日期

        Returns:
            (Context, PtradeAPI) 元组
        """
        from simtradelab.ptrade.data_context import DataContext

        # 创建组合和上下文
        portfolio = Portfolio(config.initial_capital)
        context = Context(portfolio=portfolio, current_dt=start_date)

        # 设置portfolio的context引用
        portfolio._context = context

        # 创建数据上下文
        data_context = DataContext(
            stock_data_dict=self.stock_data_dict,
            valuation_dict=self.valuation_dict,
            fundamentals_dict=self.fundamentals_dict,
            exrights_dict=self.exrights_dict,
            benchmark_data=self.benchmark_data,
            stock_metadata=self.stock_metadata,
            stock_data_store=self.stock_data_store,
            fundamentals_store=self.fundamentals_store,
            index_constituents=self.index_constituents,
            stock_status_history=self.stock_status_history,
            adj_pre_cache=self.adj_pre_cache,
            dividend_cache=self.dividend_cache
        )

        # 创建API
        api = PtradeAPI(
            data_context=data_context,
            context=context,
            log=self.log
        )

        # 初始化回测上下文
        bt_ctx = BacktestContext(
            stock_data_dict=self.stock_data_dict,
            get_stock_date_index_func=api.get_stock_date_index,
            check_limit_func=api.check_limit,
            log_obj=self.log,
            context_obj=context,
            data_context=data_context
        )

        # 绑定回测上下文
        context.portfolio._bt_ctx = bt_ctx
        context.blotter._bt_ctx = bt_ctx

        self.context = context
        return context, api

    @timer(name="回测执行")
    def _execute_backtest(self, engine: StrategyExecutionEngine, date_range) -> bool:
        """执行回测主循环

        Args:
            engine: 策略执行引擎
            date_range: 交易日序列

        Returns:
            是否成功
        """
        print("初始化策略...")

        print(f"\n开始回测循环...")

        success = engine.run_backtest(date_range)

        return success

    def _generate_reports(
        self,
        stats: dict,
        config: BacktestConfig,
        benchmark_df: pd.DataFrame,
        positions_count,
        context
    ) -> dict:
        """生成回测报告和图表

        Args:
            stats: 统计数据
            config: 回测配置
            benchmark_df: 基准数据（默认用于创建日期范围）
            positions_count: 持仓数量数组
            context: 上下文对象（用于获取用户设置的benchmark）

        Returns:
            回测报告字典
        """
        # 获取用户设置的benchmark，如果未设置则使用默认的000300.SS
        benchmark_code = context.benchmark if context.benchmark else '000300.SS'

        # 根据benchmark_code获取对应的基准数据
        # 优先从benchmark_data查找（指数），然后从stock_data_dict查找（普通股票）
        if benchmark_code in self.benchmark_data:
            actual_benchmark_df = self.benchmark_data[benchmark_code]
            self.log.info(f"使用基准（指数）: {benchmark_code}")
        elif benchmark_code in self.stock_data_dict:
            actual_benchmark_df = self.stock_data_dict[benchmark_code]
            self.log.info(f"使用基准（股票）: {benchmark_code}")
        else:
            # 如果指定的基准不存在，回退到000300.SS
            actual_benchmark_df = self.benchmark_data.get('000300.SS', benchmark_df)
            self.log.warning(f"基准 {benchmark_code} 不存在，使用默认基准 000300.SS")

        # 生成报告
        report = generate_backtest_report(stats, config.start_date, config.end_date, actual_benchmark_df)

        # 获取总耗时（仅回测执行时间，不包括数据加载）
        time_str = get_current_elapsed_time(self, '_execute_backtest')

        # 打印报告
        print_backtest_report(
            report, self.log,
            config.start_date, config.end_date,
            time_str,
            np.array(positions_count)
        )

        # 生成图表（传递实际使用的基准）
        chart_benchmark_data = {benchmark_code: actual_benchmark_df}
        chart_filename = generate_backtest_charts(
            stats,
            config.start_date, config.end_date,
            chart_benchmark_data,
            config.get_chart_filename()
        )

        log_filename = config.get_log_filename()
        print(f"\n日志已保存至: {log_filename}")
        print(f"图表已保存至: {chart_filename}")

        return report

    def _cleanup(self):
        """清理资源"""
        if not self.use_data_server:
            print("\n正在关闭数据文件...")
            self._close_stores()
        else:
            print("\n数据保持常驻内存，下次在jupyter notebook中运行无需重新加载")

    def _close_stores(self):
        """关闭HDF5存储"""
        if self.use_data_server:
            return

        for store in [self.stock_data_store, self.fundamentals_store]:
            if store is not None:
                try:
                    store.close()
                except Exception:
                    pass

    def _signal_handler(self, sig, frame):
        """处理Ctrl+C信号"""
        print("\n\n收到中断信号...")
        self._cleanup()
        os._exit(0)
