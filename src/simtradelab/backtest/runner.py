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
from simtradelab.ptrade.object import Global, LazyDataDict, Portfolio, BacktestContext
from simtradelab.backtest.stats import generate_backtest_report, generate_backtest_charts, print_backtest_report
from simtradelab.ptrade.api import PtradeAPI, timing, get_current_elapsed_time
from simtradelab.service.data_server import DataServer
from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.stats_collector import StatsCollector
from simtradelab.backtest.strategy_loader import StrategyLoader
from simtradelab.backtest.strategy_executor import StrategyExecutor
from simtradelab.ptrade.strategy_validator import validate_strategy_file


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
            from simtradelab.paths import DATA_PATH
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

        # 全局对象
        self.g = Global()
        self.log = None
        self.context = None

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)

    @timing
    def run(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        strategies_path: str,
        initial_capital: float = 1000000.0
    ) -> dict:
        """运行回测

        Args:
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期
            strategies_path: 策略文件路径
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
            strategies_path=strategies_path,
            initial_capital=initial_capital,
            use_data_server=self.use_data_server
        )

        # 先验证策略，避免数据加载后才发现策略错误
        print("检查策略...")
        is_valid, errors = validate_strategy_file(config.strategy_path)
        if not is_valid:
            print("\n策略验证失败:")
            for error in errors:
                print(f"  - {error}")
            return {}
        print("✓ 策略检查通过\n")

        try:
            # 加载数据（仅首次或非服务器模式）
            benchmark_df = self._load_data()

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

            # 加载策略
            strategy_loader = StrategyLoader(config.strategy_path, self.g, self.log, context, api)
            strategy_namespace = strategy_loader.load()
            print("✓ 策略加载完成\n")

            # 执行回测
            executor = StrategyExecutor(strategy_namespace, context, stats_collector, self.log)
            success = self._execute_backtest(executor, date_range)

            if not success:
                self.log.error("回测中断")
                return {}

            # 生成报告
            return self._generate_reports(
                stats_collector.stats,
                config,
                benchmark_df,
                stats_collector.stats['positions_count']
            )

        finally:
            self._cleanup()

    @timing
    def _load_data(self) -> pd.DataFrame:
        """加载数据（仅首次或非服务器模式）

        Returns:
            基准数据DataFrame
        """
        if self._data_loaded and self.use_data_server:
            # 数据已加载且使用服务器模式，直接返回
            print("✓ 数据已在内存中，无需重新加载\n")
            return self.benchmark_data['000300.SS']

        if self.use_data_server:
            return self._load_data_server_mode()
        else:
            return self._load_traditional_mode()

    def _load_data_server_mode(self) -> pd.DataFrame:
        """数据服务器模式加载"""
        data_server = DataServer(self.data_path)
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
        self._data_loaded = True
        return data_server.get_benchmark_data()

    def _load_traditional_mode(self) -> pd.DataFrame:
        """传统模式加载"""
        import json

        print("=" * 70)
        print("加载本地数据...")
        print("=" * 70)

        self.stock_data_store = pd.HDFStore(f'{self.data_path}/ptrade_data.h5', 'r')
        self.fundamentals_store = pd.HDFStore(f'{self.data_path}/ptrade_fundamentals.h5', 'r')

        # 提取键名
        all_stock_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/stock_data/')]
        valuation_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/valuation/')]
        fundamentals_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/fundamentals/')]
        exrights_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/exrights/')]

        # 构建数据字典
        print("预加载基本面数据...")
        self.stock_data_dict = LazyDataDict(self.stock_data_store, '/stock_data/', all_stock_keys, max_cache_size=2000)
        self.valuation_dict = LazyDataDict(self.fundamentals_store, '/valuation/', valuation_keys, preload=True)
        self.fundamentals_dict = LazyDataDict(self.fundamentals_store, '/fundamentals/', fundamentals_keys, preload=True)
        self.exrights_dict = LazyDataDict(self.stock_data_store, '/exrights/', exrights_keys, max_cache_size=800)

        print(f"✓ 股票数据: {len(all_stock_keys)} 只")
        print(f"✓ 基本面数据: {len(valuation_keys)} 只")
        print(f"✓ 除权数据: {len(exrights_keys)} 只")

        # 加载元数据
        self.stock_metadata = self.stock_data_store['/stock_metadata']
        benchmark_df = self.stock_data_store['/benchmark']
        metadata = self.stock_data_store['/metadata']

        if 'index_constituents' in metadata.index and pd.notna(metadata['index_constituents']):
            self.index_constituents = json.loads(metadata['index_constituents'])
        if 'stock_status_history' in metadata.index and pd.notna(metadata['stock_status_history']):
            self.stock_status_history = json.loads(metadata['stock_status_history'])

        self.benchmark_data = {'000300.SS': benchmark_df}
        self._data_loaded = True

        return benchmark_df

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
            stock_status_history=self.stock_status_history
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
            context_obj=context
        )

        # 绑定回测上下文
        context.portfolio._bt_ctx = bt_ctx
        context.blotter._bt_ctx = bt_ctx

        self.context = context
        return context, api

    def _execute_backtest(self, executor: StrategyExecutor, date_range) -> bool:
        """执行回测主循环

        Args:
            executor: 策略执行器
            date_range: 交易日序列

        Returns:
            是否成功
        """
        print("初始化策略...")
        executor.initialize()

        print(f"\n开始回测循环...")

        success = executor.run_daily_loop(date_range)

        return success

    def _generate_reports(
        self,
        stats: dict,
        config: BacktestConfig,
        benchmark_df: pd.DataFrame,
        positions_count
    ) -> dict:
        """生成回测报告和图表

        Args:
            stats: 统计数据
            config: 回测配置
            benchmark_df: 基准数据
            positions_count: 持仓数量数组

        Returns:
            回测报告字典
        """
        # 生成报告
        report = generate_backtest_report(stats, config.start_date, config.end_date, benchmark_df)

        # 获取总耗时（从timing装饰器保存的开始时间中计算）
        time_str = get_current_elapsed_time(self, 'run')

        # 打印报告
        print_backtest_report(
            report, self.log,
            config.start_date, config.end_date,
            time_str,
            np.array(positions_count)
        )

        # 生成图表
        chart_filename = generate_backtest_charts(
            stats,
            config.start_date, config.end_date,
            self.benchmark_data,
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
