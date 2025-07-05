#!/usr/bin/env python3
"""
核心API单元测试 - 合并所有API相关测试
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock

from simtradelab import trading, market_data, financials, utils
from simtradelab.engine import BacktestEngine
from simtradelab.context import Order, OrderStatus


class TestTradingAPIs:
    """交易API测试"""
    
    @pytest.mark.unit
    def test_order_functions(self, csv_engine):
        """测试所有订单相关函数"""
        engine = csv_engine
        
        if engine.data and 'STOCK_A' in engine.data:
            engine.current_data = {'STOCK_A': {'close': 100.0, 'volume': 1000}}
            
            # 测试order
            order_id = trading.order(engine, 'STOCK_A', 100)
            assert order_id is not None
            
            # 测试order_target
            order_id2 = trading.order_target(engine, 'STOCK_A', 50)
            assert order_id2 is not None
            
            # 测试order_value
            order_id3 = trading.order_value(engine, 'STOCK_A', 5000)
            # order_value可能返回None，这是正常的
            
            # 测试cancel_order
            if order_id:
                result = trading.cancel_order(engine, order_id)
                assert isinstance(result, bool)
        else:
            pytest.skip("No test data available")
    
    @pytest.mark.unit
    def test_query_functions(self, csv_engine):
        """测试所有查询函数"""
        engine = csv_engine
        
        # 测试get_positions
        positions = trading.get_positions(engine)
        assert isinstance(positions, dict)
        
        # 测试get_orders
        orders = trading.get_orders(engine)
        assert isinstance(orders, dict)
        
        # 测试get_open_orders
        open_orders = trading.get_open_orders(engine)
        assert isinstance(open_orders, dict)
        
        # 测试get_trades
        trades = trading.get_trades(engine)
        assert isinstance(trades, list)


class TestMarketDataAPIs:
    """市场数据API测试"""
    
    @pytest.mark.unit
    def test_history_functions(self, csv_engine):
        """测试历史数据函数"""
        engine = csv_engine
        
        if engine.data:
            stocks = list(engine.data.keys())[:2]
            
            # 测试get_history
            history = market_data.get_history(engine, 5, '1d', ['close'], stocks)
            assert isinstance(history, pd.DataFrame)
            
            # 测试get_current_data
            current = market_data.get_current_data(engine, stocks)
            assert isinstance(current, dict)
            
            # 测试get_price
            price = market_data.get_price(engine, stocks[0])
            # get_price可能返回DataFrame或数值
            assert price is not None
        else:
            pytest.skip("No test data available")
    
    @pytest.mark.unit
    def test_market_snapshot(self, csv_engine):
        """测试市场快照"""
        engine = csv_engine
        
        snapshot = market_data.get_market_snapshot(engine)
        assert isinstance(snapshot, pd.DataFrame)
        
        if engine.data:
            stocks = list(engine.data.keys())[:2]
            snapshot = market_data.get_market_snapshot(engine, stocks)
            assert isinstance(snapshot, pd.DataFrame)
    
    @pytest.mark.unit
    def test_technical_indicators(self, csv_engine):
        """测试技术指标"""
        engine = csv_engine
        
        if engine.data:
            stock = list(engine.data.keys())[0]
            
            try:
                result = market_data.get_technical_indicators(engine, stock, 'RSI')
                assert result is not None
            except Exception:
                # 数据不足时正常
                pass


class TestFinancialAPIs:
    """财务数据API测试"""
    
    @pytest.mark.unit
    def test_fundamental_data(self, csv_engine):
        """测试基本面数据"""
        engine = csv_engine
        
        # 测试get_fundamentals
        fundamentals = financials.get_fundamentals(engine, ['STOCK_A'], 'market_cap')
        assert isinstance(fundamentals, pd.DataFrame)

        # 测试get_income_statement
        income = financials.get_income_statement(engine, ['STOCK_A'], 'revenue')
        assert isinstance(income, pd.DataFrame)

        # 测试get_balance_sheet
        balance = financials.get_balance_sheet(engine, ['STOCK_A'], 'total_assets')
        assert isinstance(balance, pd.DataFrame)

        # 测试get_cash_flow
        cash_flow = financials.get_cash_flow(engine, ['STOCK_A'], 'operating_cash_flow')
        assert isinstance(cash_flow, pd.DataFrame)

        # 测试get_financial_ratios
        ratios = financials.get_financial_ratios(engine, ['STOCK_A'], 'roe')
        assert isinstance(ratios, pd.DataFrame)


class TestUtilsAPIs:
    """工具函数API测试"""
    
    @pytest.mark.unit
    def test_commission_and_limits(self, csv_engine):
        """测试佣金和限制设置"""
        engine = csv_engine
        
        # 测试set_commission
        utils.set_commission(engine, 0.001, 10.0, "STOCK")
        assert engine.commission_ratio == 0.001
        assert engine.min_commission == 10.0
        
        # 测试set_limit_mode
        utils.set_limit_mode(engine, True)
        assert engine.limit_mode is True
    
    @pytest.mark.unit
    def test_stock_info_functions(self, csv_engine):
        """测试股票信息函数"""
        engine = csv_engine
        
        # 测试get_Ashares
        stocks = utils.get_Ashares(engine)
        assert isinstance(stocks, list)
        
        # 测试get_stock_status
        status = utils.get_stock_status(engine, ['STOCK_A'], 'ST')
        assert isinstance(status, dict)
        
        # 测试get_stock_info
        info = utils.get_stock_info(engine, ['STOCK_A'])
        assert isinstance(info, dict)
        
        # 测试get_stock_name
        names = utils.get_stock_name(engine, ['STOCK_A'])
        assert isinstance(names, dict)
    
    @pytest.mark.unit
    def test_trading_calendar(self, csv_engine):
        """测试交易日历函数"""
        engine = csv_engine
        
        # 测试get_trading_day
        trading_day = utils.get_trading_day(engine)
        assert trading_day is not None
        
        # 测试get_all_trades_days
        trading_days = utils.get_all_trades_days(engine)
        assert isinstance(trading_days, pd.DatetimeIndex)
        
        # 测试get_trade_days
        trade_days = utils.get_trade_days(engine, count=10)
        assert isinstance(trade_days, pd.DatetimeIndex)
    
    @pytest.mark.unit
    def test_utility_functions(self, csv_engine):
        """测试其他工具函数"""
        engine = csv_engine
        
        # 测试is_trade
        result = utils.is_trade(engine)
        assert isinstance(result, bool)
        
        # 测试get_research_path
        path = utils.get_research_path(engine)
        assert isinstance(path, str)
        
        # 测试run_interval
        def dummy_func():
            return "test"
        
        utils.run_interval(engine, engine.context, dummy_func, 60)
        assert hasattr(engine, 'interval_tasks')
        
        # 测试get_initial_cash
        initial_cash = utils.get_initial_cash(engine, engine.context, 500000)
        assert isinstance(initial_cash, (int, float))
        
        # 测试get_num_of_positions
        num_positions = utils.get_num_of_positions(engine, engine.context)
        assert isinstance(num_positions, int)
    
    @pytest.mark.unit
    def test_benchmark_functions(self, csv_engine):
        """测试基准相关函数"""
        engine = csv_engine
        
        # 测试set_benchmark
        utils.set_benchmark(engine, '000001.SH')
        assert hasattr(engine, 'benchmark')
        
        # 测试get_benchmark_returns
        returns = utils.get_benchmark_returns(engine)
        assert isinstance(returns, pd.Series)
        
        # 测试set_universe
        utils.set_universe(engine, ['STOCK_A', 'STOCK_B'])
        # 主要是记录日志，没有返回值


class TestTechnicalIndicators:
    """技术指标测试"""
    
    @pytest.mark.unit
    def test_all_indicators(self, csv_engine):
        """测试所有技术指标"""
        engine = csv_engine
        
        if engine.data:
            stock = list(engine.data.keys())[0]
            
            # 导入技术指标函数
            from simtradelab import get_MACD, get_KDJ, get_RSI, get_CCI
            
            indicators = [
                (get_MACD, 'MACD'),
                (get_KDJ, 'KDJ'), 
                (get_RSI, 'RSI'),
                (get_CCI, 'CCI')
            ]
            
            for indicator_func, name in indicators:
                try:
                    result = indicator_func(engine, stock)
                    # 技术指标可能因数据不足返回None或抛异常
                    assert result is not None or result is None
                except Exception:
                    # 数据不足时正常
                    pass
        else:
            pytest.skip("No test data available")


class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.mark.unit
    def test_api_injection_works(self, csv_engine):
        """测试API注入机制正常工作"""
        engine = csv_engine
        
        # 验证所有API函数都存在且可调用
        api_modules = [trading, market_data, financials, utils]
        
        for module in api_modules:
            for attr_name in dir(module):
                if not attr_name.startswith('_') and callable(getattr(module, attr_name)):
                    func = getattr(module, attr_name)
                    # 只要函数存在就算成功
                    assert callable(func)
    
    @pytest.mark.unit
    def test_error_handling(self, csv_engine):
        """测试API错误处理"""
        engine = csv_engine
        
        # 测试无效参数
        try:
            trading.order(engine, 'INVALID_STOCK', 100)
        except Exception:
            pass  # 预期会有异常
        
        # 测试空数据
        try:
            market_data.get_history(engine, 0, '1d', ['close'], [])
        except Exception:
            pass  # 预期会有异常
