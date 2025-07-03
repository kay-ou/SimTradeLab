# -*- coding: utf-8 -*-
"""
回测引擎模块
"""
import importlib.util
import os
import types
from datetime import datetime
from functools import partial

import numpy as np
import pandas as pd

from . import financials, market_data, trading, utils
from .context import Context, Portfolio
from .logger import log


class BacktestEngine:
    """
    回测引擎，负责加载策略、模拟交易并运行回测。
    """

    def __init__(self, strategy_file, data_path, start_date, end_date, initial_cash, frequency='1d'):
        self.strategy_file = strategy_file
        self.data_path = data_path
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_cash = initial_cash
        self.frequency = frequency
        self.portfolio = Portfolio(initial_cash)
        self.context = Context(self.portfolio)
        self.data = self._load_data()
        self.current_data = {}
        self.portfolio_history = []
        self.strategy = self._load_strategy()

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

        api_modules = [financials, market_data, trading, utils]
        for module in api_modules:
            for func_name in dir(module):
                if not func_name.startswith("__"):
                    api_func = getattr(module, func_name)
                    if callable(api_func):
                        setattr(strategy_module, func_name, partial(api_func, self))

        return strategy_module

    def _load_data(self):
        """
        从CSV文件加载K线数据，并按证券代码分组。
        """
        try:
            df = pd.read_csv(self.data_path)
            datetime_col = next((col for col in ['datetime', 'date', 'timestamp'] if col in df.columns), None)

            if datetime_col is None:
                log.warning("错误：找不到日期时间列（datetime/date/timestamp）")
                return {}

            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df.set_index(datetime_col, inplace=True)

        except FileNotFoundError:
            log.warning(f"错误：在 {self.data_path} 找不到数据文件")
            return {}
        except Exception as e:
            log.warning(f"错误：加载数据文件失败 - {e}")
            return {}

        if self.frequency in ['1m', '5m', '15m', '30m'] and self._is_daily_data(df):
            df = self._generate_minute_data(df)

        # return dict(df.groupby('security')) 应该这个就可以了，但出错，怀疑python或者pandas的bug
        return {k: v for k, v in df.groupby('security')}


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

    def _run_daily_backtest(self, trading_days):
        """
        运行日线回测。
        """
        previous_day = None
        for day in trading_days:
            self.context.current_dt = day
            self.context.previous_date = previous_day.date() if previous_day is not None else day.date()
            log.current_dt = day.replace(hour=9, minute=30)
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