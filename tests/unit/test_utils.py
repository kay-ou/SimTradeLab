#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils模块测试
"""

import pytest
import pandas as pd
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from simtradelab import utils
from simtradelab.context import Position


class TestUtils:
    """Utils模块测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.name = "test_engine"
        engine.data = {
            'STOCK_A': pd.DataFrame({
                'open': [10.0, 10.1, 10.2],
                'high': [10.5, 10.6, 10.7],
                'low': [9.5, 9.6, 9.7],
                'close': [10.2, 10.3, 10.4],
                'volume': [100000, 110000, 120000]
            }, index=pd.date_range('2023-01-01', periods=3))
        }
        
        # 创建模拟上下文
        context = Mock()
        context.current_dt = pd.Timestamp('2023-01-02')
        context.portfolio = Mock()
        context.portfolio.starting_cash = 1000000.0
        context.portfolio.positions = {}
        engine.context = context
        
        return engine
    
    # ==================== 基础函数测试 ====================
    
    @pytest.mark.unit
    def test_is_trade(self, mock_engine):
        """测试is_trade函数"""
        result = utils.is_trade(mock_engine)
        assert result is False
    
    @pytest.mark.unit
    def test_get_research_path(self, mock_engine):
        """测试get_research_path函数"""
        result = utils.get_research_path(mock_engine)
        assert result == './'
    
    # ==================== 配置相关函数测试 ====================
    
    @pytest.mark.unit
    def test_set_commission(self, mock_engine):
        """测试设置交易手续费"""
        utils.set_commission(mock_engine, 0.001, 10.0, "STOCK")
        assert mock_engine.commission_ratio == 0.001
        assert mock_engine.min_commission == 10.0
    
    @pytest.mark.unit
    def test_set_limit_mode(self, mock_engine):
        """测试设置限价模式"""
        utils.set_limit_mode(mock_engine, True)
        assert mock_engine.limit_mode is True
        
        utils.set_limit_mode(mock_engine, False)
        assert mock_engine.limit_mode is False
    
    @pytest.mark.unit
    def test_set_fixed_slippage(self, mock_engine):
        """测试设置固定滑点"""
        utils.set_fixed_slippage(mock_engine, 0.01)
        assert mock_engine.fixed_slippage == 0.01
        
        # 测试字符串输入
        utils.set_fixed_slippage(mock_engine, "0.02")
        assert mock_engine.fixed_slippage == 0.02
    
    @pytest.mark.unit
    def test_set_slippage(self, mock_engine):
        """测试设置滑点比例"""
        utils.set_slippage(mock_engine, 0.001)
        assert mock_engine.slippage == 0.001
    
    @pytest.mark.unit
    def test_set_volume_ratio(self, mock_engine):
        """测试设置成交量比例"""
        utils.set_volume_ratio(mock_engine, 0.1)
        assert mock_engine.volume_ratio == 0.1
    
    @pytest.mark.unit
    def test_set_yesterday_position(self, mock_engine):
        """测试设置初始持仓"""
        positions = {'STOCK_A': 1000, 'STOCK_B': 2000}
        
        utils.set_yesterday_position(mock_engine, positions)
        
        # 验证持仓设置
        assert 'STOCK_A' in mock_engine.context.portfolio.positions
        assert 'STOCK_B' in mock_engine.context.portfolio.positions
    
    @pytest.mark.unit
    def test_set_yesterday_position_no_context(self, mock_engine):
        """测试无上下文时设置初始持仓"""
        mock_engine.context = None
        
        # 应该不会抛出异常，只是记录警告
        utils.set_yesterday_position(mock_engine, {'STOCK_A': 1000})
    
    @pytest.mark.unit
    def test_set_parameters(self, mock_engine):
        """测试设置策略参数"""
        params = {'param1': 'value1', 'param2': 42}

        # 确保mock_engine没有预设的strategy_params属性
        if hasattr(mock_engine, 'strategy_params'):
            delattr(mock_engine, 'strategy_params')

        utils.set_parameters(mock_engine, **params)

        assert hasattr(mock_engine, 'strategy_params')
        assert mock_engine.strategy_params == params
    
    # ==================== 定时任务测试 ====================
    
    @pytest.mark.unit
    def test_run_daily(self, mock_engine):
        """测试每日定时任务"""
        def test_func():
            return "daily_task"

        # 确保mock_engine没有预设的daily_tasks属性
        if hasattr(mock_engine, 'daily_tasks'):
            delattr(mock_engine, 'daily_tasks')

        utils.run_daily(mock_engine, mock_engine.context, test_func, '09:30')

        assert hasattr(mock_engine, 'daily_tasks')
        assert len(mock_engine.daily_tasks) == 1

        task = mock_engine.daily_tasks[0]
        assert task['func'] == test_func
        assert task['time'] == '09:30'
    
    @pytest.mark.unit
    def test_run_interval(self, mock_engine):
        """测试定时间隔任务"""
        def test_func():
            return "interval_task"

        # 确保mock_engine没有预设的interval_tasks属性
        if hasattr(mock_engine, 'interval_tasks'):
            delattr(mock_engine, 'interval_tasks')

        utils.run_interval(mock_engine, mock_engine.context, test_func, 60)

        assert hasattr(mock_engine, 'interval_tasks')
        assert len(mock_engine.interval_tasks) == 1

        task = mock_engine.interval_tasks[0]
        assert task['func'] == test_func
        assert task['seconds'] == 60
    
    # ==================== 文件操作测试 ====================
    
    @pytest.mark.unit
    def test_clear_file(self):
        """测试清除文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "subdir" / "test.txt"
            
            # 创建文件
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("test content")
            assert test_file.exists()
            
            # 清除文件
            utils.clear_file(None, str(test_file))
            assert not test_file.exists()
    
    @pytest.mark.unit
    def test_get_initial_cash(self, mock_engine):
        """测试获取初始资金"""
        result = utils.get_initial_cash(mock_engine, mock_engine.context, 500000)
        assert result == 500000  # min(1000000, 500000)
        
        result = utils.get_initial_cash(mock_engine, mock_engine.context, 1500000)
        assert result == 1000000  # min(1000000, 1500000)
    
    @pytest.mark.unit
    def test_get_num_of_positions(self, mock_engine):
        """测试获取持仓数量"""
        # 空持仓
        result = utils.get_num_of_positions(mock_engine, mock_engine.context)
        assert result == 0
        
        # 添加持仓
        mock_engine.context.portfolio.positions = {
            'STOCK_A': Mock(amount=1000),
            'STOCK_B': Mock(amount=0),  # 空持仓
            'STOCK_C': Mock(amount=500)
        }
        
        result = utils.get_num_of_positions(mock_engine, mock_engine.context)
        assert result == 2  # 只计算amount > 0的持仓
    
    @pytest.mark.unit
    def test_get_Ashares(self, mock_engine):
        """测试获取A股列表"""
        result = utils.get_Ashares(mock_engine)
        assert isinstance(result, list)
        assert 'STOCK_A' in result
    
    @pytest.mark.unit
    def test_get_stock_status(self, mock_engine):
        """测试获取股票状态"""
        # 测试单个股票
        result = utils.get_stock_status(mock_engine, 'STOCK_A', 'ST')
        assert isinstance(result, dict)
        assert result['STOCK_A'] is False
        
        # 测试多个股票
        result = utils.get_stock_status(mock_engine, ['STOCK_A', 'STOCK_B'], 'ST')
        assert len(result) == 2
        assert all(status is False for status in result.values())
    
    @pytest.mark.unit
    def test_get_stock_info(self, mock_engine):
        """测试获取股票信息"""
        # 测试默认字段
        result = utils.get_stock_info(mock_engine, 'STOCK_A')
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'stock_name' in result['STOCK_A']
        
        # 测试指定字段
        result = utils.get_stock_info(mock_engine, ['STOCK_A'], ['stock_name', 'listed_date'])
        assert 'stock_name' in result['STOCK_A']
        assert 'listed_date' in result['STOCK_A']
    
    @pytest.mark.unit
    def test_get_stock_name(self, mock_engine):
        """测试获取股票名称"""
        result = utils.get_stock_name(mock_engine, 'STOCK_A')
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert isinstance(result['STOCK_A'], str)
    
    @pytest.mark.unit
    def test_set_universe(self, mock_engine):
        """测试设置股票池"""
        # 测试字符串输入
        utils.set_universe(mock_engine, 'STOCK_A')
        
        # 测试列表输入
        utils.set_universe(mock_engine, ['STOCK_A', 'STOCK_B'])
    
    # ==================== 基准相关测试 ====================
    
    @pytest.mark.unit
    def test_set_benchmark(self, mock_engine):
        """测试设置基准指数"""
        utils.set_benchmark(mock_engine, '000001.SH')
        assert mock_engine.benchmark == '000001.SH'
        
        # 测试基准不在数据中的情况
        utils.set_benchmark(mock_engine, '000300.SH')
        assert mock_engine.benchmark == '000300.SH'
        assert '000300.SH' in mock_engine.data  # 应该生成模拟数据
    
    @pytest.mark.unit
    def test_get_benchmark_returns(self, mock_engine):
        """测试获取基准收益率"""
        # 先设置基准
        utils.set_benchmark(mock_engine, 'STOCK_A')
        
        result = utils.get_benchmark_returns(mock_engine)
        assert isinstance(result, pd.Series)
        assert len(result) > 0
        
        # 测试无基准的情况
        delattr(mock_engine, 'benchmark')
        result = utils.get_benchmark_returns(mock_engine)
        assert result is None
    
    # ==================== 交易日历测试 ====================
    
    @pytest.mark.unit
    def test_get_trading_day(self, mock_engine):
        """测试获取交易日"""
        result = utils.get_trading_day(mock_engine)
        assert result is not None
        
        # 测试偏移
        result = utils.get_trading_day(mock_engine, offset=1)
        assert result is not None
        
        # 测试指定日期
        result = utils.get_trading_day(mock_engine, date='2023-01-01', offset=0)
        assert result is not None
    
    @pytest.mark.unit
    def test_get_all_trades_days(self, mock_engine):
        """测试获取所有交易日"""
        result = utils.get_all_trades_days(mock_engine)
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) > 0
        
        # 测试无数据的情况
        mock_engine.data = {}
        result = utils.get_all_trades_days(mock_engine)
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) == 0
    
    @pytest.mark.unit
    def test_get_trade_days(self, mock_engine):
        """测试获取指定范围交易日"""
        # 测试数量限制
        result = utils.get_trade_days(mock_engine, count=2)
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) <= 2

        # 测试日期范围
        result = utils.get_trade_days(mock_engine,
                                    start_date='2023-01-01',
                                    end_date='2023-01-03')
        assert isinstance(result, pd.DatetimeIndex)

    # ==================== ETF相关测试 ====================

    @pytest.mark.unit
    def test_get_etf_info(self, mock_engine):
        """测试获取ETF信息"""
        result = utils.get_etf_info(mock_engine, '510300.SH')

        assert isinstance(result, dict)
        assert result['etf_code'] == '510300.SH'
        assert 'etf_name' in result
        assert 'tracking_index' in result
        assert 'management_fee' in result
        assert result['status'] == 'normal'

    @pytest.mark.unit
    def test_get_etf_stock_info(self, mock_engine):
        """测试获取ETF成分券信息"""
        result = utils.get_etf_stock_info(mock_engine, '510300.SH')

        assert isinstance(result, dict)
        if result:  # 如果有数据
            first_stock = list(result.keys())[0]
            stock_info = result[first_stock]
            assert 'weight' in stock_info
            assert 'shares' in stock_info
            assert 'market_value' in stock_info

    @pytest.mark.unit
    def test_get_etf_stock_list(self, mock_engine):
        """测试获取ETF成分券列表"""
        result = utils.get_etf_stock_list(mock_engine, '510300.SH')

        assert isinstance(result, list)
        # 应该与get_etf_stock_info返回的键一致
        stock_info = utils.get_etf_stock_info(mock_engine, '510300.SH')
        assert result == list(stock_info.keys())

    @pytest.mark.unit
    def test_get_etf_list(self, mock_engine):
        """测试获取ETF列表"""
        result = utils.get_etf_list(mock_engine)

        assert isinstance(result, list)
        assert len(result) > 0
        # 验证ETF代码格式
        for etf_code in result:
            assert '.' in etf_code
            assert etf_code.endswith('.SH') or etf_code.endswith('.SZ')

    @pytest.mark.unit
    def test_etf_purchase_redemption(self, mock_engine):
        """测试ETF申购赎回"""
        # 测试申购
        result = utils.etf_purchase_redemption(mock_engine, '510300.SH', 'purchase', 1000000)
        assert isinstance(result, str)
        assert len(result) > 0

        # 测试赎回
        result = utils.etf_purchase_redemption(mock_engine, '510300.SH', 'redemption', 1000000)
        assert isinstance(result, str)
        assert len(result) > 0

    # ==================== 债券相关测试 ====================

    @pytest.mark.unit
    def test_debt_to_stock_order(self, mock_engine):
        """测试债转股委托"""
        result = utils.debt_to_stock_order(mock_engine, '113008.SH', 100)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_get_cb_list(self, mock_engine):
        """测试获取可转债列表"""
        result = utils.get_cb_list(mock_engine)

        assert isinstance(result, list)
        assert len(result) > 0
        # 验证可转债代码格式
        for cb_code in result:
            assert '.' in cb_code
            assert cb_code.endswith('.SH') or cb_code.endswith('.SZ')

    @pytest.mark.unit
    def test_get_cb_info(self, mock_engine):
        """测试获取可转债信息"""
        result = utils.get_cb_info(mock_engine, '113008.SH')

        assert isinstance(result, dict)
        assert result['cb_code'] == '113008.SH'
        assert 'cb_name' in result
        assert 'stock_code' in result
        assert 'conversion_ratio' in result
        assert 'conversion_price' in result
        assert 'maturity_date' in result
        assert 'coupon_rate' in result

    # ==================== 期货相关测试 ====================

    @pytest.mark.unit
    def test_futures_trading_functions(self, mock_engine):
        """测试期货交易函数"""
        with patch('simtradelab.utils.order') as mock_order:
            mock_order.return_value = "ORDER_123"

            # 测试买开
            result = utils.buy_open(mock_engine, 'IF2312', 1)
            assert result == "ORDER_123"
            mock_order.assert_called_with(mock_engine, 'IF2312', 1)

            # 测试卖平
            result = utils.sell_close(mock_engine, 'IF2312', 1)
            assert result == "ORDER_123"
            mock_order.assert_called_with(mock_engine, 'IF2312', -1)

            # 测试卖开
            result = utils.sell_open(mock_engine, 'IF2312', 1)
            assert result == "ORDER_123"
            mock_order.assert_called_with(mock_engine, 'IF2312', -1)

            # 测试买平
            result = utils.buy_close(mock_engine, 'IF2312', 1)
            assert result == "ORDER_123"
            mock_order.assert_called_with(mock_engine, 'IF2312', 1)

    @pytest.mark.unit
    def test_set_future_commission(self, mock_engine):
        """测试设置期货手续费"""
        utils.set_future_commission(mock_engine, 0.0005, 10.0)

        assert mock_engine.future_commission_ratio == 0.0005
        assert mock_engine.future_min_commission == 10.0

    @pytest.mark.unit
    def test_set_margin_rate(self, mock_engine):
        """测试设置保证金比例"""
        utils.set_margin_rate(mock_engine, 0.15)

        assert mock_engine.margin_rate == 0.15

    @pytest.mark.unit
    def test_get_margin_rate(self, mock_engine):
        """测试获取保证金比例"""
        # 测试有设置的情况
        mock_engine.margin_rate = 0.12
        result = utils.get_margin_rate(mock_engine)
        assert result == 0.12

        # 测试无设置的情况
        delattr(mock_engine, 'margin_rate')
        result = utils.get_margin_rate(mock_engine)
        assert result == 0.1  # 默认值

    @pytest.mark.unit
    def test_get_instruments(self, mock_engine):
        """测试获取合约信息"""
        # 测试获取所有合约
        result = utils.get_instruments(mock_engine)
        assert isinstance(result, list)
        assert len(result) > 0

        # 验证合约信息结构
        instrument = result[0]
        assert 'code' in instrument
        assert 'name' in instrument
        assert 'exchange' in instrument
        assert 'multiplier' in instrument

        # 测试按交易所筛选
        result = utils.get_instruments(mock_engine, 'CFFEX')
        assert isinstance(result, list)
        for instrument in result:
            assert instrument['exchange'] == 'CFFEX'

    # ==================== 期权相关测试 ====================

    @pytest.mark.unit
    def test_get_opt_objects(self, mock_engine):
        """测试获取期权标的列表"""
        result = utils.get_opt_objects(mock_engine)

        assert isinstance(result, list)
        assert len(result) > 0
        # 验证期权标的代码格式
        for opt_code in result:
            assert '.' in opt_code
            assert opt_code.endswith('.SH') or opt_code.endswith('.SZ')

    @pytest.mark.unit
    def test_get_opt_last_dates(self, mock_engine):
        """测试获取期权到期日列表"""
        result = utils.get_opt_last_dates(mock_engine, '510050.SH')

        assert isinstance(result, list)
        assert len(result) > 0
        # 验证日期格式
        for date_str in result:
            assert len(date_str) == 10  # YYYY-MM-DD格式
            assert '-' in date_str

    @pytest.mark.unit
    def test_get_opt_contracts(self, mock_engine):
        """测试获取期权合约列表"""
        result = utils.get_opt_contracts(mock_engine, '510050.SH', '2024-01-31')

        assert isinstance(result, list)
        assert len(result) > 0

        # 验证合约信息结构
        contract = result[0]
        assert 'call' in contract
        assert 'put' in contract
        assert 'strike' in contract

    @pytest.mark.unit
    def test_option_exercise(self, mock_engine):
        """测试期权行权"""
        result = utils.option_exercise(mock_engine, '10004001.SH', 10)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_option_covered_lock_unlock(self, mock_engine):
        """测试期权备兑锁定解锁"""
        # 测试备兑锁定
        result = utils.option_covered_lock(mock_engine, '510050.SH', 100000)
        assert isinstance(result, str)
        assert len(result) > 0

        # 测试备兑解锁
        result = utils.option_covered_unlock(mock_engine, '510050.SH', 100000)
        assert isinstance(result, str)
        assert len(result) > 0

    # ==================== 市场查询测试 ====================

    @pytest.mark.unit
    def test_get_market_detail(self, mock_engine):
        """测试获取市场详细信息"""
        # 测试已知市场
        result = utils.get_market_detail(mock_engine, 'SH')
        assert isinstance(result, dict)
        assert result['name'] == '上海证券交易所'
        assert 'currency' in result
        assert 'timezone' in result

        result = utils.get_market_detail(mock_engine, 'SZ')
        assert isinstance(result, dict)
        assert result['name'] == '深圳证券交易所'

        # 测试未知市场
        result = utils.get_market_detail(mock_engine, 'UNKNOWN')
        assert isinstance(result, dict)
        assert 'name' in result

    @pytest.mark.unit
    def test_get_stock_blocks(self, mock_engine):
        """测试获取股票板块信息"""
        result = utils.get_stock_blocks(mock_engine, 'STOCK_A')

        assert isinstance(result, dict)
        assert 'industry' in result
        assert 'concept' in result
        assert 'area' in result
        assert 'market_cap' in result
        assert isinstance(result['concept'], list)

    @pytest.mark.unit
    def test_get_tick_direction(self, mock_engine):
        """测试获取tick方向"""
        result = utils.get_tick_direction(mock_engine, 'STOCK_A')

        assert isinstance(result, str)
        assert result in ['up', 'down', 'flat']

    @pytest.mark.unit
    def test_get_turnover_rate(self, mock_engine):
        """测试获取换手率"""
        result = utils.get_turnover_rate(mock_engine, 'STOCK_A')

        assert isinstance(result, float)
        assert 0 <= result <= 100  # 换手率应该在合理范围内

    @pytest.mark.unit
    def test_get_pe_ratio(self, mock_engine):
        """测试获取市盈率"""
        result = utils.get_pe_ratio(mock_engine, 'STOCK_A')

        assert isinstance(result, float)
        assert result > 0  # 市盈率应该为正数

    @pytest.mark.unit
    def test_get_pb_ratio(self, mock_engine):
        """测试获取市净率"""
        result = utils.get_pb_ratio(mock_engine, 'STOCK_A')

        assert isinstance(result, float)
        assert result > 0  # 市净率应该为正数

    # ==================== 分红配股测试 ====================

    @pytest.mark.unit
    def test_get_dividend_info(self, mock_engine):
        """测试获取分红信息"""
        # 测试默认年份
        result = utils.get_dividend_info(mock_engine, 'STOCK_A')
        assert isinstance(result, dict)
        assert result['stock'] == 'STOCK_A'
        assert 'dividend_per_share' in result
        assert 'ex_dividend_date' in result

        # 测试指定年份
        result = utils.get_dividend_info(mock_engine, 'STOCK_A', 2022)
        assert result['year'] == 2022

    @pytest.mark.unit
    def test_get_rights_issue_info(self, mock_engine):
        """测试获取配股信息"""
        result = utils.get_rights_issue_info(mock_engine, 'STOCK_A')

        assert isinstance(result, dict)
        assert result['stock'] == 'STOCK_A'
        assert 'rights_ratio' in result
        assert 'rights_shares' in result
        assert 'rights_price' in result
        assert 'ex_rights_date' in result

    # ==================== 停复牌测试 ====================

    @pytest.mark.unit
    def test_get_suspend_info(self, mock_engine):
        """测试获取停牌信息"""
        result = utils.get_suspend_info(mock_engine, 'STOCK_A')

        assert isinstance(result, dict)
        assert result['stock'] == 'STOCK_A'
        assert 'is_suspended' in result
        assert 'suspend_date' in result
        assert 'suspend_reason' in result
        assert 'expected_resume_date' in result

    @pytest.mark.unit
    def test_is_suspended(self, mock_engine):
        """测试判断股票是否停牌"""
        result = utils.is_suspended(mock_engine, 'STOCK_A')

        assert isinstance(result, bool)
        # 默认情况下应该返回False（正常交易）
        assert result is False

    # ==================== 涨跌停检查测试 ====================

    @pytest.mark.unit
    def test_check_limit(self, mock_engine):
        """测试涨跌停检查"""
        # 设置当前数据
        mock_engine.current_data = {
            'STOCK_A': {'close': 11.0}
        }

        result = utils.check_limit(mock_engine, 'STOCK_A')

        assert isinstance(result, dict)
        assert 'limit_up' in result
        assert 'limit_down' in result
        assert 'limit_up_price' in result
        assert 'limit_down_price' in result
        assert 'current_price' in result
        assert 'pct_change' in result

        # 测试无当前数据的情况
        mock_engine.current_data = {}
        result = utils.check_limit(mock_engine, 'STOCK_A')
        assert result['current_price'] is None

    # ==================== 账户信息测试 ====================

    @pytest.mark.unit
    def test_get_user_name(self, mock_engine):
        """测试获取用户名"""
        # 测试有账户ID的情况
        mock_engine.account_id = "TEST_ACCOUNT_123"
        result = utils.get_user_name(mock_engine)
        assert result == "TEST_ACCOUNT_123"

        # 测试无账户ID的情况
        delattr(mock_engine, 'account_id')
        result = utils.get_user_name(mock_engine)
        assert result == "SIMULATED_ACCOUNT_001"

    @pytest.mark.unit
    def test_get_trade_name(self, mock_engine):
        """测试获取交易名称"""
        # 测试有交易名称的情况
        mock_engine.trade_name = "TEST_TRADE"
        result = utils.get_trade_name(mock_engine)
        assert result == "TEST_TRADE"

        # 测试无交易名称的情况
        delattr(mock_engine, 'trade_name')
        result = utils.get_trade_name(mock_engine)
        assert result == "SimTradeLab_Backtest"

    @pytest.mark.unit
    def test_permission_test(self, mock_engine):
        """测试权限校验"""
        # 测试默认权限类型
        result = utils.permission_test(mock_engine)
        assert result is True

        # 测试指定权限类型
        result = utils.permission_test(mock_engine, "read")
        assert result is True

    @pytest.mark.unit
    def test_create_dir(self, mock_engine):
        """测试创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_engine.research_path = temp_dir

            # 测试创建目录
            result = utils.create_dir(mock_engine, "test_subdir/nested")

            assert result is not None
            assert Path(result).exists()
            assert Path(result).is_dir()

            # 测试无路径参数
            result = utils.create_dir(mock_engine, None)
            assert result is None

    # ==================== 股票信息查询测试 ====================

    @pytest.mark.unit
    def test_get_stock_exrights(self, mock_engine):
        """测试获取除权除息信息"""
        # 测试单个股票
        result = utils.get_stock_exrights(mock_engine, 'STOCK_A')
        assert isinstance(result, dict)
        assert 'STOCK_A' in result

        exrights_data = result['STOCK_A']
        assert 'dividend_date' in exrights_data
        assert 'ex_dividend_date' in exrights_data
        assert 'cash_dividend' in exrights_data

        # 测试多个股票
        result = utils.get_stock_exrights(mock_engine, ['STOCK_A', 'STOCK_B'])
        assert len(result) == 2

    @pytest.mark.unit
    def test_get_index_stocks(self, mock_engine):
        """测试获取指数成份股"""
        # 测试已知指数
        result = utils.get_index_stocks(mock_engine, '000001.SH')
        assert isinstance(result, list)
        assert len(result) > 0

        # 测试未知指数
        result = utils.get_index_stocks(mock_engine, 'UNKNOWN.SH')
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit
    def test_get_industry_stocks(self, mock_engine):
        """测试获取行业成份股"""
        # 测试已知行业
        result = utils.get_industry_stocks(mock_engine, '银行')
        assert isinstance(result, list)
        assert len(result) > 0

        # 测试未知行业
        result = utils.get_industry_stocks(mock_engine, '未知行业')
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit
    def test_get_ipo_stocks(self, mock_engine):
        """测试获取IPO申购标的"""
        result = utils.get_ipo_stocks(mock_engine)

        assert isinstance(result, list)
        assert len(result) > 0

        # 验证IPO信息结构
        ipo_stock = result[0]
        assert 'stock_code' in ipo_stock
        assert 'stock_name' in ipo_stock
        assert 'issue_price' in ipo_stock
        assert 'issue_date' in ipo_stock
        assert 'max_purchase_amount' in ipo_stock

    # ==================== 通知功能测试 ====================

    @pytest.mark.unit
    def test_send_email(self, mock_engine):
        """测试发送邮件"""
        result = utils.send_email(
            mock_engine,
            "test@example.com",
            "测试主题",
            "测试内容",
            ["attachment.txt"]
        )

        assert result is True

        # 测试无附件
        result = utils.send_email(mock_engine, "test@example.com", "主题", "内容")
        assert result is True

    @pytest.mark.unit
    def test_send_qywx(self, mock_engine):
        """测试发送企业微信"""
        # 测试发送到部门
        result = utils.send_qywx(mock_engine, "测试消息", toparty="部门1")
        assert result is True

        # 测试发送到用户
        result = utils.send_qywx(mock_engine, "测试消息", touser="用户1")
        assert result is True

        # 测试发送到标签
        result = utils.send_qywx(mock_engine, "测试消息", totag="标签1")
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
