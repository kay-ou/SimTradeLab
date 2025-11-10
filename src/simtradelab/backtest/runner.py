# -*- coding: utf-8 -*-
"""
回测执行器

负责策略加载、回测主循环、信号处理等
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import signal
import sys
import time
import json
import logging
import os

from simtradelab.ptrade.context import Context
from simtradelab.ptrade.object import Global, LazyDataDict, Data, clear_daily_cache, BacktestContext
from simtradelab.backtest.stats import generate_backtest_report, generate_backtest_charts, print_backtest_report
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.service.data_server import DataServer

class BacktestRunner:
    """回测执行器"""

    def __init__(self, data_path, use_data_server=True):
        self.data_path = data_path
        self.use_data_server = use_data_server

        # 数据容器
        self.stock_data_dict = None
        self.valuation_dict = None
        self.fundamentals_dict = None
        self.exrights_dict = None
        self.benchmark_data = None
        self.stock_metadata = None
        self.index_constituents = {}
        self.stock_status_history = {}

        # 用于传统模式
        self.stock_data_store = None
        self.fundamentals_store = None

        self.g = Global()
        self.log = None
        self.context = None

        self.backtest_stats = {
            'portfolio_values': [],
            'positions_count': [],
            'daily_pnl': [],
            'daily_buy_amount': [],
            'daily_sell_amount': [],
            'daily_positions_value': [],
            'trade_dates': [],
        }

        signal.signal(signal.SIGINT, self._signal_handler)

    def __enter__(self):
        """进入上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器，但不关闭数据文件（数据常驻）"""
        # 数据服务器模式：不关闭文件，保持数据常驻
        # 传统模式：关闭文件
        if not self.use_data_server:
            self._close_stores()
        return False

    def _signal_handler(self, sig, frame):
        """处理Ctrl+C信号，优雅关闭资源"""
        print("\n\n收到中断信号...")
        if self.use_data_server:
            print("数据保持常驻，下次运行无需重新加载")
        else:
            print("正在关闭数据文件...")
            self._close_stores()
        # 立即退出，不返回到调用点
        os._exit(0)

    def _close_stores(self):
        """关闭HDF5存储"""
        # 数据服务器模式下不关闭（数据常驻）
        if self.use_data_server:
            return

        # 传统模式才关闭
        for store in [self.stock_data_store, self.fundamentals_store]:
            if store is not None:
                try:
                    store.close()
                except Exception:
                    pass

    def load_data(self):
        """加载数据（支持服务器模式和传统模式）"""
        if self.use_data_server:
            # 服务器模式：使用单例，数据常驻内存
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
            return data_server.get_benchmark_data()

        # 传统模式：每次重新加载
        print("=" * 70)
        print("加载本地数据...")
        print("=" * 70)

        self.stock_data_store = pd.HDFStore(f'{self.data_path}/ptrade_data.h5', 'r')
        self.fundamentals_store = pd.HDFStore(f'{self.data_path}/ptrade_fundamentals.h5', 'r')

        # 提取所有表的键名
        all_stock_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/stock_data/')]
        valuation_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/valuation/')]
        fundamentals_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/fundamentals/')]
        exrights_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/exrights/')]

        # 构建数据字典（基本面预加载，价格数据延迟加载）
        print("预加载基本面数据...")
        self.stock_data_dict = LazyDataDict(self.stock_data_store, '/stock_data/', all_stock_keys, max_cache_size=2000)
        self.valuation_dict = LazyDataDict(self.fundamentals_store, '/valuation/', valuation_keys, preload=True)
        self.fundamentals_dict = LazyDataDict(self.fundamentals_store, '/fundamentals/', fundamentals_keys, preload=True)
        self.exrights_dict = LazyDataDict(self.stock_data_store, '/exrights/', exrights_keys, max_cache_size=800)

        print(f"✓ 股票数据: {len(all_stock_keys)} 只")
        print(f"✓ 基本面数据: {len(valuation_keys)} 只")
        print(f"✓ 除权数据: {len(exrights_keys)} 只")

        # 加载元数据和基准
        self.stock_metadata = self.stock_data_store['/stock_metadata']
        benchmark_df = self.stock_data_store['/benchmark']
        metadata = self.stock_data_store['/metadata']

        if 'index_constituents' in metadata.index and pd.notna(metadata['index_constituents']):
            self.index_constituents = json.loads(metadata['index_constituents'])
        if 'stock_status_history' in metadata.index and pd.notna(metadata['stock_status_history']):
            self.stock_status_history = json.loads(metadata['stock_status_history'])

        self.benchmark_data = {'000300.SS': benchmark_df}
        print("✓ 数据加载完成\n")

        return benchmark_df

    def load_strategy(self, strategy_name, strategies_path):
        """加载并初始化策略"""
        strategy_path = f'{strategies_path}/{strategy_name}/backtest.py'
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_code = f.read()

        api = PtradeAPI(
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
            context=self.context,
            log=self.log
        )

        # 创建策略执行环境
        strategy_namespace = {
            '__name__': '__main__',
            '__file__': strategy_path,
            'g': self.g,
            'log': self.log,
            'context': self.context,
        }

        # 注入API方法
        for attr_name in dir(api):
            if not attr_name.startswith('_'):
                attr = getattr(api, attr_name)
                if callable(attr) or attr_name == 'FUNDAMENTAL_TABLES':
                    strategy_namespace[attr_name] = attr

        exec(strategy_code, strategy_namespace)
        print("✓ 策略加载完成\n")

        return strategy_namespace, api

    def run(self, strategy_name, start_date, end_date, strategies_path):
        """运行回测

        Args:
            strategy_name: 策略名称
            start_date: 开始日期
            end_date: 结束日期
            strategies_path: 策略文件路径

        Returns:
            dict: 回测报告
        """
        try:
            # 加载数据
            benchmark_df = self.load_data()

            print(f"\n开始运行回测, 策略名称: {strategy_name}")

            # 回测参数
            start_date = pd.Timestamp(start_date)
            end_date = pd.Timestamp(end_date)

            # 创建日志
            log_filename = f'{strategies_path}/{strategy_name}/backtest_{start_date.strftime("%y%m%d")}_{end_date.strftime("%y%m%d")}_{datetime.now().strftime("%y%m%d_%H%M%S")}.log'
            print(f"日志文件: {log_filename}")

            # 配置日志（实时刷新）
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

            # 加载策略
            strategy_namespace, api = self.load_strategy(strategy_name, strategies_path)

            # 预构建日期索引（性能关键优化）
            #print("预构建股票日期索引...")
            #api.prebuild_date_index()

            # 创建交易日序列
            date_range = benchmark_df.index[
                (benchmark_df.index >= start_date) &
                (benchmark_df.index <= end_date) &
                (benchmark_df['volume'] > 0)
            ]

            self.log.info(f"回测周期: {start_date.date()} 至 {end_date.date()}")
            self.log.info(f"交易日数: {len(date_range)} 天\n")

            # 初始化context
            from simtradelab.ptrade.object import Portfolio
            portfolio = Portfolio(1000000)  # 初始资金100万
            self.context = Context(portfolio=portfolio, current_dt=start_date)
            api.context = self.context

            # 初始化回测上下文
            bt_ctx = BacktestContext(
                stock_data_dict=self.stock_data_dict,
                get_stock_date_index_func=api.get_stock_date_index,
                check_limit_func=api.check_limit,
                log_obj=self.log,
                context_obj=self.context
            )

            # 更新context和blotter的bt_ctx
            self.context.portfolio._bt_ctx = bt_ctx
            self.context.blotter._bt_ctx = bt_ctx

            # 更新策略命名空间
            strategy_namespace.update({'context': self.context, 'g': self.g, 'log': self.log})

            print("初始化策略...")
            strategy_namespace['initialize'](self.context)

            # 逐日回测
            start_time = time.time()

            for current_date in date_range:
                self.context.current_dt = current_date
                self.context.previous_date = (current_date - timedelta(days=1)).date()
                self.context.blotter.current_dt = current_date

                # 每日开始前清理全局缓存（防止内存膨胀）
                clear_daily_cache()

                # 记录当日开始前的状态
                prev_portfolio_value = self.context.portfolio.portfolio_value
                prev_cash = self.context.portfolio._cash

                # 记录当日组合价值（开盘前）
                self.backtest_stats['portfolio_values'].append(prev_portfolio_value)
                self.backtest_stats['positions_count'].append(
                    sum(1 for p in self.context.portfolio.positions.values() if p.amount > 0)
                )
                self.backtest_stats['trade_dates'].append(current_date)

                # 构造data对象
                data = Data(current_date, bt_ctx)

                # 调用before_trading_start
                try:
                    strategy_namespace['before_trading_start'](self.context, data)
                except Exception as e:
                    self.log.error(f"before_trading_start执行失败: {e}")
                    import traceback
                    traceback.print_exc()
                    break

                # 调用handle_data
                try:
                    strategy_namespace['handle_data'](self.context, data)
                except Exception as e:
                    self.log.error(f"handle_data执行失败: {e}")
                    import traceback
                    traceback.print_exc()
                    break

                # 记录当日交易金额
                cash_change = self.context.portfolio._cash - prev_cash
                self.backtest_stats['daily_buy_amount'].append(max(0, -cash_change))
                self.backtest_stats['daily_sell_amount'].append(max(0, cash_change))

                # 调用after_trading_end
                try:
                    strategy_namespace['after_trading_end'](self.context, data)
                except Exception as e:
                    self.log.error(f"after_trading_end执行失败: {e}")
                    import traceback
                    traceback.print_exc()

                # 记录当日结束后的状态
                after_portfolio_value = self.context.portfolio.portfolio_value
                daily_pnl = after_portfolio_value - prev_portfolio_value
                self.backtest_stats['daily_pnl'].append(daily_pnl)
                self.backtest_stats['daily_positions_value'].append(self.context.portfolio.positions_value)

            # 生成回测报告
            total_elapsed = time.time() - start_time
            report = generate_backtest_report(self.backtest_stats, start_date, end_date, benchmark_df)
            print_backtest_report(report, self.log, start_date, end_date, total_elapsed,
                                np.array(self.backtest_stats['positions_count']))

            # 生成图表
            chart_filename = generate_backtest_charts(
                self.backtest_stats, start_date, end_date,
                self.benchmark_data, strategy_name, strategies_path
            )

            print(f"\n日志已保存至: {log_filename}")
            print(f"图表已保存至: {chart_filename}")

            return report

        finally:
            # 数据服务器模式：不关闭文件，数据保持常驻
            # 传统模式：关闭文件
            if not self.use_data_server:
                print("\n正在关闭数据文件...")
                self._close_stores()
            else:
                print("\n数据保持常驻内存，下次运行无需重新加载")
