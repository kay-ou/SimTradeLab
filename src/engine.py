# -*- coding: utf-8 -*-
"""
回测引擎模块
"""
import importlib.util
import os
import types
from datetime import datetime
from functools import partial
from typing import Union, List, Optional

import numpy as np
import pandas as pd

from . import financials, market_data, trading, utils
from .context import Context, Portfolio
from .logger import log
from .data_sources import DataSourceFactory, DataSourceManager, CSVDataSource
from .config import load_config


class BacktestEngine:
    """
    回测引擎，负责加载策略、模拟交易并运行回测。
    """

    def __init__(self, strategy_file, data_path=None, start_date=None, end_date=None,
                 initial_cash=1000000, frequency='1d', data_source=None,
                 securities=None, config_path=None):
        """
        初始化回测引擎

        Args:
            strategy_file: 策略文件路径
            data_path: CSV数据文件路径（向后兼容）
            start_date: 开始日期
            end_date: 结束日期
            initial_cash: 初始资金
            frequency: 交易频率
            data_source: 数据源类型或数据源对象
            securities: 股票列表（用于在线数据源）
            config_path: 配置文件路径
        """
        self.strategy_file = strategy_file
        self.data_path = data_path
        self.start_date = pd.to_datetime(start_date) if start_date else None
        self.end_date = pd.to_datetime(end_date) if end_date else None
        self.initial_cash = initial_cash
        self.frequency = frequency
        self.securities = securities or []

        # 加载配置
        self.config = load_config(config_path)

        # 初始化数据源
        self.data_source_manager = self._init_data_source(data_source)

        # 初始化其他组件
        self.portfolio = Portfolio(initial_cash)
        self.context = Context(self.portfolio)
        self.commission_ratio = 0.0003  # 默认佣金
        self.min_commission = 5      # 默认最低佣金
        self.slippage = 0.001  # 默认滑点
        self.data = self._load_data()
        self.current_data = {}
        self.portfolio_history = []
        self.strategy = self._load_strategy()

    def _init_data_source(self, data_source):
        """初始化数据源管理器"""
        if data_source is None:
            # 向后兼容：如果指定了data_path，使用CSV数据源
            if self.data_path:
                primary_source = CSVDataSource(data_path=self.data_path)
                log.info("使用CSV数据源（向后兼容模式）")
            else:
                # 使用配置文件中的默认数据源
                default_source_name = self.config.get_default_source()
                primary_source = self._create_data_source(default_source_name)
                log.info(f"使用默认数据源: {default_source_name}")
        elif isinstance(data_source, str):
            # 根据字符串创建数据源
            primary_source = self._create_data_source(data_source)
            log.info(f"使用指定数据源: {data_source}")
        else:
            # 直接使用传入的数据源对象
            primary_source = data_source
            log.info(f"使用自定义数据源: {type(data_source).__name__}")

        # 创建数据源管理器（暂时不添加备用数据源）
        return DataSourceManager(primary_source)

    def _create_data_source(self, source_name):
        """根据名称创建数据源"""
        source_config = self.config.get_source_config(source_name)

        if source_name == 'csv':
            data_path = source_config.get('data_path', self.data_path or './data/sample_data.csv')
            return DataSourceFactory.create('csv', data_path=data_path)
        elif source_name == 'tushare':
            token = self.config.get_tushare_token()
            if not token:
                raise ValueError("Tushare token未配置，请设置环境变量TUSHARE_TOKEN或在配置文件中设置")
            cache_dir = source_config.get('cache_dir', './cache/tushare')
            cache_enabled = source_config.get('cache_enabled', True)
            return DataSourceFactory.create('tushare', token=token,
                                          cache_dir=cache_dir, cache_enabled=cache_enabled)
        elif source_name == 'akshare':
            cache_dir = source_config.get('cache_dir', './cache/akshare')
            cache_enabled = source_config.get('cache_enabled', True)
            return DataSourceFactory.create('akshare',
                                          cache_dir=cache_dir, cache_enabled=cache_enabled)
        else:
            raise ValueError(f"不支持的数据源类型: {source_name}")

    def _load_strategy(self):
        """
        动态加载指定的策略文件，并注入API和'g'对象。
        """
        spec = importlib.util.spec_from_file_location("strategy", self.strategy_file)
        strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy_module)

        if not hasattr(strategy_module, 'g'):
            strategy_module.g = types.SimpleNamespace()

        strategy_module.log = log

        from . import compatibility, performance

        # 注入需要engine参数的API函数
        api_modules = [financials, market_data, trading, utils]
        for module in api_modules:
            for func_name in dir(module):
                if not func_name.startswith("__"):
                    api_func = getattr(module, func_name)
                    # 只注入函数，排除类、模块和其他对象
                    if callable(api_func) and hasattr(api_func, '__call__') and not isinstance(api_func, type):
                        # 创建一个安全的包装函数，确保返回值类型正确
                        def create_wrapper(func, engine, name):
                            def wrapper(*args, **kwargs):
                                try:
                                    result = func(engine, *args, **kwargs)
                                    # 对于 get_research_path，确保返回字符串
                                    if name == 'get_research_path' and not isinstance(result, str):
                                        log.warning(f"get_research_path 返回了非字符串类型: {type(result)}, 使用默认路径")
                                        return './'
                                    return result
                                except Exception as e:
                                    log.warning(f"API函数 {name} 调用失败: {e}")
                                    # 为关键函数提供默认返回值
                                    if name == 'get_research_path':
                                        return './'
                                    raise
                            return wrapper
                        setattr(strategy_module, func_name, create_wrapper(api_func, self, func_name))

        # 注入不需要engine参数的函数（兼容性和性能模块）
        standalone_modules = [compatibility, performance]
        for module in standalone_modules:
            for func_name in dir(module):
                if not func_name.startswith("__") and not func_name.startswith("_"):
                    api_func = getattr(module, func_name)
                    if callable(api_func):
                        setattr(strategy_module, func_name, api_func)

        # 设置当前引擎到性能模块
        performance._set_current_engine(self)

        return strategy_module

    def _load_data(self):
        """
        使用数据源管理器加载数据
        """
        try:
            # 如果没有指定日期范围，尝试从数据源获取可用的日期范围
            if self.start_date is None or self.end_date is None:
                log.warning("未指定日期范围，将尝试加载所有可用数据")
                # 对于CSV数据源，可以从文件中推断日期范围
                # 对于在线数据源，需要用户指定日期范围
                if self.start_date is None:
                    self.start_date = pd.to_datetime('2023-01-01')
                if self.end_date is None:
                    self.end_date = pd.to_datetime('2023-12-31')

            # 确定要获取数据的股票列表
            securities = self.securities
            if not securities:
                # 如果没有指定股票列表，尝试从数据源获取
                securities = self.data_source_manager.get_stock_list()
                if not securities:
                    log.warning("无法获取股票列表，请在初始化时指定securities参数")
                    return {}
                # 限制股票数量以避免过多的API调用
                securities = securities[:10]  # 默认只取前10只股票
                log.info(f"自动选择股票列表: {securities}")

            # 从数据源获取历史数据
            data_dict = self.data_source_manager.get_history(
                securities=securities,
                start_date=self.start_date.strftime('%Y-%m-%d'),
                end_date=self.end_date.strftime('%Y-%m-%d'),
                frequency=self.frequency
            )

            log.info(f"成功加载 {len(data_dict)} 只股票的数据")
            return data_dict

        except Exception as e:
            log.warning(f"加载数据失败: {e}")
            return {}


    def _is_daily_data(self, df):
        """
        判断数据是否为日线数据。
        """
        if df.empty:
            return True
        time_diff = df.index[1] - df.index[0] if len(df) > 1 else pd.Timedelta(days=1)
        return time_diff >= pd.Timedelta(days=1)

    def _generate_minute_data(self, daily_df):
        """
        从日线数据生成分钟级数据。
        """
        freq_map = {'1m': 1, '5m': 5, '15m': 15, '30m': 30}
        minute_interval = freq_map.get(self.frequency, 1)
        periods_per_day = 240 // minute_interval

        minute_data_list = []
        for security, security_data in daily_df.groupby('security'):
            for idx, row in security_data.iterrows():
                day_start = idx.replace(hour=9, minute=30)
                minute_times = pd.date_range(start=day_start, periods=periods_per_day, freq=f'{minute_interval}T')
                daily_range = row['high'] - row['low']
                daily_volume = row['volume']

                for i, minute_time in enumerate(minute_times):
                    progress = i / periods_per_day
                    np.random.seed(int(minute_time.timestamp()) % 10000)
                    noise = np.random.normal(0, daily_range * 0.01)
                    minute_close = max(row['low'], min(row['high'], row['low'] + daily_range * progress + noise))
                    minute_open = minute_close * (1 + np.random.normal(0, 0.001))
                    minute_high = max(minute_open, minute_close, minute_close * (1 + abs(np.random.normal(0, 0.002))))
                    minute_low = min(minute_open, minute_close, minute_close * (1 - abs(np.random.normal(0, 0.002))))
                    minute_volume = daily_volume / periods_per_day

                    minute_data_list.append({
                        'datetime': minute_time, 'open': minute_open, 'high': minute_high,
                        'low': minute_low, 'close': minute_close, 'volume': minute_volume,
                        'security': security
                    })

        if not minute_data_list:
            return daily_df
        
        minute_df = pd.DataFrame(minute_data_list)
        minute_df.set_index('datetime', inplace=True)
        return minute_df

    def _update_portfolio_value(self, current_prices):
        """
        根据当前价格更新投资组合的总价值。
        """
        total_value = self.portfolio.cash
        for security, position in self.portfolio.positions.items():
            price = current_prices.get(security, 0)
            total_value += position.amount * price
        self.portfolio.total_value = total_value

    def run(self):
        """
        运行回测。
        """
        start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        strategy_name = os.path.basename(self.strategy_file).replace('.py', '')
        print(f"{start_time_str} 开始运行回测, 策略名称: {strategy_name}, 频率: {self.frequency}")

        if hasattr(self.strategy, 'initialize'):
            self.strategy.initialize(self.context)

        if not self.data:
            log.warning("没有可用的数据")
            return

        first_security = list(self.data.keys())[0]
        trading_times = self.data[first_security].index
        trading_times = trading_times[(trading_times >= self.start_date) & (trading_times <= self.end_date)]

        if self.frequency == '1d':
            self._run_daily_backtest(trading_times)
        else:
            self._run_minute_backtest(trading_times)

        log.current_dt = None
        log.info("策略回测结束")

        # 生成性能分析报告
        self._generate_performance_report()

    def _run_daily_backtest(self, trading_days):
        """
        运行日线回测。
        """
        previous_day = None
        for day in trading_days:
            self.context.current_dt = day
            self.context.previous_date = previous_day.date() if previous_day is not None else day.date()
            log.current_dt = day.replace(hour=9, minute=30)

            # 重置当日订单和成交数据
            self.context.blotter.reset_daily_data()

            self.current_data = {sec: df.loc[day] for sec, df in self.data.items() if day in df.index}
            self._update_position_prices()
            self._execute_trading_session()

            current_prices = {sec: data['close'] for sec, data in self.current_data.items()}
            self._update_portfolio_value(current_prices)
            self.portfolio_history.append({
                'datetime': day, 'total_value': self.portfolio.total_value, 'cash': self.portfolio.cash
            })
            previous_day = day

    def _run_minute_backtest(self, trading_times):
        """
        运行分钟级回测。
        """
        current_day = None
        previous_time = None
        for current_time in trading_times:
            self.context.current_dt = current_time
            self.context.previous_date = previous_time.date() if previous_time is not None else current_time.date()
            log.current_dt = current_time
            self.current_data = {sec: df.loc[current_time] for sec, df in self.data.items() if current_time in df.index}
            self._update_position_prices()

            if current_day is None or current_time.date() != current_day:
                current_day = current_time.date()
                if hasattr(self.strategy, 'before_trading_start'):
                    self.strategy.before_trading_start(self.context, self.current_data)

            if hasattr(self.strategy, 'handle_data'):
                self.strategy.handle_data(self.context, self.current_data)

            if current_time.hour == 15 and current_time.minute == 0 and hasattr(self.strategy, 'after_trading_end'):
                self.strategy.after_trading_end(self.context, self.current_data)

            current_prices = {sec: data['close'] for sec, data in self.current_data.items()}
            self._update_portfolio_value(current_prices)

            if current_time.minute == 0 or (current_time.hour == 15 and current_time.minute == 0):
                self.portfolio_history.append({
                    'datetime': current_time, 'total_value': self.portfolio.total_value, 'cash': self.portfolio.cash
                })
            previous_time = current_time

    def _update_position_prices(self):
        """
        更新持仓最新价格。
        """
        for stock, pos in self.context.portfolio.positions.items():
            if stock in self.current_data:
                pos.last_sale_price = self.current_data[stock]['close']

    def _execute_trading_session(self):
        """
        执行日线交易会话。
        """
        if hasattr(self.strategy, 'before_trading_start'):
            self.strategy.before_trading_start(self.context, self.current_data)

        if hasattr(self.strategy, 'handle_data'):
            self.strategy.handle_data(self.context, self.current_data)

        if hasattr(self.strategy, 'after_trading_end'):
            log.current_dt = self.context.current_dt.replace(hour=15, minute=30)
            self.strategy.after_trading_end(self.context, self.current_data)

    def _generate_performance_report(self):
        """生成性能分析报告"""
        from .performance import print_performance_report
        from .utils import get_benchmark_returns

        # 获取基准收益率（如果设置了基准）
        benchmark_returns = None
        if hasattr(self, 'benchmark') and self.benchmark:
            benchmark_returns = get_benchmark_returns(self, self.start_date, self.end_date)

        # 打印性能报告
        print_performance_report(self, benchmark_returns)