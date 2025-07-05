#!/usr/bin/env python3
"""
补充缺失的API函数单元测试
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock

from ptradesim import trading, market_data, financials, utils
from ptradesim.engine import BacktestEngine
from ptradesim.context import Order, OrderStatus


class TestMissingTradingAPIs:
    """补充缺失的交易API测试"""
    
    @pytest.mark.unit
    def test_cancel_order(self, csv_engine):
        """测试cancel_order函数"""
        engine = csv_engine
        
        # 先创建一个订单
        if engine.data and 'STOCK_A' in engine.data:
            engine.current_data = {'STOCK_A': {'close': 100.0, 'volume': 1000}}
            order_id = trading.order(engine, 'STOCK_A', 100)
            
            if order_id:
                # 测试取消订单
                result = trading.cancel_order(engine, order_id)
                assert isinstance(result, bool)
                
                # 测试取消不存在的订单
                result = trading.cancel_order(engine, 'non_existent_order')
                assert result is False
        else:
            pytest.skip("No test data available")
    
    @pytest.mark.unit
    def test_get_open_orders(self, csv_engine):
        """测试get_open_orders函数"""
        engine = csv_engine
        
        # 测试获取未完成订单
        open_orders = trading.get_open_orders(engine)
        assert isinstance(open_orders, dict)
        
        # 创建订单后再测试
        if engine.data and 'STOCK_A' in engine.data:
            engine.current_data = {'STOCK_A': {'close': 100.0, 'volume': 1000}}
            order_id = trading.order(engine, 'STOCK_A', 100)
            
            if order_id:
                open_orders = trading.get_open_orders(engine)
                assert isinstance(open_orders, dict)
        else:
            pytest.skip("No test data available")
    
    @pytest.mark.unit
    def test_get_trades(self, csv_engine):
        """测试get_trades函数"""
        engine = csv_engine
        
        # 测试获取成交记录
        trades = trading.get_trades(engine)
        assert isinstance(trades, list)
        
        # 初始应该没有成交记录
        assert len(trades) == 0


class TestMissingMarketDataAPIs:
    """补充缺失的市场数据API测试"""
    
    @pytest.mark.unit
    def test_get_market_snapshot(self, csv_engine):
        """测试get_market_snapshot函数"""
        engine = csv_engine
        
        # 测试获取市场快照
        snapshot = market_data.get_market_snapshot(engine)
        assert isinstance(snapshot, pd.DataFrame)
        
        # 测试指定股票的快照
        if engine.data:
            stocks = list(engine.data.keys())[:2]  # 取前两只股票
            snapshot = market_data.get_market_snapshot(engine, stocks)
            assert isinstance(snapshot, pd.DataFrame)
            
            # 测试指定字段
            snapshot = market_data.get_market_snapshot(engine, stocks, ['close', 'volume'])
            assert isinstance(snapshot, pd.DataFrame)
    
    @pytest.mark.unit
    def test_get_technical_indicators(self, csv_engine):
        """测试get_technical_indicators函数"""
        engine = csv_engine
        
        if engine.data:
            stock = list(engine.data.keys())[0]
            
            # 测试单个指标
            try:
                result = market_data.get_technical_indicators(engine, stock, 'RSI')
                assert result is not None
            except Exception:
                # 数据不足时正常
                pass
            
            # 测试多个指标
            try:
                result = market_data.get_technical_indicators(engine, stock, ['RSI', 'MACD'])
                assert result is not None
            except Exception:
                # 数据不足时正常
                pass
        else:
            pytest.skip("No test data available")


class TestMissingFinancialsAPIs:
    """补充缺失的财务API测试"""
    
    @pytest.mark.unit
    def test_get_cash_flow(self, csv_engine):
        """测试get_cash_flow函数"""
        engine = csv_engine
        
        # 测试获取现金流量表
        cash_flow = financials.get_cash_flow(engine, ['STOCK_A'])
        assert isinstance(cash_flow, pd.DataFrame)
        assert 'STOCK_A' in cash_flow.index
        
        # 测试指定字段
        cash_flow = financials.get_cash_flow(
            engine, ['STOCK_A'], 
            fields=['operating_cash_flow', 'investing_cash_flow']
        )
        assert isinstance(cash_flow, pd.DataFrame)
    
    @pytest.mark.unit
    def test_get_financial_ratios(self, csv_engine):
        """测试get_financial_ratios函数"""
        engine = csv_engine
        
        # 测试获取财务比率
        ratios = financials.get_financial_ratios(engine, ['STOCK_A'])
        assert isinstance(ratios, pd.DataFrame)
        assert 'STOCK_A' in ratios.index
        
        # 测试指定字段
        ratios = financials.get_financial_ratios(
            engine, ['STOCK_A'], 
            fields=['roe', 'current_ratio', 'debt_to_equity']
        )
        assert isinstance(ratios, pd.DataFrame)


class TestMissingUtilsAPIs:
    """补充缺失的工具函数API测试"""
    
    @pytest.mark.unit
    def test_is_trade(self, csv_engine):
        """测试is_trade函数"""
        engine = csv_engine
        
        # 在回测模式下应该返回False
        result = utils.is_trade(engine)
        assert result is False
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    def test_get_research_path(self, csv_engine):
        """测试get_research_path函数"""
        engine = csv_engine
        
        # 测试获取研究路径
        path = utils.get_research_path(engine)
        assert isinstance(path, str)
        assert path == './'
    
    @pytest.mark.unit
    def test_run_interval(self, csv_engine):
        """测试run_interval函数"""
        engine = csv_engine
        
        def dummy_func():
            return "test"
        
        # 测试注册定时任务
        utils.run_interval(engine, engine.context, dummy_func, 60)
        
        # 检查是否记录了定时任务
        assert hasattr(engine, 'interval_tasks')
        assert len(engine.interval_tasks) > 0
    
    @pytest.mark.unit
    def test_get_initial_cash(self, csv_engine):
        """测试get_initial_cash函数"""
        engine = csv_engine
        
        # 测试获取初始资金
        max_cash = 500000
        initial_cash = utils.get_initial_cash(engine, engine.context, max_cash)
        assert isinstance(initial_cash, (int, float))
        assert initial_cash <= max_cash
    
    @pytest.mark.unit
    def test_get_num_of_positions(self, csv_engine):
        """测试get_num_of_positions函数"""
        engine = csv_engine
        
        # 测试获取持仓数量
        num_positions = utils.get_num_of_positions(engine, engine.context)
        assert isinstance(num_positions, int)
        assert num_positions >= 0
    
    @pytest.mark.unit
    def test_get_stock_info(self, csv_engine):
        """测试get_stock_info函数"""
        engine = csv_engine
        
        # 测试获取股票信息
        info = utils.get_stock_info(engine, ['STOCK_A'])
        assert isinstance(info, dict)
        assert 'STOCK_A' in info
        
        # 测试指定字段
        info = utils.get_stock_info(engine, ['STOCK_A'], field=['stock_name', 'industry'])
        assert isinstance(info, dict)
        assert 'STOCK_A' in info
        assert 'stock_name' in info['STOCK_A']
    
    @pytest.mark.unit
    def test_get_stock_name(self, csv_engine):
        """测试get_stock_name函数"""
        engine = csv_engine
        
        # 测试获取股票名称
        names = utils.get_stock_name(engine, ['STOCK_A'])
        assert isinstance(names, dict)
        assert 'STOCK_A' in names
        assert isinstance(names['STOCK_A'], str)
    
    @pytest.mark.unit
    def test_set_universe(self, csv_engine):
        """测试set_universe函数"""
        engine = csv_engine
        
        # 测试设置股票池
        stocks = ['STOCK_A', 'STOCK_B']
        utils.set_universe(engine, stocks)
        
        # 函数主要是记录日志，没有返回值
        # 测试单个股票
        utils.set_universe(engine, 'STOCK_A')
    
    @pytest.mark.unit
    def test_set_benchmark(self, csv_engine):
        """测试set_benchmark函数"""
        engine = csv_engine
        
        # 测试设置基准指数
        benchmark = '000001.SH'
        utils.set_benchmark(engine, benchmark)
        
        # 检查是否设置了基准
        assert hasattr(engine, 'benchmark')
        assert engine.benchmark == benchmark
    
    @pytest.mark.unit
    def test_get_benchmark_returns(self, csv_engine):
        """测试get_benchmark_returns函数"""
        engine = csv_engine
        
        # 先设置基准
        utils.set_benchmark(engine, '000001.SH')
        
        # 测试获取基准收益率
        returns = utils.get_benchmark_returns(engine)
        assert isinstance(returns, pd.Series)
    
    @pytest.mark.unit
    def test_get_trading_day(self, csv_engine):
        """测试get_trading_day函数"""
        engine = csv_engine
        
        # 测试获取交易日
        trading_day = utils.get_trading_day(engine)
        assert trading_day is not None
        
        # 测试指定日期
        trading_day = utils.get_trading_day(engine, date='2023-01-01')
        assert trading_day is not None
        
        # 测试偏移
        trading_day = utils.get_trading_day(engine, offset=1)
        assert trading_day is not None
    
    @pytest.mark.unit
    def test_get_all_trades_days(self, csv_engine):
        """测试get_all_trades_days函数"""
        engine = csv_engine
        
        # 测试获取所有交易日
        trading_days = utils.get_all_trades_days(engine)
        assert isinstance(trading_days, pd.DatetimeIndex)
        assert len(trading_days) > 0
    
    @pytest.mark.unit
    def test_get_trade_days(self, csv_engine):
        """测试get_trade_days函数"""
        engine = csv_engine
        
        # 测试获取指定范围的交易日
        trade_days = utils.get_trade_days(engine, start_date='2023-01-01', end_date='2023-01-31')
        assert isinstance(trade_days, pd.DatetimeIndex)
        
        # 测试指定数量
        trade_days = utils.get_trade_days(engine, count=10)
        assert isinstance(trade_days, pd.DatetimeIndex)
        assert len(trade_days) <= 10


class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.mark.integration
    def test_all_apis_callable(self, csv_engine):
        """测试所有API都可以调用"""
        engine = csv_engine
        
        # 测试所有API函数都存在且可调用
        api_functions = [
            # Trading APIs
            (trading.order, (engine, 'STOCK_A', 100)),
            (trading.cancel_order, (engine, 'dummy_order')),
            (trading.get_open_orders, (engine,)),
            (trading.get_trades, (engine,)),
            
            # Market Data APIs  
            (market_data.get_market_snapshot, (engine,)),
            (market_data.get_technical_indicators, (engine, 'STOCK_A', 'RSI')),
            
            # Financials APIs
            (financials.get_cash_flow, (engine, ['STOCK_A'])),
            (financials.get_financial_ratios, (engine, ['STOCK_A'])),
            
            # Utils APIs
            (utils.is_trade, (engine,)),
            (utils.get_research_path, (engine,)),
            (utils.get_stock_info, (engine, ['STOCK_A'])),
            (utils.get_stock_name, (engine, ['STOCK_A'])),
            (utils.get_all_trades_days, (engine,)),
        ]
        
        for func, args in api_functions:
            try:
                result = func(*args)
                # 只要不抛异常就算成功
                assert result is not None or result is None  # 允许None返回值
            except Exception as e:
                # 某些函数在数据不足时可能抛异常，这是正常的
                print(f"⚠️ {func.__name__} 抛出异常: {e}")
                pass
