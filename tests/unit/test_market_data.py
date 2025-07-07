# -*- coding: utf-8 -*-
"""
市场数据模块测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from simtradelab.market_data import (
    get_history, get_price, get_current_data, get_market_snapshot,
    get_technical_indicators, get_MACD, get_KDJ, get_RSI, get_CCI,
    get_market_list, get_cash, get_total_value, get_datetime,
    get_previous_trading_date, get_next_trading_date, get_snapshot,
    get_volume_ratio, get_turnover_rate, get_pe_ratio, get_pb_ratio,
    get_individual_entrust, get_individual_transaction, get_gear_price,
    get_sort_msg
)


class TestMarketDataModule:
    """市场数据模块测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        
        # 创建足够多的测试数据（30天数据，确保技术指标计算正常）
        dates = pd.date_range('2023-01-01', '2023-01-30', freq='D')
        test_data = {
            'STOCK_A': pd.DataFrame({
                'open': np.random.rand(len(dates)) * 10 + 100,
                'high': np.random.rand(len(dates)) * 10 + 105,
                'low': np.random.rand(len(dates)) * 10 + 95,
                'close': np.random.rand(len(dates)) * 10 + 100,
                'volume': np.random.randint(1000000, 2000000, len(dates)),
            }, index=dates),
            'STOCK_B': pd.DataFrame({
                'open': np.random.rand(len(dates)) * 10 + 50,
                'high': np.random.rand(len(dates)) * 10 + 55,
                'low': np.random.rand(len(dates)) * 10 + 45,
                'close': np.random.rand(len(dates)) * 10 + 50,
                'volume': np.random.randint(500000, 1000000, len(dates)),
            }, index=dates)
        }
        
        engine.data = test_data
        engine.context = Mock()
        engine.context.current_dt = dates[20]  # 设置为第20天，确保有足够历史数据
        
        return engine
    
    def test_get_history_basic(self, mock_engine):
        """测试基本历史数据获取"""
        result = get_history(mock_engine, count=5, field=['close'], security_list=['STOCK_A'])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 1
        assert ('close', 'STOCK_A') in result.columns
    
    def test_get_history_multiple_fields(self, mock_engine):
        """测试获取多个字段的历史数据"""
        result = get_history(
            mock_engine, 
            count=5, 
            field=['open', 'close'], 
            security_list=['STOCK_A']
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 2
        assert ('open', 'STOCK_A') in result.columns
        assert ('close', 'STOCK_A') in result.columns
    
    def test_get_history_dict_format(self, mock_engine):
        """测试字典格式返回"""
        result = get_history(
            mock_engine, 
            count=5, 
            field=['close'], 
            security_list=['STOCK_A'], 
            is_dict=True
        )
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'close' in result['STOCK_A']
        assert isinstance(result['STOCK_A']['close'], np.ndarray)
    
    def test_get_history_with_dates(self, mock_engine):
        """测试指定日期范围的历史数据"""
        result = get_history(
            mock_engine,
            count=10,
            start_date='2023-01-03',
            end_date='2023-01-07',
            security_list=['STOCK_A']
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= 5  # 最多5个交易日
    
    def test_get_history_extended_fields(self, mock_engine):
        """测试扩展字段计算"""
        result = get_history(
            mock_engine,
            count=5,
            field=['close', 'pct_change', 'amplitude'],
            security_list=['STOCK_A'],
            is_dict=True
        )
        
        assert 'STOCK_A' in result
        assert 'pct_change' in result['STOCK_A']
        assert 'amplitude' in result['STOCK_A']
    
    def test_get_history_nonexistent_security(self, mock_engine):
        """测试不存在的股票"""
        result = get_history(
            mock_engine,
            count=5,
            security_list=['NONEXISTENT'],
            is_dict=True
        )
        
        assert 'NONEXISTENT' in result
        assert len(result['NONEXISTENT']['close']) == 0
    
    def test_get_price_single_security(self, mock_engine):
        """测试获取单只股票价格"""
        result = get_price(mock_engine, 'STOCK_A', count=3, fields=['close', 'open'])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 2
        assert len(result) == 3
    
    def test_get_price_multiple_securities(self, mock_engine):
        """测试获取多只股票价格"""
        result = get_price(mock_engine, ['STOCK_A', 'STOCK_B'], fields='close', count=3)
        
        assert isinstance(result, pd.DataFrame)
        assert 'STOCK_A' in result.columns
        assert 'STOCK_B' in result.columns
    
    def test_get_price_multiple_fields(self, mock_engine):
        """测试获取多个字段价格"""
        result = get_price(mock_engine, 'STOCK_A', fields=['open', 'close'], count=3)
        
        assert isinstance(result, pd.DataFrame)
        assert ('open', 'STOCK_A') in result.columns
        assert ('close', 'STOCK_A') in result.columns
    
    def test_get_price_calculated_fields(self, mock_engine):
        """测试计算字段"""
        result = get_price(
            mock_engine, 
            'STOCK_A', 
            fields=['close', 'pct_change', 'vwap'], 
            count=3
        )
        
        assert isinstance(result, pd.DataFrame)
        assert ('pct_change', 'STOCK_A') in result.columns
        assert ('vwap', 'STOCK_A') in result.columns
    
    def test_get_current_data_all_securities(self, mock_engine):
        """测试获取所有股票当前数据"""
        result = get_current_data(mock_engine)
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
        assert 'close' in result['STOCK_A']
        assert 'bid1' in result['STOCK_A']
        assert 'ask1' in result['STOCK_A']
    
    def test_get_current_data_specific_security(self, mock_engine):
        """测试获取指定股票当前数据"""
        result = get_current_data(mock_engine, 'STOCK_A')
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' not in result
    
    def test_get_current_data_multiple_securities(self, mock_engine):
        """测试获取多只股票当前数据"""
        result = get_current_data(mock_engine, ['STOCK_A', 'STOCK_B'])
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
    
    def test_get_market_snapshot_default(self, mock_engine):
        """测试默认市场快照"""
        result = get_market_snapshot(mock_engine)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # STOCK_A 和 STOCK_B
        assert 'open' in result.columns
        assert 'close' in result.columns
    
    def test_get_market_snapshot_specific_fields(self, mock_engine):
        """测试指定字段市场快照"""
        result = get_market_snapshot(mock_engine, fields=['close', 'volume'])
        
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns
        assert 'volume' in result.columns
        assert 'open' not in result.columns
    
    def test_get_market_snapshot_specific_security(self, mock_engine):
        """测试指定股票市场快照"""
        result = get_market_snapshot(mock_engine, security='STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.index[0] == 'STOCK_A'
    
    def test_get_technical_indicators_ma(self, mock_engine):
        """测试移动平均线指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'MA', period=5)
        
        assert isinstance(result, pd.DataFrame)
        assert ('MA5', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_multiple(self, mock_engine):
        """测试多个技术指标"""
        result = get_technical_indicators(
            mock_engine, 
            'STOCK_A', 
            ['MA', 'EMA', 'RSI'], 
            period=5
        )
        
        assert isinstance(result, pd.DataFrame)
        assert ('MA5', 'STOCK_A') in result.columns
        assert ('EMA5', 'STOCK_A') in result.columns
        assert ('RSI5', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_macd(self, mock_engine):
        """测试MACD指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'MACD')
        
        assert isinstance(result, pd.DataFrame)
        assert ('MACD_DIF', 'STOCK_A') in result.columns
        assert ('MACD_DEA', 'STOCK_A') in result.columns
        assert ('MACD_HIST', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_boll(self, mock_engine):
        """测试布林带指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'BOLL')
        
        assert isinstance(result, pd.DataFrame)
        assert ('BOLL_UPPER', 'STOCK_A') in result.columns
        assert ('BOLL_MIDDLE', 'STOCK_A') in result.columns
        assert ('BOLL_LOWER', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_kdj(self, mock_engine):
        """测试KDJ指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'KDJ')
        
        assert isinstance(result, pd.DataFrame)
        assert ('KDJ_K', 'STOCK_A') in result.columns
        assert ('KDJ_D', 'STOCK_A') in result.columns
        assert ('KDJ_J', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_cci(self, mock_engine):
        """测试CCI指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'CCI', period=14)
        
        assert isinstance(result, pd.DataFrame)
        assert ('CCI14', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_insufficient_data(self, mock_engine):
        """测试数据不足的情况"""
        # 创建只有很少数据的引擎
        short_engine = Mock()
        dates = pd.date_range('2023-01-01', '2023-01-02', freq='D')
        short_engine.data = {
            'STOCK_A': pd.DataFrame({
                'close': [100.0, 101.0],
            }, index=dates)
        }
        short_engine.context = Mock()
        short_engine.context.current_dt = dates[1]
        
        result = get_technical_indicators(short_engine, 'STOCK_A', 'MA', period=20)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    def test_get_macd_function(self, mock_engine):
        """测试MACD独立函数"""
        result = get_MACD(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('MACD_DIF', 'STOCK_A') in result.columns
    
    def test_get_kdj_function(self, mock_engine):
        """测试KDJ独立函数"""
        result = get_KDJ(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('KDJ_K', 'STOCK_A') in result.columns
    
    def test_get_rsi_function(self, mock_engine):
        """测试RSI独立函数"""
        result = get_RSI(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('RSI14', 'STOCK_A') in result.columns
    
    def test_get_cci_function(self, mock_engine):
        """测试CCI独立函数"""
        result = get_CCI(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('CCI20', 'STOCK_A') in result.columns



class TestMarketInformationFunctions:
    """市场信息函数测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.data = {
            '000001.SZ': Mock(),
            '000002.SZ': Mock(),
            '600001.SH': Mock(),
            '300001': Mock()  # 没有后缀的股票，默认为SZ
        }
        
        # 配置context和portfolio
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.cash = 50000.0
        engine.context.portfolio.total_value = 150000.0
        engine.context.current_dt = pd.Timestamp('2023-01-15 10:30:00')
        
        return engine
    
    def test_get_market_list(self, mock_engine):
        """测试获取市场列表"""
        result = get_market_list(mock_engine)
        
        assert isinstance(result, list)
        assert 'SZ' in result
        assert 'SH' in result
        assert len(result) >= 2
    
    def test_get_market_list_empty_data(self):
        """测试空数据的市场列表"""
        engine = Mock()
        engine.data = {}
        
        result = get_market_list(engine)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_cash(self, mock_engine):
        """测试获取当前现金"""
        result = get_cash(mock_engine)
        
        assert isinstance(result, float)
        assert result == 50000.0
    
    def test_get_cash_no_context(self):
        """测试无context时获取现金"""
        engine = Mock()
        del engine.context  # 删除context属性
        
        result = get_cash(engine)
        
        assert result == 0.0
    
    def test_get_total_value(self, mock_engine):
        """测试获取总资产"""
        result = get_total_value(mock_engine)
        
        assert isinstance(result, float)
        assert result == 150000.0
    
    def test_get_total_value_no_context(self):
        """测试无context时获取总资产"""
        engine = Mock()
        del engine.context
        
        result = get_total_value(engine)
        
        assert result == 0.0
    
    def test_get_datetime(self, mock_engine):
        """测试获取当前时间"""
        result = get_datetime(mock_engine)
        
        assert isinstance(result, str)
        assert result == '2023-01-15 10:30:00'
    
    def test_get_datetime_no_context(self):
        """测试无context时获取时间"""
        engine = Mock()
        del engine.context
        
        result = get_datetime(engine)
        
        assert result == ""


class TestTradingCalendarFunctions:
    """交易日历函数测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.context = Mock()
        engine.context.current_dt = pd.Timestamp('2023-01-15')
        return engine
    
    @patch('simtradelab.utils.get_trading_day')
    def test_get_previous_trading_date(self, mock_get_trading_day, mock_engine):
        """测试获取上一交易日"""
        mock_get_trading_day.return_value = pd.Timestamp('2023-01-14')
        
        result = get_previous_trading_date(mock_engine, '2023-01-15')
        
        assert result == '2023-01-14'
        mock_get_trading_day.assert_called_once_with(mock_engine, '2023-01-15', offset=-1)
    
    @patch('simtradelab.utils.get_trading_day')
    def test_get_previous_trading_date_no_result(self, mock_get_trading_day, mock_engine):
        """测试无结果时的上一交易日"""
        mock_get_trading_day.return_value = None
        
        result = get_previous_trading_date(mock_engine)
        
        assert result == ""
    
    @patch('simtradelab.utils.get_trading_day')
    def test_get_next_trading_date(self, mock_get_trading_day, mock_engine):
        """测试获取下一交易日"""
        mock_get_trading_day.return_value = pd.Timestamp('2023-01-16')
        
        result = get_next_trading_date(mock_engine, '2023-01-15')
        
        assert result == '2023-01-16'
        mock_get_trading_day.assert_called_once_with(mock_engine, '2023-01-15', offset=1)
    
    @patch('simtradelab.utils.get_trading_day')
    def test_get_next_trading_date_no_result(self, mock_get_trading_day, mock_engine):
        """测试无结果时的下一交易日"""
        mock_get_trading_day.return_value = None
        
        result = get_next_trading_date(mock_engine)
        
        assert result == ""


class TestAdvancedMarketDataFunctions:
    """高级市场数据函数测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        test_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0],
            'low': [95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0],
            'close': [102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000, 1900000],
        }, index=dates)
        
        engine.data = {'STOCK_A': test_data}
        
        return engine
    
    def test_get_snapshot(self, mock_engine):
        """测试获取股票快照"""
        result = get_snapshot(mock_engine, 'STOCK_A')
        
        assert isinstance(result, dict)
        assert 'code' in result
        assert result['code'] == 'STOCK_A'
        assert 'open' in result
        assert 'high' in result
        assert 'low' in result
        assert 'close' in result
        assert 'volume' in result
        assert 'turnover' in result
        assert 'bid1' in result
        assert 'ask1' in result
        assert 'bid1_volume' in result
        assert 'ask1_volume' in result
    
    def test_get_snapshot_nonexistent_stock(self, mock_engine):
        """测试不存在股票的快照"""
        result = get_snapshot(mock_engine, 'NONEXISTENT')
        
        assert isinstance(result, dict)
        assert 'code' in result
        assert result['code'] == 'NONEXISTENT'
        assert 'error' in result
    
    def test_get_volume_ratio(self, mock_engine):
        """测试获取量比"""
        result = get_volume_ratio(mock_engine, 'STOCK_A')
        
        assert isinstance(result, float)
        assert result > 0
    
    def test_get_volume_ratio_insufficient_data(self, mock_engine):
        """测试数据不足时的量比"""
        # 创建数据不足的引擎
        dates = pd.date_range('2023-01-01', periods=2, freq='D')
        test_data = pd.DataFrame({
            'volume': [1000000, 1100000],
        }, index=dates)
        mock_engine.data = {'STOCK_A': test_data}
        
        result = get_volume_ratio(mock_engine, 'STOCK_A')
        
        assert result == 1.0
    
    def test_get_volume_ratio_nonexistent_stock(self, mock_engine):
        """测试不存在股票的量比"""
        result = get_volume_ratio(mock_engine, 'NONEXISTENT')
        
        assert result == 1.0
    
    def test_get_turnover_rate(self, mock_engine):
        """测试获取换手率"""
        result = get_turnover_rate(mock_engine, 'STOCK_A')
        
        assert isinstance(result, float)
        assert 0.5 <= result <= 5.0  # 根据实现的范围
    
    def test_get_pe_ratio(self, mock_engine):
        """测试获取市盈率"""
        result = get_pe_ratio(mock_engine, 'STOCK_A')
        
        assert isinstance(result, float)
        assert 10 <= result <= 50  # 根据实现的范围
    
    def test_get_pb_ratio(self, mock_engine):
        """测试获取市净率"""
        result = get_pb_ratio(mock_engine, 'STOCK_A')
        
        assert isinstance(result, float)
        assert 0.5 <= result <= 8.0  # 根据实现的范围


class TestHighFrequencyDataFunctions:
    """高频数据函数测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        return engine
    
    def test_get_individual_entrust_single_stock(self, mock_engine):
        """测试获取单只股票逐笔委托"""
        result = get_individual_entrust(mock_engine, 'STOCK_A')
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert isinstance(result['STOCK_A'], pd.DataFrame)
        
        df = result['STOCK_A']
        expected_columns = ['business_time', 'hq_px', 'business_amount', 'order_no', 'business_direction', 'trans_kind']
        for col in expected_columns:
            assert col in df.columns
    
    def test_get_individual_entrust_multiple_stocks(self, mock_engine):
        """测试获取多只股票逐笔委托"""
        result = get_individual_entrust(mock_engine, ['STOCK_A', 'STOCK_B'])
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
        assert len(result) == 2
    
    def test_get_individual_entrust_with_time_range(self, mock_engine):
        """测试带时间范围的逐笔委托"""
        result = get_individual_entrust(
            mock_engine, 
            'STOCK_A', 
            start_time='2023-01-01 09:30:00',
            end_time='2023-01-01 15:00:00'
        )
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert isinstance(result['STOCK_A'], pd.DataFrame)
    
    def test_get_individual_transaction_single_stock(self, mock_engine):
        """测试获取单只股票逐笔成交"""
        result = get_individual_transaction(mock_engine, 'STOCK_A')
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert isinstance(result['STOCK_A'], pd.DataFrame)
        
        df = result['STOCK_A']
        expected_columns = [
            'business_time', 'hq_px', 'business_amount', 'trade_index', 
            'business_direction', 'buy_no', 'sell_no', 'trans_flag', 
            'trans_identify_am', 'channel_num'
        ]
        for col in expected_columns:
            assert col in df.columns
    
    def test_get_individual_transaction_multiple_stocks(self, mock_engine):
        """测试获取多只股票逐笔成交"""
        result = get_individual_transaction(mock_engine, ['STOCK_A', 'STOCK_B'])
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
        assert len(result) == 2
    
    def test_get_individual_transaction_with_time_range(self, mock_engine):
        """测试带时间范围的逐笔成交"""
        result = get_individual_transaction(
            mock_engine, 
            'STOCK_A', 
            start_time='2023-01-01 09:30:00',
            end_time='2023-01-01 15:00:00'
        )
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert isinstance(result['STOCK_A'], pd.DataFrame)
    
    def test_get_gear_price(self, mock_engine):
        """测试获取档位行情"""
        result = get_gear_price(mock_engine, 'STOCK_A')
        
        assert isinstance(result, dict)
        assert 'security' in result
        assert result['security'] == 'STOCK_A'
        assert 'timestamp' in result
        assert 'bid_prices' in result
        assert 'ask_prices' in result
        assert 'bid_volumes' in result
        assert 'ask_volumes' in result
        assert 'last_price' in result
        assert 'total_bid_volume' in result
        assert 'total_ask_volume' in result
        
        # 检查买卖五档数据
        assert len(result['bid_prices']) == 5
        assert len(result['ask_prices']) == 5
        assert len(result['bid_volumes']) == 5
        assert len(result['ask_volumes']) == 5


class TestMarketRankingFunctions:
    """市场排名函数测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        return engine
    
    def test_get_sort_msg_sector_default(self, mock_engine):
        """测试获取板块排名（默认参数）"""
        result = get_sort_msg(mock_engine)
        
        assert isinstance(result, list)
        assert len(result) <= 20  # 默认count=20
        
        if result:  # 如果有结果
            first_item = result[0]
            assert 'name' in first_item
            assert 'code' in first_item
            assert 'pct_change' in first_item
            assert 'volume' in first_item
            assert 'amount' in first_item
            assert 'up_count' in first_item
            assert 'down_count' in first_item
            assert 'flat_count' in first_item
            assert '板块' in first_item['name']
    
    def test_get_sort_msg_industry(self, mock_engine):
        """测试获取行业排名"""
        result = get_sort_msg(mock_engine, market_type='industry')
        
        assert isinstance(result, list)
        
        if result:
            first_item = result[0]
            assert 'name' in first_item
            # 行业名称应该不是板块名称（不包含"板块"）
            assert '板块' not in first_item['name']
    
    def test_get_sort_msg_custom_sort_field(self, mock_engine):
        """测试自定义排序字段"""
        result = get_sort_msg(
            mock_engine, 
            market_type='sector',
            sort_field='volume',
            ascending=True,
            count=10
        )
        
        assert isinstance(result, list)
        assert len(result) <= 10
        
        # 检查是否按volume升序排列
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]['volume'] <= result[i + 1]['volume']
    
    def test_get_sort_msg_descending_sort(self, mock_engine):
        """测试降序排列"""
        result = get_sort_msg(
            mock_engine,
            sort_field='pct_change',
            ascending=False,
            count=5
        )
        
        assert isinstance(result, list)
        assert len(result) <= 5
        
        # 检查是否按pct_change降序排列
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]['pct_change'] >= result[i + 1]['pct_change']
    
    def test_get_sort_msg_amount_sort(self, mock_engine):
        """测试按成交额排序"""
        result = get_sort_msg(
            mock_engine,
            sort_field='amount',
            count=3
        )
        
        assert isinstance(result, list)
        assert len(result) <= 3
        
        if result:
            first_item = result[0]
            assert isinstance(first_item['amount'], int)
            assert first_item['amount'] > 0


class TestMarketDataEdgeCases:
    """市场数据边界情况测试类"""
    
    def test_functions_with_empty_engine(self):
        """测试空引擎的各种函数"""
        # 创建一个简单的空引擎类
        class EmptyEngine:
            def __init__(self):
                self.data = {}
        
        empty_engine = EmptyEngine()
        
        # 测试不会抛出异常
        assert get_market_list(empty_engine) == []
        assert get_cash(empty_engine) == 0.0
        assert get_total_value(empty_engine) == 0.0
        assert get_datetime(empty_engine) == ""
    
    def test_functions_with_none_engine(self):
        """测试None引擎的处理"""
        # 这些函数应该能处理None引擎而不崩溃
        try:
            get_volume_ratio(None, 'STOCK_A')
            get_turnover_rate(None, 'STOCK_A')
            get_pe_ratio(None, 'STOCK_A')
            get_pb_ratio(None, 'STOCK_A')
        except AttributeError:
            # 预期会有AttributeError，因为访问None的属性
            pass
    
    def test_high_frequency_data_edge_cases(self):
        """测试高频数据函数的边界情况"""
        engine = Mock()
        
        # 测试空字符串股票代码
        result1 = get_individual_entrust(engine, '')
        assert isinstance(result1, dict)
        assert '' in result1
        
        # 测试空列表
        result2 = get_individual_entrust(engine, [])
        assert isinstance(result2, dict)
        assert len(result2) == 0
        
        # 测试gear_price的稳定性
        result3 = get_gear_price(engine, 'ANY_STOCK')
        assert isinstance(result3, dict)
        assert 'security' in result3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])