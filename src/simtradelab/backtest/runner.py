# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
回测执行器 - 重构版

职责：编排回测流程，协调各组件工作

"""

import numpy as np
import pandas as pd
import signal
import logging
import os

from simtradelab.i18n import set_locale, t
from simtradelab.ptrade.context import Context
from simtradelab.ptrade.object import Portfolio, BacktestContext
from simtradelab.ptrade.config_manager import config as ptrade_config
from simtradelab.backtest.stats import generate_backtest_report, generate_backtest_charts, print_backtest_report
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.service.data_server import DataServer
from simtradelab.backtest.config import BacktestConfig
from simtradelab.ptrade.market_profile import get_market_profile
from simtradelab.backtest.backtest_stats import StatsCollector, BacktestStats
from simtradelab.ptrade.strategy_engine import StrategyExecutionEngine
from simtradelab.ptrade.strategy_validator import validate_strategy_file
from simtradelab.utils.perf import timer, get_current_elapsed_time


class BacktestRunner:
    """回测执行器 - 负责编排整个回测流程"""

    def __init__(self):
        """初始化回测执行器
        """

        # 数据容器（延迟加载）
        self._data_loaded = False
        self._cancel_event: object = None
        self.stock_data_dict = None
        self.stock_data_dict_1m = None
        self.valuation_dict = None
        self.fundamentals_dict = None
        self.exrights_dict = None
        self.benchmark_data = None
        self.stock_metadata = None
        self.index_constituents = {}
        self.stock_status_history = {}
        self.adj_pre_cache = None
        self.adj_post_cache = None
        self.dividend_cache = None
        self.trade_days = None

        # 优化模式：跨 trial 共享日期索引缓存
        self._shared_date_index: dict | None = None

        # 注册信号处理（仅在主线程）
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # 在子进程中会失败，忽略
            pass

    @timer(name="perf.name.total")
    def run(self, config: BacktestConfig) -> dict:
        """运行回测

        Args:
            config: 回测配置对象

        Returns:
            回测报告字典
        """
        set_locale(config.locale)

        # 先验证策略，避免数据加载后才发现策略错误
        if not config.optimization_mode:
            print(t("bt.checking_strategy"))
            is_valid, errors, fixed_code = validate_strategy_file(
                config.strategy_path,
                check_py35_compat=config.sandbox
            )
            if not is_valid:
                print(t("bt.validation_failed"))
                for error in errors:
                    print(f"  - {error}")
                return {}
            if fixed_code:
                print(t("bt.auto_fixed"))
            print(t("bt.validation_passed"))

        # 分析策略数据依赖
        if not config.optimization_mode:
            print(t("bt.analyzing_deps"))
            from simtradelab.ptrade.strategy_data_analyzer import (
                analyze_strategy_data_requirements,
                print_dependencies
            )
            deps = analyze_strategy_data_requirements(config.strategy_path)
            print_dependencies(deps)
            print("")

        # 转换为数据加载参数
        if config.optimization_mode:
            # 优化模式：数据已加载，跳过依赖分析
            required_data = None
        else:
            required_data = set()
            if deps.needs_price_data:
                required_data.add('price')
            if deps.needs_valuation:
                required_data.add('valuation')
            if deps.needs_fundamentals:
                required_data.add('fundamentals')
            if deps.needs_exrights:
                required_data.add('exrights')

        # 获取市场配置
        profile = get_market_profile(config.market)
        self._profile = profile

        try:
            # 加载数据
            benchmark_df = self._load_data(required_data, config.frequency, config.data_path, config.market)

            if self._cancel_event and self._cancel_event.is_set():
                return {}

            # 初始化日志
            if not config.optimization_mode:
                self._setup_logging(config)
            log = logging.getLogger('backtest')

            if not config.optimization_mode:
                log.info(t("bt.start", strategy=config.strategy_name))
                log.info(t("bt.period", start=config.start_date.date(), end=config.end_date.date()))

            # 创建交易日序列
            date_range = self._create_date_range(benchmark_df, config.start_date, config.end_date)

            if len(date_range) == 0:
                log.error(t("bt.empty_dates", start=config.start_date.date(), end=config.end_date.date()))
                log.error(t("bt.benchmark_range", start=benchmark_df.index.min(), end=benchmark_df.index.max()))
                return {}

            log.info(t("bt.trading_days", count=len(date_range)))

            # 初始化回测组件
            context, api = self._initialize_context(config, config.start_date, log)
            name_map: dict[str, str] = {}
            if self.stock_metadata is not None and not self.stock_metadata.empty and "stock_name" in self.stock_metadata.columns:
                name_map = self.stock_metadata["stock_name"].to_dict()
            stats_collector = StatsCollector(name_map=name_map)
            api.stats_collector = stats_collector

            # 创建策略执行引擎
            engine = StrategyExecutionEngine(
                context=context,
                api=api,
                stats_collector=stats_collector,
                log=log,
                frequency=config.frequency,
                sandbox=config.sandbox,
                cancel_event=self._cancel_event,
            )

            # 加载策略
            engine.set_strategy_name(config.strategy_name)
            engine.load_strategy_from_file(config.strategy_path)
            print(t("bt.strategy_loaded"))

            # 执行回测
            success = self._execute_backtest(engine, date_range)

            # 优化模式：保存日期索引缓存供后续 trial 复用
            if config.optimization_mode and self._shared_date_index is None:
                self._shared_date_index = api._stock_date_index

            if not success:
                log.error(t("bt.interrupted"))
                return {}

            # 生成报告
            return self._generate_report(
                stats_collector.stats,
                config,
                benchmark_df,
                stats_collector.stats.positions_count,
                context,
            )

        finally:
            self._cleanup()

    @timer(name="perf.name.data_load")
    def _load_data(self, required_data=None, frequency='1d', data_path: str = None, market: str = "CN") -> pd.DataFrame:
        """加载数据

        Args:
            required_data: 需要加载的数据集合
            frequency: 回测频率 '1d'日线 '1m'分钟线

        Returns:
            基准数据DataFrame
        """
        if self._data_loaded:
            # 数据已加载，直接返回
            print(t("bt.data_cached"))
            # 从 benchmark_data 获取默认基准(会在后续根据 context.benchmark 重新选择)
            return next(iter(self.benchmark_data.values())) # type: ignore

        # 使用多进程安全的DataServer
        data_server = DataServer(required_data, frequency, data_path, market=market)

        # 绑定到runner实例
        self.stock_data_dict = data_server.stock_data_dict
        self.stock_data_dict_1m = data_server.stock_data_dict_1m
        self.valuation_dict = data_server.valuation_dict
        self.fundamentals_dict = data_server.fundamentals_dict
        self.exrights_dict = data_server.exrights_dict
        self.benchmark_data = data_server.benchmark_data
        self.stock_metadata = data_server.stock_metadata
        self.index_constituents = data_server.index_constituents
        self.stock_status_history = data_server.stock_status_history
        self.adj_pre_cache = data_server.adj_pre_cache
        self.adj_post_cache = data_server.adj_post_cache
        self.dividend_cache = data_server.dividend_cache
        self.trade_days = getattr(data_server, 'trade_days', None)
        self._data_loaded = True
        return data_server.get_benchmark_data()

    def _setup_logging(self, config: BacktestConfig):
        """配置日志系统

        Args:
            config: 回测配置
        """
        import sys
        from simtradelab.ptrade import strategy_engine as _se

        class BacktestDateFilter(logging.Filter):
            def filter(self, record):
                record.backtest_dt = _se._current_backtest_date or ''
                return True

        handlers = [logging.StreamHandler(sys.stdout)]

        # 仅在启用日志时创建文件handler
        os.makedirs(config.log_dir, exist_ok=True)
        if config.enable_logging:
            self._log_filename = config.get_log_filename()
            print(t("bt.log_file", path=self._log_filename))
            handlers.append(logging.FileHandler(self._log_filename, mode='w', encoding='utf-8'))
        if config.enable_charts:
            self._chart_filename = config.get_chart_filename()

        for h in handlers:
            h.addFilter(BacktestDateFilter())

        logging.basicConfig(
            level=logging.INFO,
            format='%(backtest_dt)s [%(levelname)s] %(message)s',
            handlers=handlers,
            force=True
        )

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

    def _initialize_context(self, config: BacktestConfig, start_date, log) -> tuple:
        """初始化上下文和API

        Args:
            config: 回测配置
            start_date: 开始日期

        Returns:
            (Context, PtradeAPI) 元组
        """
        from simtradelab.ptrade.data_context import DataContext

        # 重置全局交易配置，避免前次回测的残留设置污染本次回测
        ptrade_config.reset_to_defaults()
        ptrade_config.apply_market_defaults(self._profile)

        # 创建组合和上下文
        portfolio = Portfolio(config.initial_capital)
        t_plus_1 = config.t_plus_1 if config.t_plus_1 is not None else self._profile.t_plus_1
        context = Context(portfolio=portfolio, current_dt=start_date,
                          frequency=config.frequency, t_plus_1=t_plus_1)

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
            index_constituents=self.index_constituents,
            stock_status_history=self.stock_status_history,
            adj_pre_cache=self.adj_pre_cache,
            adj_post_cache=self.adj_post_cache,
            dividend_cache=self.dividend_cache,
            trade_days=self.trade_days,
            stock_data_dict_1m=self.stock_data_dict_1m
        )

        # 创建API
        api = PtradeAPI(
            data_context=data_context,
            context=context,
            log=log
        )
        api.lot_size = self._profile.lot_size
        api.has_price_limit = self._profile.has_price_limit

        # 优化模式：复用日期索引缓存
        if self._shared_date_index is not None:
            api._stock_date_index = self._shared_date_index

        # 初始化回测上下文
        bt_ctx = BacktestContext(
            stock_data_dict=self.stock_data_dict,
            get_stock_date_index_func=api.get_stock_date_index,
            check_limit_func=api.check_limit,
            log_obj=log,
            context_obj=context,
            data_context=data_context
        )

        # 绑定回测上下文
        context.portfolio._bt_ctx = bt_ctx
        context.blotter._bt_ctx = bt_ctx

        self.context = context
        return context, api

    @timer(name="perf.name.backtest")
    def _execute_backtest(self, engine: StrategyExecutionEngine, date_range) -> bool:
        """执行回测主循环

        Args:
            engine: 策略执行引擎
            date_range: 交易日序列

        Returns:
            是否成功
        """
        print(t("bt.initializing"))

        print(t("bt.starting_loop"))

        success = engine.run_backtest(date_range)

        return success

    def _generate_report(
        self,
        stats: BacktestStats,
        config: BacktestConfig,
        benchmark_df: pd.DataFrame,
        positions_count: list[int],
        context,
    ) -> dict:
        """生成回测报告

        Args:
            stats: 回测统计数据
            config: 回测配置
            benchmark_df: 基准数据DataFrame
            positions_count: 持仓数量数组
            context: 上下文对象（用于获取用户设置的benchmark）

        Returns:
            回测报告字典
        """
        log = logging.getLogger('backtest')

        # 优先使用配置中的benchmark_code，如果未设置则从context获取
        benchmark_code = config.benchmark_code or context.benchmark or self._profile.default_benchmark

        # 根据benchmark_code获取对应的基准数据
        # 优先从benchmark_data查找（指数），然后从stock_data_dict查找（普通股票）
        if benchmark_code in self.benchmark_data:
            actual_benchmark_df = self.benchmark_data[benchmark_code]
            log.info(t("bt.benchmark_index", code=benchmark_code))
        elif benchmark_code in self.stock_data_dict:
            actual_benchmark_df = self.stock_data_dict[benchmark_code]
            log.info(t("bt.benchmark_stock", code=benchmark_code))
        else:
            # 如果指定的基准不存在，回退到市场默认基准
            fallback = self._profile.default_benchmark
            actual_benchmark_df = self.benchmark_data.get(fallback, benchmark_df)
            log.warning(t("bt.benchmark_fallback", code=benchmark_code, fallback=fallback))

        # 生成报告
        report = generate_backtest_report(
            stats, 
            config.start_date, 
            config.end_date, 
            actual_benchmark_df,
            benchmark_code=benchmark_code
        )

        # 获取总耗时（仅回测执行时间，不包括数据加载）
        time_str = get_current_elapsed_time(self, '_execute_backtest')

        # 打印报告
        print_backtest_report(
            report, log,
            config.start_date, config.end_date,
            time_str,
            np.array(positions_count)
        )

        # 生成图表
        if config.enable_charts:
            chart_benchmark_data = {benchmark_code: actual_benchmark_df}
            generate_backtest_charts(
                stats, config.start_date, config.end_date,
                chart_benchmark_data, self._chart_filename, benchmark_code)
            print(t("bt.chart_saved", path=self._chart_filename))

        if config.enable_logging:
            print(t("bt.log_saved", path=self._log_filename))

        report["_stats"] = stats
        if config.enable_charts and hasattr(self, '_chart_filename'):
            report["_chart_path"] = self._chart_filename

        if config.enable_export:
            from simtradelab.backtest.export import export_to_csv
            export_to_csv(report, config.log_dir)

        # 基准净值序列（对齐到策略交易日，归一化到1.0起点）
        trade_dates_set = set()
        for d in stats.trade_dates:
            if hasattr(d, 'date'):
                trade_dates_set.add(str(d.date()))
            elif hasattr(d, 'strftime'):
                trade_dates_set.add(str(d.strftime('%Y-%m-%d')))
            else:
                trade_dates_set.add(str(d))
        
        # 确保 actual_benchmark_df 存在且不为空
        if actual_benchmark_df is not None and not actual_benchmark_df.empty:
            # 筛选基准数据的日期范围
            bm_slice = actual_benchmark_df[
                (actual_benchmark_df.index >= config.start_date) &
                (actual_benchmark_df.index <= config.end_date)
            ]
            
            # 进一步筛选到策略的交易日
            def get_date_key(d):
                if hasattr(d, 'date'):
                    return str(d.date())
                elif hasattr(d, 'strftime'):
                    return str(d.strftime('%Y-%m-%d'))
                else:
                    return str(d)
            
            bm_slice = bm_slice[
                bm_slice.index.map(get_date_key).isin(trade_dates_set)
            ]
            
            if len(bm_slice) > 0:
                bm_initial = bm_slice['close'].iloc[0]
                if bm_initial > 0:
                    report["_benchmark_nav"] = (bm_slice['close'] / bm_initial).tolist()
                else:
                    report["_benchmark_nav"] = []
            else:
                report["_benchmark_nav"] = []
        else:
            report["_benchmark_nav"] = []

        return report

    def _cleanup(self):
        """清理资源"""
        pass

    def _signal_handler(self, sig, frame):
        """处理Ctrl+C信号"""
        _ = sig, frame  # 消除未使用参数警告
        print(t("bt.signal_received"))
        self._cleanup()
        os._exit(0)
