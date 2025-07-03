# -*- coding: utf-8 -*-

import importlib.util
from datetime import datetime
import pandas as pd
from functools import partial
import types

from .context import Context, Portfolio
from . import api as ptrade_api

class BacktestEngine:
    """
    回测引擎，负责加载策略、模拟交易并运行回测。
    支持日线和分钟级交易周期。
    """
    def __init__(self, strategy_file, data_path, start_date, end_date, initial_cash, frequency='1d'):
        self.strategy_file = strategy_file
        self.data_path = data_path
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_cash = initial_cash
        self.frequency = frequency  # 交易频率：'1d' 日线, '1m' 分钟线

        self.portfolio = Portfolio(initial_cash)
        self.context = Context(self.portfolio)
        self.data = self._load_data()
        self.current_data = {}

        self.portfolio_history = []  # 改名为更通用的历史记录
        self.strategy = self._load_strategy()


    def _load_strategy(self):
        """
        动态加载指定的策略文件，并注入API和'g'对象。
        加载顺序：先执行策略文件，再注入API，以确保框架API覆盖策略中的同名函数。
        """
        spec = importlib.util.spec_from_file_location("strategy", self.strategy_file)
        strategy_module = importlib.util.module_from_spec(spec)

        # 1. 先执行策略文件，允许它定义自己的函数和变量
        spec.loader.exec_module(strategy_module)

        # 2. 再注入 'g' 对象 (如果策略没有定义)
        if not hasattr(strategy_module, 'g'):
            strategy_module.g = types.SimpleNamespace()

        # 3. 再注入 log 对象, 覆盖策略中的定义 (如果有)
        strategy_module.log = ptrade_api.log

        # 4. 再注入所有API函数, 覆盖策略中的同名函数
        for func_name in dir(ptrade_api):
            api_func = getattr(ptrade_api, func_name)
            # 只注入在 api.py 中定义的函数，避免注入导入的类 (如 Path)
            if callable(api_func) and not func_name.startswith("__") and getattr(api_func, '__module__', None) == ptrade_api.__name__:
                # 使用 partial 绑定引擎实例
                setattr(strategy_module, func_name, partial(api_func, self))
        
        return strategy_module

    def _load_data(self):
        """
        从 CSV 文件加载 K 线数据，并按证券代码分组。
        支持日线和分钟级数据。
        """
        try:
            # 尝试解析日期时间列，支持多种格式
            df = pd.read_csv(self.data_path)

            # 检测日期时间列名
            datetime_col = None
            for col in ['datetime', 'date', 'timestamp']:
                if col in df.columns:
                    datetime_col = col
                    break

            if datetime_col is None:
                ptrade_api.log.warning("错误：找不到日期时间列（datetime/date/timestamp）")
                return {}

            # 解析日期时间并设置为索引
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df.set_index(datetime_col, inplace=True)

        except FileNotFoundError:
            ptrade_api.log.warning(f"错误：在 {self.data_path} 找不到数据文件")
            return {}
        except Exception as e:
            ptrade_api.log.warning(f"错误：加载数据文件失败 - {e}")
            return {}

        # 如果是分钟级频率但数据是日线，则生成分钟级数据
        if self.frequency in ['1m', '5m', '15m', '30m'] and self._is_daily_data(df):
            df = self._generate_minute_data(df)

        data_by_security = {security: group for security, group in df.groupby('security')}
        return data_by_security

    def _is_daily_data(self, df):
        """
        判断数据是否为日线数据
        """
        if df.empty:
            return True

        # 检查时间间隔，如果大于1天则认为是日线数据
        time_diff = df.index[1] - df.index[0] if len(df) > 1 else pd.Timedelta(days=1)
        return time_diff >= pd.Timedelta(days=1)

    def _generate_minute_data(self, daily_df):
        """
        从日线数据生成分钟级数据
        """
        import numpy as np

        # 频率映射
        freq_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30
        }

        minute_interval = freq_map.get(self.frequency, 1)
        trading_minutes = 240  # 4小时交易时间
        periods_per_day = trading_minutes // minute_interval

        minute_data_list = []

        for security in daily_df['security'].unique():
            security_data = daily_df[daily_df['security'] == security].copy()

            for idx, row in security_data.iterrows():
                # 生成当天的分钟级时间索引
                day_start = idx.replace(hour=9, minute=30)
                minute_times = pd.date_range(
                    start=day_start,
                    periods=periods_per_day,
                    freq=f'{minute_interval}T'
                )

                # 模拟分钟级价格波动
                daily_range = row['high'] - row['low']
                daily_volume = row['volume']

                for i, minute_time in enumerate(minute_times):
                    # 基于时间生成价格波动
                    progress = i / periods_per_day

                    # 添加随机波动
                    np.random.seed(int(minute_time.timestamp()) % 10000)  # 确保可重现
                    noise = np.random.normal(0, daily_range * 0.01)  # 1%的随机波动

                    # 计算分钟收盘价
                    minute_close = row['low'] + daily_range * progress + noise
                    minute_close = max(row['low'], min(row['high'], minute_close))

                    # 生成分钟级OHLC
                    minute_open = minute_close * (1 + np.random.normal(0, 0.001))
                    minute_high = minute_close * (1 + abs(np.random.normal(0, 0.002)))
                    minute_low = minute_close * (1 - abs(np.random.normal(0, 0.002)))
                    minute_volume = daily_volume / periods_per_day

                    # 确保OHLC逻辑正确
                    minute_high = max(minute_open, minute_close, minute_high)
                    minute_low = min(minute_open, minute_close, minute_low)

                    minute_data_list.append({
                        'datetime': minute_time,
                        'open': minute_open,
                        'high': minute_high,
                        'low': minute_low,
                        'close': minute_close,
                        'volume': minute_volume,
                        'security': security
                    })

        if minute_data_list:
            minute_df = pd.DataFrame(minute_data_list)
            minute_df.set_index('datetime', inplace=True)
            return minute_df
        else:
            return daily_df

    def _update_portfolio_value(self, current_prices):
        """
        根据当前价格更新投资组合的总价值。
        """
        total_value = self.portfolio.cash
        for security, position in self.portfolio.positions.items():
            price = current_prices.get(security, 0) # 如果价格不存在，则为0
            total_value += position.amount * price
        self.portfolio.total_value = total_value

    def run(self):
        """
        运行回测，支持日线和分钟级交易周期。
        """
        # 记录回测开始
        from datetime import datetime
        import os
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 动态获取策略名称（从文件路径中提取，去掉.py扩展名）
        strategy_name = os.path.basename(self.strategy_file).replace('.py', '')
        print(f"{start_time} 开始运行回测, 策略名称: {strategy_name}, 频率: {self.frequency}")

        # 1. 调用策略初始化函数
        if hasattr(self.strategy, 'initialize'):
            self.strategy.initialize(self.context)

        # 2. 获取交易时间序列
        if not self.data:
            ptrade_api.log.warning("没有可用的数据")
            return

        # 获取第一个股票的时间索引作为基准
        first_security = list(self.data.keys())[0]
        trading_times = self.data[first_security].index
        trading_times = trading_times[(trading_times >= self.start_date) & (trading_times <= self.end_date)]

        if self.frequency == '1d':
            self._run_daily_backtest(trading_times)
        else:
            self._run_minute_backtest(trading_times)

        # 设置最终时间戳
        ptrade_api.log.current_dt = None  # 使用当前系统时间
        ptrade_api.log.info("策略回测结束")

    def _run_daily_backtest(self, trading_days):
        """
        运行日线回测
        """
        previous_day = None
        for day in trading_days:
            self.context.current_dt = day
            self.context.previous_date = previous_day.date() if previous_day is not None else day.date()

            # 更新Logger的当前时间
            ptrade_api.log.current_dt = day.replace(hour=9, minute=30)

            # 准备当日数据
            self.current_data = {sec: df.loc[day] for sec, df in self.data.items() if day in df.index}

            # 更新持仓最新价格
            self._update_position_prices()

            # 运行交易逻辑
            self._execute_trading_session()

            # 更新并记录资产
            current_prices = {sec: data['close'] for sec, data in self.current_data.items()}
            self._update_portfolio_value(current_prices)
            self.portfolio_history.append({
                'datetime': day,
                'total_value': self.portfolio.total_value,
                'cash': self.portfolio.cash
            })

            previous_day = day

    def _run_minute_backtest(self, trading_times):
        """
        运行分钟级回测
        """
        current_day = None
        previous_time = None

        for current_time in trading_times:
            self.context.current_dt = current_time
            self.context.previous_date = previous_time.date() if previous_time is not None else current_time.date()

            # 更新Logger的当前时间
            ptrade_api.log.current_dt = current_time

            # 准备当前时间点数据
            self.current_data = {sec: df.loc[current_time] for sec, df in self.data.items() if current_time in df.index}

            # 更新持仓最新价格
            self._update_position_prices()

            # 检查是否是新的交易日
            if current_day is None or current_time.date() != current_day:
                current_day = current_time.date()
                # 执行盘前逻辑
                if hasattr(self.strategy, 'before_trading_start'):
                    self.strategy.before_trading_start(self.context, self.current_data)

            # 执行分钟级交易逻辑
            if hasattr(self.strategy, 'handle_data'):
                self.strategy.handle_data(self.context, self.current_data)

            # 检查是否是交易日结束（15:00）
            if current_time.hour == 15 and current_time.minute == 0:
                if hasattr(self.strategy, 'after_trading_end'):
                    self.strategy.after_trading_end(self.context, self.current_data)

            # 更新并记录资产（每分钟记录）
            current_prices = {sec: data['close'] for sec, data in self.current_data.items()}
            self._update_portfolio_value(current_prices)

            # 只在整点或收盘时记录历史
            if current_time.minute == 0 or (current_time.hour == 15 and current_time.minute == 0):
                self.portfolio_history.append({
                    'datetime': current_time,
                    'total_value': self.portfolio.total_value,
                    'cash': self.portfolio.cash
                })

            previous_time = current_time

    def _update_position_prices(self):
        """
        更新持仓最新价格
        """
        for stock, pos in self.context.portfolio.positions.items():
            if stock in self.current_data:
                pos.last_sale_price = self.current_data[stock]['close']

    def _execute_trading_session(self):
        """
        执行交易会话（日线模式）
        """
        if hasattr(self.strategy, 'before_trading_start'):
            self.strategy.before_trading_start(self.context, self.current_data)

        if hasattr(self.strategy, 'handle_data'):
            self.strategy.handle_data(self.context, self.current_data)

        if hasattr(self.strategy, 'after_trading_end'):
            # 设置收盘时间的时间戳
            ptrade_api.log.current_dt = self.context.current_dt.replace(hour=15, minute=30)
            self.strategy.after_trading_end(self.context, self.current_data)
        
