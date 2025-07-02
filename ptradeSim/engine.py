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
    """
    def __init__(self, strategy_file, data_path, start_date, end_date, initial_cash):
        self.strategy_file = strategy_file
        self.data_path = data_path
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_cash = initial_cash
        
        self.portfolio = Portfolio(initial_cash)
        self.context = Context(self.portfolio)
        self.data = self._load_data()
        self.current_data = {}
        
        self.daily_portfolio_history = []
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
        """
        try:
            df = pd.read_csv(self.data_path, parse_dates=['date'], index_col='date')
        except FileNotFoundError:
            ptrade_api.log.warning(f"错误：在 {self.data_path} 找不到数据文件")
            return {}

        data_by_security = {security: group for security, group in df.groupby('security')}
        return data_by_security

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
        运行回测。
        """
        # 记录回测开始
        from datetime import datetime
        import os
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 动态获取策略名称（从文件路径中提取，去掉.py扩展名）
        strategy_name = os.path.basename(self.strategy_file).replace('.py', '')
        print(f"{start_time} 开始运行回测, 策略名称: {strategy_name}")

        # 1. 调用策略初始化函数
        if hasattr(self.strategy, 'initialize'):
            self.strategy.initialize(self.context)

        # 2. 获取所有交易日
        trading_days = self.data['STOCK_A'].index
        trading_days = trading_days[(trading_days >= self.start_date) & (trading_days <= self.end_date)]

        # 3. 模拟每日交易
        previous_day = None
        for day in trading_days:
            self.context.current_dt = day
            # 对于第一个交易日，使用当前日期作为previous_date，避免None值导致的错误
            self.context.previous_date = previous_day.date() if previous_day is not None else day.date()

            # 更新Logger的当前时间，支持ptrade风格的时间戳
            ptrade_api.log.current_dt = day.replace(hour=9, minute=30)  # 模拟开盘时间

            # 准备当日数据
            self.current_data = {sec: df.loc[day] for sec, df in self.data.items() if day in df.index}
            
            # 更新持仓最新价格
            for stock, pos in self.context.portfolio.positions.items():
                if stock in self.current_data:
                    pos.last_sale_price = self.current_data[stock]['close']

            # 运行交易逻辑
            if hasattr(self.strategy, 'before_trading_start'):
                self.strategy.before_trading_start(self.context, self.current_data)

            if hasattr(self.strategy, 'handle_data'):
                self.strategy.handle_data(self.context, self.current_data)

            if hasattr(self.strategy, 'after_trading_end'):
                # 设置收盘时间的时间戳
                ptrade_api.log.current_dt = day.replace(hour=15, minute=30)
                self.strategy.after_trading_end(self.context, self.current_data)

            # 更新并记录每日资产
            current_prices = {sec: data['close'] for sec, data in self.current_data.items()}
            self._update_portfolio_value(current_prices)
            self.daily_portfolio_history.append(self.portfolio.total_value)

            previous_day = day

        # 设置最终时间戳
        ptrade_api.log.current_dt = None  # 使用当前系统时间
        ptrade_api.log.info("策略回测结束")
        
