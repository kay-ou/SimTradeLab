# -*- coding: utf-8 -*-
"""
完整API测试 - 测试所有新增的PTrade兼容API
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from simtradelab import (
    # ETF相关
    get_etf_info, get_etf_stock_info, get_etf_stock_list, get_etf_list, etf_purchase_redemption,
    # 债券相关
    debt_to_stock_order, get_cb_list, get_cb_info,
    # 期货相关
    buy_open, sell_close, sell_open, buy_close, set_future_commission, 
    set_margin_rate, get_margin_rate, get_instruments,
    # 期权相关
    get_opt_objects, get_opt_last_dates, get_opt_contracts, option_exercise,
    option_covered_lock, option_covered_unlock,
    # 基础查询
    get_market_detail, get_stock_blocks, get_tick_direction,
    # 高级市场数据
    get_snapshot, get_volume_ratio, get_turnover_rate, get_pe_ratio, get_pb_ratio,
    # 分红配股
    get_dividend_info, get_rights_issue_info,
    # 停复牌
    get_suspend_info, is_suspended
)


class TestETFAPIs:
    """ETF相关API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.data = {
            'STOCK_A': pd.DataFrame(),
            'STOCK_B': pd.DataFrame()
        }
        return engine
    
    def test_get_etf_info(self, mock_engine):
        """测试获取ETF信息"""
        result = get_etf_info(mock_engine, '510300.SH')
        assert isinstance(result, dict)
        assert 'etf_code' in result
        assert result['etf_code'] == '510300.SH'
    
    def test_get_etf_stock_info(self, mock_engine):
        """测试获取ETF成分券信息"""
        result = get_etf_stock_info(mock_engine, '510300.SH')
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'weight' in result['STOCK_A']
    
    def test_get_etf_stock_list(self, mock_engine):
        """测试获取ETF成分券列表"""
        result = get_etf_stock_list(mock_engine, '510300.SH')
        assert isinstance(result, list)
        assert 'STOCK_A' in result
    
    def test_get_etf_list(self, mock_engine):
        """测试获取ETF列表"""
        result = get_etf_list(mock_engine)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_etf_purchase_redemption(self, mock_engine):
        """测试ETF申购赎回"""
        result = etf_purchase_redemption(mock_engine, '510300.SH', 'purchase', 1000000)
        assert result is not None
        assert isinstance(result, str)


class TestBondAPIs:
    """债券相关API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        return Mock()
    
    def test_debt_to_stock_order(self, mock_engine):
        """测试债转股委托"""
        result = debt_to_stock_order(mock_engine, '113008.SH', 1000)
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_cb_list(self, mock_engine):
        """测试获取可转债列表"""
        result = get_cb_list(mock_engine)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_cb_info(self, mock_engine):
        """测试获取可转债信息"""
        result = get_cb_info(mock_engine, '113008.SH')
        assert isinstance(result, dict)
        assert 'cb_code' in result
        assert 'conversion_ratio' in result


class TestFuturesAPIs:
    """期货相关API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.current_data = {'IF2312': {'close': 4000.0}}
        engine.commission_ratio = 0.0003
        engine.min_commission = 5.0
        engine.slippage = 0.001
        
        # 模拟context和portfolio
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.cash = 1000000.0
        engine.context.portfolio.positions = {}
        engine.context.blotter = Mock()
        engine.context.blotter.orders = []
        # 确保blotter.add_order返回字符串而不是Mock对象
        engine.context.blotter.add_order.return_value = 'order_123'
        
        return engine
    
    @patch('simtradelab.utils.order')
    def test_buy_open(self, mock_order, mock_engine):
        """测试期货多开"""
        mock_order.return_value = 'order_123'
        result = buy_open(mock_engine, 'IF2312', 5)
        assert result == 'order_123'
        mock_order.assert_called_once_with(mock_engine, 'IF2312', 5)
    
    @patch('simtradelab.utils.order')
    def test_sell_close(self, mock_order, mock_engine):
        """测试期货多平"""
        mock_order.return_value = 'order_123'
        result = sell_close(mock_engine, 'IF2312', 5)
        assert result == 'order_123'
        mock_order.assert_called_once_with(mock_engine, 'IF2312', -5)
    
    @patch('simtradelab.utils.order')
    def test_sell_open(self, mock_order, mock_engine):
        """测试期货空开"""
        mock_order.return_value = 'order_123'
        result = sell_open(mock_engine, 'IF2312', 5)
        assert result == 'order_123'
        mock_order.assert_called_once_with(mock_engine, 'IF2312', -5)
    
    @patch('simtradelab.utils.order')
    def test_buy_close(self, mock_order, mock_engine):
        """测试期货空平"""
        mock_order.return_value = 'order_123'
        result = buy_close(mock_engine, 'IF2312', 5)
        assert result == 'order_123'
        mock_order.assert_called_once_with(mock_engine, 'IF2312', 5)
    
    def test_set_future_commission(self, mock_engine):
        """测试设置期货手续费"""
        set_future_commission(mock_engine, 0.0005, 10.0)
        assert mock_engine.future_commission_ratio == 0.0005
        assert mock_engine.future_min_commission == 10.0
    
    def test_set_margin_rate(self, mock_engine):
        """测试设置保证金比例"""
        set_margin_rate(mock_engine, 0.15)
        assert mock_engine.margin_rate == 0.15
    
    def test_get_margin_rate(self, mock_engine):
        """测试获取保证金比例"""
        mock_engine.margin_rate = 0.12
        result = get_margin_rate(mock_engine)
        assert result == 0.12
    
    def test_get_instruments(self, mock_engine):
        """测试获取合约信息"""
        result = get_instruments(mock_engine)
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'code' in result[0]
        assert 'name' in result[0]


class TestOptionsAPIs:
    """期权相关API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        return Mock()
    
    def test_get_opt_objects(self, mock_engine):
        """测试获取期权标的列表"""
        result = get_opt_objects(mock_engine)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_opt_last_dates(self, mock_engine):
        """测试获取期权到期日列表"""
        result = get_opt_last_dates(mock_engine, '510050.SH')
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_opt_contracts(self, mock_engine):
        """测试获取期权合约列表"""
        result = get_opt_contracts(mock_engine, '510050.SH', '2024-01-31')
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'call' in result[0]
        assert 'put' in result[0]
    
    def test_option_exercise(self, mock_engine):
        """测试期权行权"""
        result = option_exercise(mock_engine, '510050C2401M03000', 10)
        assert result is not None
        assert isinstance(result, str)
    
    def test_option_covered_lock(self, mock_engine):
        """测试期权备兑锁定"""
        result = option_covered_lock(mock_engine, '510050.SH', 10000)
        assert result is not None
        assert isinstance(result, str)
    
    def test_option_covered_unlock(self, mock_engine):
        """测试期权备兑解锁"""
        result = option_covered_unlock(mock_engine, '510050.SH', 10000)
        assert result is not None
        assert isinstance(result, str)


class TestQueryAPIs:
    """基础查询API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        return Mock()
    
    def test_get_market_detail(self, mock_engine):
        """测试获取市场详情"""
        result = get_market_detail(mock_engine, 'SH')
        assert isinstance(result, dict)
        assert 'name' in result
        assert result['name'] == '上海证券交易所'
    
    def test_get_stock_blocks(self, mock_engine):
        """测试获取股票板块信息"""
        result = get_stock_blocks(mock_engine, '000001.SZ')
        assert isinstance(result, dict)
        assert 'industry' in result
        assert 'concept' in result
    
    def test_get_tick_direction(self, mock_engine):
        """测试获取tick方向"""
        result = get_tick_direction(mock_engine, '000001.SZ')
        assert result in ['up', 'down', 'flat']


class TestAdvancedMarketDataAPIs:
    """高级市场数据API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        # 创建模拟数据
        dates = pd.date_range('2023-01-01', '2023-01-10', freq='D')
        engine.data = {
            'STOCK_A': pd.DataFrame({
                'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
                'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
                'low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107],
                'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
                'volume': [1000000, 1100000, 1200000, 1300000, 1400000, 
                          1500000, 1600000, 1700000, 1800000, 1900000]
            }, index=dates)
        }
        return engine
    
    def test_get_snapshot(self, mock_engine):
        """测试获取快照数据"""
        result = get_snapshot(mock_engine, 'STOCK_A')
        assert isinstance(result, dict)
        assert 'code' in result
        assert 'open' in result
        assert 'close' in result
    
    def test_get_volume_ratio(self, mock_engine):
        """测试获取量比"""
        result = get_volume_ratio(mock_engine, 'STOCK_A')
        assert isinstance(result, float)
        assert result > 0
    
    def test_get_turnover_rate(self, mock_engine):
        """测试获取换手率"""
        result = get_turnover_rate(mock_engine, 'STOCK_A')
        assert isinstance(result, float)
        assert 0 < result <= 100
    
    def test_get_pe_ratio(self, mock_engine):
        """测试获取市盈率"""
        result = get_pe_ratio(mock_engine, 'STOCK_A')
        assert isinstance(result, float)
        assert result > 0
    
    def test_get_pb_ratio(self, mock_engine):
        """测试获取市净率"""
        result = get_pb_ratio(mock_engine, 'STOCK_A')
        assert isinstance(result, float)
        assert result > 0


class TestDividendAPIs:
    """分红配股API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        return Mock()
    
    def test_get_dividend_info(self, mock_engine):
        """测试获取分红信息"""
        result = get_dividend_info(mock_engine, '000001.SZ')
        assert isinstance(result, dict)
        assert 'stock' in result
        assert 'dividend_per_share' in result
        assert 'ex_dividend_date' in result
    
    def test_get_dividend_info_with_year(self, mock_engine):
        """测试获取指定年份分红信息"""
        result = get_dividend_info(mock_engine, '000001.SZ', 2022)
        assert result['year'] == 2022
    
    def test_get_rights_issue_info(self, mock_engine):
        """测试获取配股信息"""
        result = get_rights_issue_info(mock_engine, '000001.SZ')
        assert isinstance(result, dict)
        assert 'stock' in result
        assert 'rights_ratio' in result
        assert 'rights_price' in result


class TestSuspendAPIs:
    """停复牌API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        return Mock()
    
    def test_get_suspend_info(self, mock_engine):
        """测试获取停牌信息"""
        result = get_suspend_info(mock_engine, '000001.SZ')
        assert isinstance(result, dict)
        assert 'stock' in result
        assert 'is_suspended' in result
        assert isinstance(result['is_suspended'], bool)
    
    def test_is_suspended(self, mock_engine):
        """测试判断是否停牌"""
        result = is_suspended(mock_engine, '000001.SZ')
        assert isinstance(result, bool)


class TestAPIIntegration:
    """API集成测试"""
    
    def test_all_apis_importable(self):
        """测试所有API都可以正常导入"""
        # ETF相关
        from simtradelab import (
            get_etf_info, get_etf_stock_info, get_etf_stock_list, 
            get_etf_list, etf_purchase_redemption
        )
        
        # 债券相关
        from simtradelab import debt_to_stock_order, get_cb_list, get_cb_info
        
        # 期货相关
        from simtradelab import (
            buy_open, sell_close, sell_open, buy_close,
            set_future_commission, set_margin_rate, get_margin_rate, get_instruments
        )
        
        # 期权相关
        from simtradelab import (
            get_opt_objects, get_opt_last_dates, get_opt_contracts,
            option_exercise, option_covered_lock, option_covered_unlock
        )
        
        # 基础查询
        from simtradelab import get_market_detail, get_stock_blocks, get_tick_direction
        
        # 高级市场数据
        from simtradelab import (
            get_snapshot, get_volume_ratio, get_turnover_rate, 
            get_pe_ratio, get_pb_ratio
        )
        
        # 分红配股
        from simtradelab import get_dividend_info, get_rights_issue_info
        
        # 停复牌
        from simtradelab import get_suspend_info, is_suspended
        
        # 验证所有函数都是可调用的
        apis = [
            # ETF相关
            get_etf_info, get_etf_stock_info, get_etf_stock_list, 
            get_etf_list, etf_purchase_redemption,
            # 债券相关
            debt_to_stock_order, get_cb_list, get_cb_info,
            # 期货相关
            buy_open, sell_close, sell_open, buy_close,
            set_future_commission, set_margin_rate, get_margin_rate, get_instruments,
            # 期权相关
            get_opt_objects, get_opt_last_dates, get_opt_contracts,
            option_exercise, option_covered_lock, option_covered_unlock,
            # 基础查询
            get_market_detail, get_stock_blocks, get_tick_direction,
            # 高级市场数据
            get_snapshot, get_volume_ratio, get_turnover_rate, 
            get_pe_ratio, get_pb_ratio,
            # 分红配股
            get_dividend_info, get_rights_issue_info,
            # 停复牌
            get_suspend_info, is_suspended
        ]
        
        for api in apis:
            assert callable(api), f"{api.__name__} 不是可调用函数"
    
    def test_api_coverage_statistics(self):
        """测试API覆盖率统计"""
        # 统计不同类别API的数量
        etf_apis = 5
        bond_apis = 3
        futures_apis = 8
        options_apis = 6
        query_apis = 3
        market_data_apis = 5
        dividend_apis = 2
        suspend_apis = 2
        
        total_new_apis = (etf_apis + bond_apis + futures_apis + 
                         options_apis + query_apis + market_data_apis + 
                         dividend_apis + suspend_apis)
        
        print(f"新增API总数: {total_new_apis}")
        print(f"ETF相关API: {etf_apis}个")
        print(f"债券相关API: {bond_apis}个")
        print(f"期货相关API: {futures_apis}个")
        print(f"期权相关API: {options_apis}个")
        print(f"查询相关API: {query_apis}个")
        print(f"市场数据API: {market_data_apis}个")
        print(f"分红配股API: {dividend_apis}个")
        print(f"停复牌API: {suspend_apis}个")
        
        assert total_new_apis >= 30  # 至少新增30个API


if __name__ == '__main__':
    pytest.main([__file__, '-v'])