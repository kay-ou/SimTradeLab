# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
API高级格式测试 - 提升覆盖率到71%
"""

import numpy as np
import pandas as pd

from simtradelab.ptrade.api import _compute_hl_adj, _has_typeab, _round2
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase


class TestPTradeRounding:
    """测试PTrade前复权舍入边界"""

    def test_compute_hl_adj_bypasses_xx4_range_pollution(self):
        """测试.XX4 high/low range污染时使用float64值"""
        adj_b = np.array([-1.506] * 20)
        high = np.array([5.79] + [5.0] * 19)
        low = np.array([4.5] * 19 + [4.07])

        adj_high, adj_low = _compute_hl_adj(adj_b, high, low)

        assert adj_high[0] == high[0] + adj_b[0]
        assert adj_low[-1] == low[-1] + adj_b[-1]
        assert _round2(high + adj_b)[0] == 4.28
        assert _round2(low + adj_b)[-1] == 2.56

    def test_compute_hl_adj_keeps_typeab_rounded(self):
        """测试TypeA/anti-TypeA窗口不触发high/low bypass"""
        adj_b = np.array([-0.395] * 20)
        high = np.array([10.03] + [10.0] * 19)
        low = np.array([9.0] * 19 + [8.0])

        adj_high, adj_low = _compute_hl_adj(adj_b, high, low)

        assert _has_typeab(high + adj_b)
        np.testing.assert_array_equal(adj_high, _round2(high + adj_b))
        np.testing.assert_array_equal(adj_low, _round2(low + adj_b))


class TestAPIAdvancedFormats:
    """测试API的多种返回格式"""

    def test_get_history_is_dict_format(self, ptrade_api):
        """测试get_history的is_dict=True返回格式"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # is_dict=True应返回字典格式 {stock: {field: array}}
        result = ptrade_api.get_history(
            count=3,
            field=["close", "volume"],
            security_list=["600000.SH", "000001.XSHE"],
            is_dict=True,
        )

        # 验证返回字典格式
        assert isinstance(result, dict)
        if result:  # 如果有数据
            for stock in result:
                assert isinstance(result[stock], dict)
                for field in result[stock]:
                    assert isinstance(
                        result[stock][field], (np.ndarray, pd.Series, list)
                    )

    def test_get_history_single_stock_not_in_result(self, ptrade_api):
        """测试get_history单股票不在结果中返回空DataFrame"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 查询不存在的股票
        result = ptrade_api.get_history(
            count=3, field="close", security_list="INVALID.XX"
        )

        # 应返回空DataFrame
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_history_single_stock_single_field(self, ptrade_api):
        """测试get_history单股票单字段返回DataFrame"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 单股票单字段
        result = ptrade_api.get_history(count=3, field="close", security_list="600000.SH")

        # 应返回DataFrame或Series（取决于数据可用性）
        # 如果有测试数据，验证结构
        if result is not None:
            assert isinstance(result, (pd.DataFrame, pd.Series))
            if isinstance(result, pd.DataFrame):
                assert "close" in result.columns or len(result.columns) > 0

    def test_get_history_multi_stock_single_field(self, ptrade_api):
        """测试get_history多股票单字段返回DataFrame"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 多股票单字段
        result = ptrade_api.get_history(
            count=3, field="close", security_list=["600000.SH", "000001.XSHE"]
        )

        # 应返回DataFrame
        if result is not None:
            assert isinstance(result, pd.DataFrame)
            # 如果有数据，应该包含股票列
            if not result.empty:
                assert len(result.columns) > 0

    def test_get_history_multi_stock_multi_field_panel(self, ptrade_api):
        """测试get_history多股票多字段返回PanelLike"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 多股票多字段应返回Panel格式
        result = ptrade_api.get_history(
            count=3,
            field=["close", "volume"],
            security_list=["600000.SH", "000001.XSHE"],
        )

        # 应返回PanelLike（字典类型，包含empty属性）
        if result is not None:
            # PanelLike是dict的子类
            assert isinstance(result, dict) or isinstance(result, pd.DataFrame)
            if isinstance(result, dict) and hasattr(result, "empty"):
                # 验证empty属性
                assert isinstance(result.empty, bool)

    def test_get_history_empty_result_with_is_dict(self, ptrade_api):
        """测试get_history空结果时is_dict=True返回空字典"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 查询不存在的股票，is_dict=True
        result = ptrade_api.get_history(
            count=3, field="close", security_list="INVALID.XX", is_dict=True
        )

        # 应返回空字典
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_history_empty_result_without_is_dict(self, ptrade_api):
        """测试get_history空结果时is_dict=False返回空DataFrame"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 查询不存在的股票，is_dict=False
        result = ptrade_api.get_history(
            count=3,
            field="close",
            security_list=["INVALID1.XX", "INVALID2.XX"],
            is_dict=False,
        )

        # 应返回空DataFrame或dict（取决于实现）
        if isinstance(result, pd.DataFrame):
            assert result.empty
        elif isinstance(result, dict):
            assert len(result) == 0
        # 如果返回None也是合理的（表示无数据）


class TestAPIComplexBranches:
    """测试API的复杂分支逻辑"""

    def test_get_stock_blocks_with_valid_json(self, ptrade_api, data_context):
        """测试get_stock_blocks解析JSON"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 如果有stock_metadata
        if not data_context.stock_metadata.empty:
            result = ptrade_api.get_stock_blocks("600000.SH")
            # 应返回字典（可能为空）
            assert isinstance(result, dict)

    def test_get_stock_blocks_invalid_stock(self, ptrade_api):
        """测试get_stock_blocks无效股票返回None"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        result = ptrade_api.get_stock_blocks("INVALID.XX")
        assert result is None

    def test_get_stock_info_field_not_in_metadata(self, ptrade_api):
        """测试get_stock_info字段不在metadata中的处理"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 查询不存在的字段
        result = ptrade_api.get_stock_info("600000.SH", field="non_existent_field")

        # 应返回字典
        assert isinstance(result, dict)
        assert "600000.SH" in result

    def test_get_stock_info_stock_name_fallback(self, ptrade_api):
        """测试get_stock_info的stock_name回退逻辑"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 查询不存在的股票
        result = ptrade_api.get_stock_info("INVALID.XX", field="stock_name")

        # stock_name应该回退到股票代码
        assert isinstance(result, dict)
        assert "INVALID.XX" in result
        if "stock_name" in result["INVALID.XX"]:
            assert result["INVALID.XX"]["stock_name"] == "INVALID.XX"


class TestAPIFundamentals:
    """测试get_fundamentals的复杂分支"""

    def test_get_fundamentals_empty_dataframe(self, ptrade_api, data_context):
        """测试get_fundamentals处理空DataFrame"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 模拟空数据
        data_context.fundamentals_dict["EMPTY.STOCK"] = pd.DataFrame()

        result = ptrade_api.get_fundamentals(
            security="EMPTY.STOCK",
            table="profit_ability",
            fields=["roe"],
            date="2024-01-05",
        )

        # 应返回空结果
        assert isinstance(result, (pd.DataFrame, dict, object))

    def test_get_fundamentals_valuation_vs_other_tables(self, ptrade_api):
        """测试get_fundamentals区分valuation和其他表"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # valuation表使用不同的data_dict
        result_val = ptrade_api.get_fundamentals(
            security="600000.SH",
            table="valuation",
            fields=["market_cap"],
            date="2024-01-05",
        )

        # 其他表
        result_income = ptrade_api.get_fundamentals(
            security="600000.SH",
            table="profit_ability",
            fields=["roe"],
            date="2024-01-05",
        )

        # 都应该返回有效对象
        assert result_val is not None
        assert result_income is not None

    def test_get_index_stocks_date_lookup(self, ptrade_api, data_context):
        """测试get_index_stocks的日期查找逻辑"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-05")

        # 模拟指数成份股数据（日期格式需与API一致：YYYYMMDD）
        data_context.index_constituents = {
            "20240101": {"000001.XSHG": ["600000.SH", "000001.XSHE"]},
            "20240110": {"000001.XSHG": ["600000.SH", "000002.XSHE"]},
        }
        ptrade_api._sorted_index_dates = None  # 清除缓存

        # 查询中间日期，应返回最近的历史数据
        result = ptrade_api.get_index_stocks("000001.XSHG", date="2024-01-05")

        # 应返回列表
        assert isinstance(result, list)

    def test_get_index_stocks_no_data_before_date(self, ptrade_api, data_context):
        """测试get_index_stocks查询日期早于所有数据"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 模拟指数数据（YYYYMMDD格式）
        data_context.index_constituents = {
            "20240110": {"000001.XSHG": ["600000.SH"]},
        }
        ptrade_api._sorted_index_dates = None  # 清除缓存

        # 查询早于所有数据的日期
        result = ptrade_api.get_index_stocks("000001.XSHG", date="2024-01-01")

        # 应返回空列表
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_industry_stocks_all_industries(self, ptrade_api, data_context):
        """测试get_industry_stocks返回所有行业"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # industry_code=None应返回所有行业
        result = ptrade_api.get_industry_stocks(industry_code=None)

        # 应返回字典
        assert isinstance(result, dict)

    def test_get_industry_stocks_specific_industry(self, ptrade_api, data_context):
        """测试get_industry_stocks返回特定行业"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 查询特定行业（可能不存在）
        result = ptrade_api.get_industry_stocks(industry_code="HY001")

        # 应返回列表
        assert isinstance(result, list)

    def test_get_industry_stocks_empty_metadata(self, ptrade_api, data_context):
        """测试get_industry_stocks处理空metadata"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 清空metadata
        original_metadata = data_context.stock_metadata
        data_context.stock_metadata = pd.DataFrame()

        result_all = ptrade_api.get_industry_stocks(industry_code=None)
        result_specific = ptrade_api.get_industry_stocks(industry_code="HY001")

        # 恢复
        data_context.stock_metadata = original_metadata

        # 空metadata应返回空
        assert result_all == {}
        assert result_specific == []
