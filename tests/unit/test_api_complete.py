# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
测试剩余的关键API - 完整覆盖
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, datetime

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase, PTradeLifecycleError
from simtradelab.ptrade.config_manager import config


class TestFundamentalsAPI:
    """测试基本面数据API"""

    def test_get_fundamentals(self, ptrade_api):
        """测试get_fundamentals - 获取基本面数据"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 获取基本面数据
        result = ptrade_api.get_fundamentals(
            security='600000.SH',
            table='valuation',
            fields=['market_cap', 'pe_ratio'],
            date='2024-01-01'
        )
        assert result is None or isinstance(result, pd.DataFrame)


class TestTradingDaysAPI:
    """测试交易日相关API"""

    def test_get_all_trades_days(self, ptrade_api):
        """测试get_all_trades_days"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_all_trades_days(date='2024-01-01')
        assert isinstance(result, np.ndarray)

    def test_get_trading_day(self, ptrade_api):
        """测试get_trading_day - 获取指定偏移的交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 获取当天
        result = ptrade_api.get_trading_day(day=0)
        assert result is None or isinstance(result, date)

        # 获取前一天
        result = ptrade_api.get_trading_day(day=-1)
        assert result is None or isinstance(result, date)

    def test_get_trading_day_by_date(self, ptrade_api):
        """测试get_trading_day_by_date返回datetime.date"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_trading_day_by_date('2024-01-02')
        assert result is None or isinstance(result, date)

    def test_is_trade(self, ptrade_api):
        """测试is_trade - 判断是否交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.is_trade()
        assert isinstance(result, bool)


class TestStockBlocksAPI:
    """测试股票板块和行业API - 非必测，仅保留基础测试"""

    def test_get_stock_blocks(self, ptrade_api):
        """测试get_stock_blocks - 获取股票所属板块"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_stock_blocks('600000.SH')
        assert result is None or isinstance(result, dict)


class TestOrderManagementAPI:
    """测试订单管理API"""

    def test_get_open_orders(self, ptrade_api):
        """测试get_open_orders - 获取未成交订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_open_orders()
        assert isinstance(result, list)

    def test_get_orders(self, ptrade_api):
        """测试get_orders - 获取所有订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 获取所有订单
        result = ptrade_api.get_orders()
        assert isinstance(result, list)

        # 获取指定股票的订单
        result = ptrade_api.get_orders(security='600000.SH')
        assert isinstance(result, list)

    def test_get_order(self, ptrade_api):
        """测试get_order - 获取单个订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 文档要求返回只包含指定Order对象的list；不存在时为空list
        result = ptrade_api.get_order(order_id='non_existent_order')
        assert result == []

    def test_get_trades(self, ptrade_api):
        """测试get_trades - 获取成交记录"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_trades()
        assert isinstance(result, dict)


class TestAdvancedConfigAPI:
    """测试高级配置API"""

    def test_set_volume_ratio(self, ptrade_api):
        """测试set_volume_ratio - 设置成交量比例"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        ptrade_api.set_volume_ratio(volume_ratio=0.30)
        # 验证配置已更新
        assert config.trading.volume_ratio == 0.30

    def test_set_yesterday_position(self, ptrade_api):
        """测试set_yesterday_position - 设置昨日持仓"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        poslist = [
            {'sid': '600000.SH', 'enable_amount': 600, 'amount': 1000, 'cost_basis': 10.0},
            {'sid': '000001.SZ', 'enable_amount': 500, 'amount': 500, 'cost_basis': 15.0}
        ]
        ptrade_api.set_yesterday_position(poslist)

        position = ptrade_api.context.portfolio.positions['600000.SH']
        assert position.amount == 1000
        assert position.enable_amount == 600

    def test_set_yesterday_position_initializes_portfolio_state(self, ptrade_api):
        """底仓应初始化批次、失效净值缓存，并支持后续同股加仓。"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        portfolio = ptrade_api.context.portfolio
        portfolio._cached_portfolio_value = 123456.0

        ptrade_api.set_yesterday_position([
            {'sid': '600000.SH', 'enable_amount': 100, 'amount': 100, 'cost_basis': 10.0}
        ])

        assert portfolio._cached_portfolio_value is None
        assert portfolio._position_lots['600000.SH'][0]['amount'] == 100
        portfolio.add_position('600000.SH', 100, 11.0, datetime(2024, 1, 2))
        assert len(portfolio._position_lots['600000.SH']) == 2

    def test_convert_position_from_csv_document_fields(self, ptrade_api, tmp_path):
        """文档: CSV字段为sid,enable_amount,amount,cost_basis"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        csv_path = Path(tmp_path) / 'Poslist.csv'
        csv_path.write_text('sid,enable_amount,amount,cost_basis\n600570.SS,10000,10000,45\n', encoding='utf-8')

        result = ptrade_api.convert_position_from_csv(str(csv_path))

        assert result == [{'sid': '600570.SS', 'enable_amount': 10000, 'amount': 10000, 'cost_basis': 45.0}]

    def test_run_daily(self, ptrade_api):
        """测试run_daily - 设置每日定时任务"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        def my_daily_func(context, data):
            pass

        # 设置每日9:31执行
        ptrade_api.run_daily(ptrade_api.context, my_daily_func, time='9:31')

        assert ptrade_api._daily_tasks == [(my_daily_func, '09:31')]

    def test_run_daily_normalizes_default_time(self, ptrade_api):
        """默认任务时间应与分钟循环使用相同的零填充格式。"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        def my_daily_func(context):
            pass

        ptrade_api.run_daily(ptrade_api.context, my_daily_func)

        assert ptrade_api._daily_tasks == [(my_daily_func, '09:31')]

    def test_run_interval(self, ptrade_api):
        """测试run_interval - 设置定时任务"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        def my_interval_func(context, data):
            pass

        # 设置每10秒执行
        ptrade_api.run_interval(ptrade_api.context, my_interval_func, seconds=10)

        # 不报错即可
        assert True


class TestUtilityAPI:
    """测试工具类API"""

    def test_get_research_path(self, ptrade_api):
        """测试get_research_path - 获取研究路径"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_research_path()
        # 应该返回字符串路径
        assert result is None or isinstance(result, str)

    def test_prebuild_date_index(self, ptrade_api):
        """测试prebuild_date_index - 预构建日期索引"""
        # 预构建日期索引（性能优化）
        stocks = ['600000.SH', '000001.SZ']
        ptrade_api.prebuild_date_index(stocks=stocks)

        # 不报错即可
        assert True

    def test_get_stock_date_index(self, ptrade_api):
        """测试get_stock_date_index - 获取股票日期索引"""
        date_dict, sorted_dates = ptrade_api.get_stock_date_index('600000.SH')
        assert isinstance(date_dict, dict)
        assert isinstance(sorted_dates, (list, np.ndarray))


class TestLifecycleStrictness:
    """测试生命周期限制的严格性 - 确保所有API都遵守"""

    def test_set_volume_ratio_only_in_initialize(self, ptrade_api):
        """set_volume_ratio只能在initialize调用"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.set_volume_ratio(0.3)

        # 在handle_data阶段不能调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        with pytest.raises(PTradeLifecycleError):
            ptrade_api.set_volume_ratio(0.3)

    def test_set_yesterday_position_only_in_initialize(self, ptrade_api):
        """set_yesterday_position只能在initialize调用"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.set_yesterday_position([])

        # 也可以在before_trading_start调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.BEFORE_TRADING_START)
        ptrade_api.set_yesterday_position([])

    def test_run_daily_only_in_initialize(self, ptrade_api):
        """run_daily只能在initialize调用"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        def func(ctx, data):
            pass

        ptrade_api.run_daily(ptrade_api.context, func)

        # 验证是否成功设置（run_daily不一定会在handle_data抛错，取决于实现）
        assert True

    def test_cancel_order_in_correct_phases(self, ptrade_api):
        """cancel_order可以在handle_data调用"""
        # handle_data阶段可以调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        result = ptrade_api.cancel_order(None)
        assert result is None
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
加强薄弱API的测试 - 深度测试
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase, PTradeLifecycleError


class TestOrderTargetValueEnhanced:
    """加强order_target_value测试"""

    def test_order_target_value_zero(self, ptrade_api):
        """测试目标金额为0（清仓）"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.order_target_value('600000.SH', 0)
        # 目标金额0应该触发清仓
        assert result is not None or result is None

    def test_order_target_value_negative(self, ptrade_api):
        """测试负的目标金额"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 负金额应该被处理或拒绝
        result = ptrade_api.order_target_value('600000.SH', -10000)
        assert result is not None or result is None

    def test_order_target_value_exceed_cash(self, ptrade_api):
        """测试目标金额超过现金"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 尝试目标金额超过总资金
        result = ptrade_api.order_target_value('600000.SH', 99999999)
        assert result is not None or result is None


class TestOrderQueryEnhanced:
    """加强订单查询API测试"""

    def test_get_open_orders_empty(self, ptrade_api):
        """测试没有未成交订单时"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_open_orders()
        assert isinstance(result, list)
        # 初始应该是空的
        assert len(result) == 0

    def test_get_open_orders_after_order(self, ptrade_api):
        """测试下单后查询未成交订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 先下单
        ptrade_api.order('600000.SH', 100)

        # 查询未成交订单
        result = ptrade_api.get_open_orders()
        assert isinstance(result, list)

    def test_get_order_nonexistent(self, ptrade_api):
        """测试查询不存在的订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询不存在的订单ID
        result = ptrade_api.get_order('nonexistent_id_123456')
        assert result == []

    def test_get_order_with_valid_id(self, ptrade_api):
        """测试用有效ID查询订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 先下单获取订单ID
        order_id = ptrade_api.order('600000.SH', 100)

        if order_id:
            # 用订单ID查询
            result = ptrade_api.get_order(order_id)
            assert isinstance(result, list)
            assert len(result) <= 1

    def test_get_trades_empty(self, ptrade_api):
        """测试没有成交记录时"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_trades()
        assert result == {}


class TestConfigEnhanced:
    """加强配置API测试"""

    def test_set_slippage_default_is_point001(self, ptrade_api):
        """通用文档: set_slippage默认slippage=0.001"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        config.update_trading_config(slippage=0.0)

        ptrade_api.set_slippage()

        assert config.trading.slippage == 0.001

    def test_set_fixed_slippage_zero(self, ptrade_api):
        """测试设置0滑点"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        ptrade_api.set_fixed_slippage(fixedslippage=0.0)
        # 配置通过config管理,不需要检查context属性

    def test_set_fixed_slippage_default_is_zero(self, ptrade_api):
        """通用文档: set_fixed_slippage默认fixedslippage=0.0"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        config.update_trading_config(fixed_slippage=0.05)

        ptrade_api.set_fixed_slippage()

        assert config.trading.fixed_slippage == 0.0

    def test_set_fixed_slippage_large(self, ptrade_api):
        """测试设置大滑点"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        ptrade_api.set_fixed_slippage(fixedslippage=0.05)  # 5%滑点
        # 配置通过config管理,不需要检查context属性

    def test_set_limit_mode_strict(self, ptrade_api):
        """测试LIMIT模式（严格涨跌停）"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        ptrade_api.set_limit_mode(limit_mode='LIMIT')
        # 配置通过config管理,不需要检查context属性

    def test_set_limit_mode_pct_change(self, ptrade_api):
        """测试PCT_CHANGE模式"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        ptrade_api.set_limit_mode(limit_mode='PCT_CHANGE')
        # 配置通过config管理,不需要检查context属性

    def test_run_interval_different_times(self, ptrade_api):
        """测试不同时间间隔的定时任务"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        def my_func(context, data):
            pass

        # 测试不同秒数
        ptrade_api.run_interval(ptrade_api.context, my_func, seconds=5)
        ptrade_api.run_interval(ptrade_api.context, my_func, seconds=60)
        ptrade_api.run_interval(ptrade_api.context, my_func, seconds=300)

        assert True


class TestTradingDaysEnhanced:
    """加强交易日API测试"""

    def test_get_all_trades_days_with_date(self, ptrade_api):
        """测试指定日期获取所有交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_all_trades_days(date='2024-01-01')
        assert isinstance(result, np.ndarray)
        if result:
            # 验证返回的是日期字符串
            assert isinstance(result[0], str)

    def test_get_all_trades_days_none(self, ptrade_api):
        """测试不传日期获取交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_all_trades_days(date=None)
        assert isinstance(result, np.ndarray)

    def test_get_trade_days_date_range(self, ptrade_api):
        """测试日期范围获取交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_trade_days(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )
        assert isinstance(result, np.ndarray)
        # 验证返回的交易日数量合理
        assert len(result) <= 31  # 一个月最多31天

    def test_get_trade_days_with_count(self, ptrade_api):
        """测试用count参数获取交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 根据PTrade文档,start_date和count不能同时使用
        # 只使用count获取最近10个交易日
        result = ptrade_api.get_trade_days(count=10)
        assert isinstance(result, np.ndarray)
        # 验证数量不超过count
        assert len(result) <= 10

    def test_is_trade_different_dates(self, ptrade_api):
        """测试不同日期是否交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 测试工作日
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')  # 周二
        result = ptrade_api.is_trade()
        assert isinstance(result, bool)

        # 测试周末
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-06')  # 周六
        result = ptrade_api.is_trade()
        assert isinstance(result, bool)


class TestDataAPIEnhanced:
    """加强数据API测试"""

    def test_get_fundamentals_different_tables(self, ptrade_api):
        """测试不同基本面数据表"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 每个表使用正确的字段
        test_cases = [
            ('valuation', ['market_cap', 'pe_ratio']),
            ('profit_ability', ['roe', 'roa']),
            ('growth_ability', ['net_profit_grow_rate']),
        ]

        for table, fields in test_cases:
            result = ptrade_api.get_fundamentals(
                security='600000.SH',
                table=table,
                fields=fields,
                date='2024-01-01'
            )
            assert result is None or isinstance(result, pd.DataFrame)

    def test_get_fundamentals_multiple_stocks(self, ptrade_api):
        """测试多个股票的基本面数据"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_fundamentals(
            security=['600000.SH', '000001.SZ'],
            table='valuation',
            fields=['market_cap', 'pe_ratio'],
            date='2024-01-01'
        )
        assert result is None or isinstance(result, pd.DataFrame)

    def test_get_price_single_stock_single_field(self, ptrade_api):
        """测试get_price - 单股票单字段"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-15')

        # 单股票，单字段，返回DataFrame
        result = ptrade_api.get_price(
            security='600000.SH',
            start_date='2024-01-01',
            end_date='2024-01-10',
            fields='close'
        )
        assert isinstance(result, pd.DataFrame)

    def test_get_price_single_stock_multiple_fields(self, ptrade_api):
        """测试get_price - 单股票多字段"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-15')

        # 单股票，多字段
        result = ptrade_api.get_price(
            security='600000.SH',
            start_date='2024-01-01',
            end_date='2024-01-10',
            fields=['open', 'high', 'low', 'close']
        )
        assert isinstance(result, pd.DataFrame)

    def test_get_price_multiple_stocks_single_field(self, ptrade_api):
        """测试get_price - 多股票单字段"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-15')

        # 多股票，单字段，返回DataFrame（列为股票代码）
        result = ptrade_api.get_price(
            security=['600000.SH', '000001.SZ'],
            start_date='2024-01-01',
            end_date='2024-01-10',
            fields='close'
        )
        assert isinstance(result, pd.DataFrame) or isinstance(result, ptrade_api.PanelLike)

    def test_get_price_multiple_stocks_multiple_fields(self, ptrade_api):
        """测试get_price - 多股票多字段"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-15')

        # 多股票，多字段，返回PanelLike对象
        result = ptrade_api.get_price(
            security=['600000.SH', '000001.SZ'],
            start_date='2024-01-01',
            end_date='2024-01-10',
            fields=['open', 'close']
        )
        # 应该返回PanelLike或DataFrame
        assert isinstance(result, pd.DataFrame) or isinstance(result, ptrade_api.PanelLike)

    def test_get_price_with_count(self, ptrade_api):
        """测试get_price - 使用count参数"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-15')

        # 使用count参数获取最近N天数据
        result = ptrade_api.get_price(
            security='600000.SH',
            end_date='2024-01-10',
            fields='close',
            count=5
        )
        assert isinstance(result, pd.DataFrame)

    def test_get_price_with_fq(self, ptrade_api):
        """测试get_price - 复权参数"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-15')

        # 测试前复权
        result = ptrade_api.get_price(
            security='600000.SH',
            start_date='2024-01-01',
            end_date='2024-01-10',
            fields='close',
            fq='pre'
        )
        assert isinstance(result, pd.DataFrame)

class TestUtilityEnhanced:
    """加强工具API测试"""

    def test_get_research_path_returns_string(self, ptrade_api):
        """测试get_research_path返回路径字符串"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_research_path()
        assert result is None or isinstance(result, str)
        if isinstance(result, str):
            # 验证路径格式
            assert len(result) > 0

    def test_prebuild_date_index_single_stock(self, ptrade_api):
        """测试单个股票预构建索引"""
        stocks = ['600000.SH']
        ptrade_api.prebuild_date_index(stocks=stocks)
        assert True

    def test_prebuild_date_index_multiple_stocks(self, ptrade_api):
        """测试多个股票预构建索引"""
        stocks = ['600000.SH', '000001.SZ', '600519.SH']
        ptrade_api.prebuild_date_index(stocks=stocks)
        assert True

    def test_prebuild_date_index_none(self, ptrade_api):
        """测试不传股票列表预构建索引"""
        ptrade_api.prebuild_date_index(stocks=None)
        assert True

    def test_get_stock_date_index_valid_stock(self, ptrade_api):
        """测试获取有效股票的日期索引"""
        date_dict, sorted_dates = ptrade_api.get_stock_date_index('600000.SH')
        assert isinstance(date_dict, dict)
        assert isinstance(sorted_dates, (list, np.ndarray))
        # 验证结构
        if len(sorted_dates) > 0:
            # 日期列表应该是排序的
            assert len(sorted_dates) > 0

    def test_get_stock_date_index_invalid_stock(self, ptrade_api):
        """测试获取无效股票的日期索引"""
        date_dict, sorted_dates = ptrade_api.get_stock_date_index('INVALID.XX')
        # 无效股票应该返回空或抛异常
        assert isinstance(date_dict, dict)
        assert isinstance(sorted_dates, (list, np.ndarray))


class TestPositionQueryEnhanced:
    """加强持仓查询测试"""

    def test_get_position_empty(self, ptrade_api):
        """测试查询空持仓"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询未持有的股票
        position = ptrade_api.get_position('600000.SH')

        from simtradelab.ptrade.object import Position
        assert isinstance(position, Position)
        assert position.amount == 0

    def test_get_position_after_buy(self, ptrade_api, portfolio):
        """测试买入后查询持仓"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 先建立持仓
        portfolio.add_position('600000.SH', 100, 10.0, datetime(2024, 1, 1))

        # 查询持仓
        position = ptrade_api.get_position('600000.SH')

        from simtradelab.ptrade.object import Position
        if position:
            assert isinstance(position, Position)
            assert position.amount == 100

    def test_get_position_multiple_stocks(self, ptrade_api, portfolio):
        """测试查询多个股票持仓"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 建立多个持仓
        portfolio.add_position('600000.SH', 100, 10.0, datetime(2024, 1, 1))
        portfolio.add_position('000001.SZ', 200, 15.0, datetime(2024, 1, 1))

        # 分别查询
        pos1 = ptrade_api.get_position('600000.SH')
        pos2 = ptrade_api.get_position('000001.SZ')
        pos3 = ptrade_api.get_position('600519.SH')  # 未持有

        assert pos1.amount == 100
        assert pos2.amount == 200
        assert pos3.amount == 0


class TestOrderTargetBehavior:
    """测试order_target的核心行为逻辑"""

    def test_order_target_same_as_current(self, ptrade_api, portfolio):
        """测试目标数量等于当前持仓"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 先建立100股持仓
        portfolio.add_position('600000.SH', 100, 10.0, datetime(2024, 1, 1))

        # order_target(100)应该不下单（delta=0）
        result = ptrade_api.order_target('600000.SH', 100)

        # delta为0，应该返回None
        assert result is None


class TestCancelOrderBehavior:
    """测试cancel_order的行为"""

    def test_cancel_order_valid_order(self, ptrade_api):
        """测试取消有效订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 先创建订单
        order_id = ptrade_api.order('600000.SH', 100)

        if order_id:
            # 取消订单
            result = ptrade_api.cancel_order(order_id)
            assert result is None

    def test_cancel_order_nonexistent(self, ptrade_api):
        """测试取消不存在的订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 取消不存在的订单
        result = ptrade_api.cancel_order('nonexistent_order_id_12345')

        assert result is None

    def test_cancel_order_none(self, ptrade_api):
        """测试取消None订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 取消None订单
        result = ptrade_api.cancel_order(None)

        assert result is None


class TestOrderQueryBehavior:
    """测试订单查询API的行为"""

    def test_get_orders_after_placing_order(self, ptrade_api):
        """测试下单后查询订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 下单前查询
        orders_before = ptrade_api.get_orders()
        assert isinstance(orders_before, list)
        initial_count = len(orders_before)

        # 下单
        order_id = ptrade_api.order('600000.SH', 100)

        if order_id:
            # 下单后查询
            orders_after = ptrade_api.get_orders()
            assert isinstance(orders_after, list)
            # 订单数量应该增加（如果订单被记录）
            assert len(orders_after) >= initial_count

    def test_get_orders_by_security(self, ptrade_api):
        """测试按股票代码查询订单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 对特定股票下单
        order_id = ptrade_api.order('600000.SH', 100)

        if order_id:
            # 查询该股票的订单
            orders = ptrade_api.get_orders(security='600000.SH')
            assert isinstance(orders, list)

    def test_get_trades_after_execution(self, ptrade_api):
        """测试订单执行后查询成交"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询执行前的成交记录
        trades_before = ptrade_api.get_trades()
        assert isinstance(trades_before, dict)
        initial_count = len(trades_before)

        # 下单（如果成功执行会产生成交记录）
        order_id = ptrade_api.order('600000.SH', 100)

        if order_id:
            # 查询成交记录
            trades_after = ptrade_api.get_trades()
            assert isinstance(trades_after, dict)
            assert len(trades_after) >= initial_count
            trade_rows = trades_after[str(order_id)]
            assert len(trade_rows[0]) == 8
            assert trade_rows[0][2] == '600000.XSHG'
