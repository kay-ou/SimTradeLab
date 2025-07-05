#!/usr/bin/env python3
"""
核心组件单元测试 - 引擎、上下文、数据源等
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from simtradelab.engine import BacktestEngine
from simtradelab.context import Portfolio, Position, Context, Order, Trade, Blotter
from simtradelab.data_sources.csv_source import CSVDataSource
from simtradelab.data_sources.akshare_source import AkshareDataSource
from simtradelab.data_sources.manager import DataSourceManager


class TestBacktestEngine:
    """回测引擎单元测试"""
    
    @pytest.mark.unit
    def test_engine_initialization(self, sample_strategy_file, sample_data_file):
        """测试引擎初始化"""
        engine = BacktestEngine(
            strategy_file=sample_strategy_file,
            data_path=sample_data_file,
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=100000
        )
        
        assert engine.initial_cash == 100000
        assert str(engine.start_date).startswith('2023-01-01')
        assert str(engine.end_date).startswith('2023-01-05')
        assert engine.frequency == '1d'  # 默认值
        assert hasattr(engine, 'context')
        assert hasattr(engine, 'data')
    
    @pytest.mark.unit
    def test_engine_with_different_frequencies(self, sample_strategy_file, sample_data_file):
        """测试不同频率的引擎初始化"""
        frequencies = ['1d', '1m', '5m', '15m', '30m']
        
        for freq in frequencies:
            engine = BacktestEngine(
                strategy_file=sample_strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-02',
                initial_cash=100000,
                frequency=freq
            )
            assert engine.frequency == freq
    
    @pytest.mark.unit
    def test_engine_data_loading(self, sample_strategy_file, sample_data_file):
        """测试引擎数据加载"""
        engine = BacktestEngine(
            strategy_file=sample_strategy_file,
            data_path=sample_data_file,
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=100000
        )
        
        assert engine.data is not None
        assert isinstance(engine.data, dict)
        assert len(engine.data) > 0
        
        # 检查数据格式
        for stock, data in engine.data.items():
            assert isinstance(data, pd.DataFrame)
            assert 'close' in data.columns


class TestPortfolio:
    """投资组合单元测试"""
    
    @pytest.mark.unit
    def test_portfolio_initialization(self):
        """测试投资组合初始化"""
        portfolio = Portfolio(1000000)
        
        assert portfolio.cash == 1000000
        assert portfolio.total_value == 1000000
        assert len(portfolio.positions) == 0
    
    @pytest.mark.unit
    def test_portfolio_position_management(self):
        """测试持仓管理"""
        portfolio = Portfolio(1000000)
        
        # 直接操作positions字典（实际的Portfolio类没有update_position方法）
        from simtradelab.context import Position
        portfolio.positions['STOCK_A'] = Position('STOCK_A', 100, 10.0)
        assert 'STOCK_A' in portfolio.positions
        assert portfolio.positions['STOCK_A'].amount == 100
        assert portfolio.positions['STOCK_A'].cost_basis == 10.0

        # 测试获取持仓
        position = portfolio.positions.get('STOCK_A')
        assert position is not None
        assert position.amount == 100

        # 测试移除持仓
        del portfolio.positions['STOCK_A']
        assert 'STOCK_A' not in portfolio.positions
    
    @pytest.mark.unit
    def test_portfolio_value_calculation(self):
        """测试投资组合价值计算"""
        portfolio = Portfolio(1000000)
        from simtradelab.context import Position

        # 模拟购买股票后的状态
        purchase_cost = 100 * 10.0 + 200 * 5.0  # 2000
        portfolio.cash -= purchase_cost  # 扣除购买成本
        portfolio.positions['STOCK_A'] = Position('STOCK_A', 100, 10.0)
        portfolio.positions['STOCK_B'] = Position('STOCK_B', 200, 5.0)

        # 模拟当前价格
        current_prices = {
            'STOCK_A': {'close': 12.0},
            'STOCK_B': {'close': 6.0}
        }

        total_value = portfolio.calculate_total_value(current_prices)

        # 现金 + 持仓市值
        expected_cash = 1000000 - purchase_cost  # 998000
        expected_positions_value = 100 * 12.0 + 200 * 6.0  # 2400
        expected_value = expected_cash + expected_positions_value  # 1000400
        assert abs(total_value - expected_value) < 0.01


class TestPosition:
    """持仓单元测试"""
    
    @pytest.mark.unit
    def test_position_creation(self):
        """测试持仓创建"""
        position = Position('STOCK_A', 100, 10.0)
        
        assert position.security == 'STOCK_A'
        assert position.amount == 100
        assert position.cost_basis == 10.0
        assert position.last_sale_price == 10.0
    
    @pytest.mark.unit
    def test_position_with_current_price(self):
        """测试带当前价格的持仓"""
        position = Position('STOCK_A', 100, 10.0, 12.0)
        
        assert position.last_sale_price == 12.0
        assert position.market_value == 1200.0  # 100 * 12.0
        assert position.pnl == 200.0  # (12.0 - 10.0) * 100
        assert abs(position.pnl_percent - 0.2) < 0.001  # 20%
    
    @pytest.mark.unit
    def test_position_properties(self):
        """测试持仓属性计算"""
        position = Position('STOCK_A', 100, 10.0, 8.0)
        
        # 测试亏损情况
        assert position.market_value == 800.0
        assert position.pnl == -200.0
        assert abs(position.pnl_percent - (-0.2)) < 0.001  # -20%


# Order, Trade, Blotter类在实际代码中可能不存在或结构不同
# 这些测试暂时跳过，等确认实际的类结构后再添加


class TestDataSources:
    """数据源单元测试"""
    
    @pytest.mark.unit
    def test_csv_data_source(self, sample_data_file):
        """测试CSV数据源"""
        csv_source = CSVDataSource(sample_data_file)
        
        # 测试获取股票列表
        stocks = csv_source.get_stock_list()
        assert isinstance(stocks, list)
        assert len(stocks) > 0
        
        # 测试获取历史数据
        history = csv_source.get_history(stocks[:2], '2023-01-01', '2023-01-05')
        assert isinstance(history, dict)
        
        # 测试获取当前数据
        current = csv_source.get_current_data(stocks[:2])
        assert isinstance(current, dict)
    
    @pytest.mark.unit
    def test_akshare_data_source(self):
        """测试AkShare数据源"""
        try:
            akshare_source = AkshareDataSource()

            # 测试代码转换
            assert akshare_source._convert_security_code('000001.SZ') == '000001'
            assert akshare_source._convert_security_code('600000.SH') == '600000'
            assert akshare_source._convert_security_code('000001') == '000001'
        except ImportError:
            pytest.skip("AkShare未安装，跳过测试")
    
    @pytest.mark.unit
    def test_data_source_manager(self, sample_data_file):
        """测试数据源管理器"""
        csv_source = CSVDataSource(sample_data_file)
        manager = DataSourceManager(csv_source)
        
        stocks = csv_source.get_stock_list()
        
        # 测试通过管理器获取数据
        history = manager.get_history(stocks[:1], '2023-01-01', '2023-01-02')
        assert isinstance(history, dict)
        
        current = manager.get_current_data(stocks[:1])
        assert isinstance(current, dict)


class TestContext:
    """上下文单元测试"""

    @pytest.mark.unit
    def test_context_creation(self):
        """测试上下文创建"""
        portfolio = Portfolio(1000000)
        context = Context(portfolio)

        assert context.portfolio == portfolio
        # Context类的实际结构可能不同，只测试基本功能

    @pytest.mark.unit
    def test_context_attributes(self):
        """测试上下文属性设置"""
        portfolio = Portfolio(1000000)
        context = Context(portfolio)

        # 测试动态属性设置
        context.my_variable = "test_value"
        assert context.my_variable == "test_value"

        context.stock_list = ['STOCK_A', 'STOCK_B']
        assert len(context.stock_list) == 2
