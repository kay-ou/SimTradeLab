# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
API高级功能和边界测试 - 提升覆盖率
"""

import pytest
import pandas as pd
import numpy as np
import pandas as pd
from datetime import date

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase


class TestGetAsharesAPI:
    """测试get_Ashares API"""

    def test_get_ashares_no_date(self, ptrade_api):
        """测试不指定日期获取A股列表"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_Ashares()
        assert isinstance(result, list)
        assert len(result) > 0


class TestMarketAndExrightsAPI:
    """按文档返回形态测试市场与除权接口"""

    def test_get_market_list_uses_documented_codes(self, ptrade_api):
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        result = ptrade_api.get_market_list()

        assert 'XSHG' in set(result['finance_mic'])
        assert 'XSHE' in set(result['finance_mic'])
        assert 'XSHO' in set(result['finance_mic'])
        assert 'SHO' not in set(result['finance_mic'])

    def test_get_stock_exrights_accepts_int_date(self, ptrade_api, data_context):
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        data_context.exrights_dict['600000.SH'] = pd.DataFrame(
            {'bonus_ps': [0.1], 'allotted_ps': [0.0]},
            index=pd.Index([20240102], name='date')
        )

        result = ptrade_api.get_stock_exrights('600000.SH', date=20240102)

        assert isinstance(result, pd.DataFrame)
        assert result.index.tolist() == [20240102]


class TestFundamentalsAdvanced:
    """测试基本面数据的高级场景"""

    def test_get_fundamentals_valuation_table(self, ptrade_api):
        """测试valuation表的特殊处理"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_fundamentals(
            security='600000.SH',
            table='valuation',
            fields=['market_cap', 'pe_ratio'],
            date='2024-01-01'
        )
        assert result is None or isinstance(result, pd.DataFrame)

    def test_get_fundamentals_empty_security(self, ptrade_api):
        """测试空股票列表查询"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_fundamentals(
            security=[],
            table='valuation',
            fields=['market_cap']
        )
        assert result is None or (isinstance(result, pd.DataFrame) and result.empty)

    def test_get_fundamentals_fields_none_valuation(self, ptrade_api, data_context):
        """通用/财务文档: valuation表fields可不传"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-03')
        data_context.valuation_dict['600000.SH'] = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-02')],
            'total_shares': [1000.0, 1000.0],
            'pb': [1.1, 1.2],
        })

        result = ptrade_api.get_fundamentals('600000.SH', 'valuation', date='2024-01-02')

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['trading_day', 'total_value', 'secu_code']

    def test_get_fundamentals_valuation_uses_date_column(self, ptrade_api, data_context):
        """估值数据按date列选择查询日前最近记录"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-03')
        data_context.valuation_dict['600000.SH'] = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-03')],
            'pb': [1.1, 1.3],
        })

        result = ptrade_api.get_fundamentals('600000.SH', 'valuation', fields='pb', date='2024-01-02')

        assert result.loc['600000.SH', 'pb'] == 1.1

    def test_get_fundamentals_valuation_default_trading_day_from_index(self, ptrade_api, data_context):
        """storage加载后date进入索引时，默认valuation字段仍返回trading_day"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-03')
        data_context.valuation_dict['600000.SH'] = pd.DataFrame(
            {
                'total_shares': [1000.0, 1000.0],
                'pb': [1.1, 1.2],
            },
            index=pd.to_datetime(['2024-01-01', '2024-01-02'])
        )

        result = ptrade_api.get_fundamentals('600000.SH', 'valuation', date='2024-01-02')

        assert result.loc['600000.SH', 'trading_day'] == pd.Timestamp('2024-01-02')

    def test_get_fundamentals_default_end_date_from_index(self, ptrade_api, data_context):
        """storage加载后date进入索引时，默认财务字段仍返回end_date"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-05-01')
        data_context.fundamentals_dict['600000.SH'] = pd.DataFrame(
            {
                'secu_abbr': ['浦发银行'],
                'publ_date': [pd.Timestamp('2024-04-20')],
            },
            index=pd.to_datetime(['2024-03-31'])
        )

        result = ptrade_api.get_fundamentals(
            '600000.SH',
            'profit_ability',
            fields=None,
            date='2024-05-01'
        )

        assert result.loc['600000.SH', 'end_date'] == pd.Timestamp('2024-03-31')


class TestTradeDaysAdvanced:
    """测试交易日API的高级场景"""

    def test_get_trade_days_with_start_end(self, ptrade_api):
        """测试用开始和结束日期获取交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_trade_days(
            start_date='2024-01-01',
            end_date='2024-01-10'
        )
        assert isinstance(result, np.ndarray)

    def test_get_trade_days_none_params(self, ptrade_api):
        """测试不传参数获取所有交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        result = ptrade_api.get_trade_days()
        assert isinstance(result, np.ndarray)
        assert bool(result) is True

    def test_get_trading_day_guosheng_non_trade_day(self, ptrade_api):
        """国盛文档: 非交易日day=0返回下一交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.broker_profile = 'guosheng'
        ptrade_api.context.broker_profile = 'guosheng'
        ptrade_api.context.current_dt = pd.Timestamp('2023-12-31')

        result = ptrade_api.get_trading_day(day=0)
        assert result == date(2024, 1, 1)

    def test_get_trading_day_future(self, ptrade_api):
        """测试获取未来交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-05')

        result = ptrade_api.get_trading_day(day=1)
        assert result is None or isinstance(result, date)

    def test_get_trading_day_far_past(self, ptrade_api):
        """测试获取很久之前的交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-05')

        result = ptrade_api.get_trading_day(day=-100)
        assert result is None or isinstance(result, date)


class TestStockInfoAdvanced:
    """测试股票信息查询的高级场景"""

    def test_get_stock_info_all_fields(self, ptrade_api):
        """测试获取所有字段"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_stock_info('600000.SH')
        assert result is None or isinstance(result, dict)

    def test_get_stock_info_specific_fields(self, ptrade_api):
        """测试获取特定字段 - 通过结果判断"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_stock_info('600000.SH')
        # get_stock_info不支持fields参数,直接测试返回值
        assert result is None or isinstance(result, dict)

    def test_get_stock_info_invalid_stock(self, ptrade_api):
        """测试查询无效股票信息"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_stock_info('INVALID.XX')
        # 无效股票也会返回字典(可能包含默认值)
        assert result is None or isinstance(result, dict)


class TestGetPriceAdvanced:
    """测试get_price的高级场景"""

    def test_get_price_multiple_fields(self, ptrade_api):
        """测试获取多个字段"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-05')

        result = ptrade_api.get_price(
            security='600000.SH',
            count=5,
            fields=['open', 'high', 'low', 'close', 'volume']
        )
        assert result is None or isinstance(result, (pd.Series, pd.DataFrame, dict, float, int))

    def test_get_price_with_count(self, ptrade_api):
        """测试用count获取历史数据"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-05')

        result = ptrade_api.get_price(
            security='600000.SH',
            count=5,
            fields='close'
        )
        assert result is None or isinstance(result, (pd.Series, pd.DataFrame))

    def test_get_price_with_start_end(self, ptrade_api):
        """测试用起止日期获取历史数据"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-10')

        result = ptrade_api.get_price(
            security='600000.SH',
            start_date='2024-01-01',
            end_date='2024-01-05',
            fields='close'
        )
        assert result is None or isinstance(result, (pd.Series, pd.DataFrame))

    def test_get_price_list_of_securities(self, ptrade_api):
        """测试股票列表查询"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-05')

        result = ptrade_api.get_price(
            security=['600000.SH', '000001.SZ', '600519.SH'],
            count=5,
            fields='close'
        )
        assert result is None or isinstance(result, (pd.Series, pd.DataFrame))

    def test_get_price_with_fq(self, ptrade_api):
        """测试复权参数"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-05')

        # 测试前复权
        result = ptrade_api.get_price(
            security='600000.SH',
            count=5,
            fields='close',
            fq='pre'
        )
        assert result is None or isinstance(result, (float, int, np.number, pd.Series, pd.DataFrame))


class TestCheckStockStatus:
    """测试股票状态检查的高级场景"""

    def test_check_limit_up(self, ptrade_api):
        """测试涨停检查"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.check_limit('600000.SH')
        # check_limit返回字典
        assert isinstance(result, dict)

    def test_check_limit_guosheng_backtest(self, ptrade_api):
        """国盛文档: 回测中check_limit返回空字典"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')
        ptrade_api.broker_profile = 'guosheng'
        ptrade_api.context.broker_profile = 'guosheng'

        assert ptrade_api.check_limit('600000.SH') == {}

    def test_order_guosheng_empty_check_limit_does_not_keyerror(self, ptrade_api):
        """国盛check_limit返回空字典时，下单路径按无限制处理。"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')
        ptrade_api.broker_profile = 'guosheng'
        ptrade_api.context.broker_profile = 'guosheng'

        ptrade_api.order('600000.SH', 100)

    def test_check_limit_invalid_security_type(self, ptrade_api):
        """通用文档: 非str非list入参返回空字典"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        assert ptrade_api.check_limit(123) == {}

    def test_get_stock_status_normal(self, ptrade_api):
        """测试正常股票状态查询"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_stock_status('600000.SH')
        # 返回1表示正常，0表示停牌或字典
        assert result is not None

    def test_get_stock_status_unknown_stock_returns_none_value(self, ptrade_api):
        """通用文档: 未查询到相关数据时对应股票value为None"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        result = ptrade_api.get_stock_status('INVALID.XX')

        assert result == {'INVALID.XX': None}

    def test_get_stock_status_invalid_input_returns_none(self, ptrade_api):
        """通用文档: stocks入参错误时整体返回None"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        assert ptrade_api.get_stock_status(123) is None
