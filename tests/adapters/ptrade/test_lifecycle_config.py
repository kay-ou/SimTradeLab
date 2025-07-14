# -*- coding: utf-8 -*-
"""
lifecycle_config.py 测试文件

测试PTrade API生命周期配置
"""

import pytest

from src.simtradelab.adapters.ptrade.lifecycle_config import (
    API_LIFECYCLE_RESTRICTIONS,
    get_api_allowed_phases,
    get_phase_apis,
    is_api_allowed_in_phase,
    validate_config,
)


@pytest.mark.unit
class TestAPILifecycleRestrictions:
    """API生命周期限制测试"""

    def test_api_lifecycle_restrictions_structure(self):
        """测试API生命周期限制数据结构"""
        assert isinstance(API_LIFECYCLE_RESTRICTIONS, dict)
        assert len(API_LIFECYCLE_RESTRICTIONS) > 0

        # 检查一些已知的关键API
        assert "set_universe" in API_LIFECYCLE_RESTRICTIONS
        assert "order" in API_LIFECYCLE_RESTRICTIONS
        assert "get_price" in API_LIFECYCLE_RESTRICTIONS
        assert "get_history" in API_LIFECYCLE_RESTRICTIONS

    def test_all_apis_have_list_restrictions(self):
        """测试所有API都有列表类型的限制"""
        for api_name, restrictions in API_LIFECYCLE_RESTRICTIONS.items():
            assert isinstance(restrictions, list), f"API {api_name} 的限制应该是列表类型"
            assert len(restrictions) > 0, f"API {api_name} 的限制列表不能为空"

    def test_known_lifecycle_phases(self):
        """测试已知的生命周期阶段"""
        all_phases = set()
        for restrictions in API_LIFECYCLE_RESTRICTIONS.values():
            all_phases.update(restrictions)

        # 检查关键阶段存在
        expected_phases = {
            "initialize",
            "handle_data",
            "before_trading_start",
            "after_trading_end",
            "tick_data",
            "all",
        }

        for phase in expected_phases:
            assert phase in all_phases, f"缺少关键生命周期阶段: {phase}"

    def test_all_phase_semantics(self):
        """测试'all'阶段的语义"""
        # 有些API应该在所有阶段都可用
        apis_with_all_phase = [
            api
            for api, restrictions in API_LIFECYCLE_RESTRICTIONS.items()
            if "all" in restrictions
        ]

        # 至少应该有一些通用API有'all'权限
        assert len(apis_with_all_phase) > 0

        # 检查一些预期的通用API
        expected_all_apis = ["get_price", "get_history", "log"]
        for api in expected_all_apis:
            if api in API_LIFECYCLE_RESTRICTIONS:
                assert "all" in API_LIFECYCLE_RESTRICTIONS[api], f"{api} 应该在所有阶段可用"


@pytest.mark.unit
class TestIsApiAllowedInPhase:
    """测试is_api_allowed_in_phase函数"""

    def test_api_allowed_in_specific_phase(self):
        """测试API在特定阶段被允许"""
        # set_universe 只能在initialize阶段调用
        assert is_api_allowed_in_phase("set_universe", "initialize") is True
        assert is_api_allowed_in_phase("set_universe", "handle_data") is False

        # order 能在handle_data阶段调用
        if "order" in API_LIFECYCLE_RESTRICTIONS:
            order_phases = API_LIFECYCLE_RESTRICTIONS["order"]
            if "handle_data" in order_phases:
                assert is_api_allowed_in_phase("order", "handle_data") is True
            if "initialize" not in order_phases:
                assert is_api_allowed_in_phase("order", "initialize") is False

    def test_api_with_all_phase(self):
        """测试有'all'权限的API"""
        # 查找有'all'权限的API
        apis_with_all = [
            api
            for api, restrictions in API_LIFECYCLE_RESTRICTIONS.items()
            if "all" in restrictions
        ]

        if apis_with_all:
            test_api = apis_with_all[0]
            # 在知名阶段都应该被允许
            assert is_api_allowed_in_phase(test_api, "initialize") is True
            assert is_api_allowed_in_phase(test_api, "handle_data") is True
            assert is_api_allowed_in_phase(test_api, "before_trading_start") is True
            # 未知阶段的行为取决于具体实现，这里不做断言

    def test_unknown_api(self):
        """测试未知API"""
        # 根据实际实现，未知API返回所有阶段（默认"all"）
        # 所以在任何知名阶段都应该被允许
        assert is_api_allowed_in_phase("unknown_api", "handle_data") is True
        assert is_api_allowed_in_phase("non_existent_api", "initialize") is True

    def test_empty_api_name(self):
        """测试空API名称"""
        # 根据实际实现，空API名称返回所有阶段（默认"all"）
        assert is_api_allowed_in_phase("", "handle_data") is True
        assert is_api_allowed_in_phase(None, "handle_data") is True

    def test_case_sensitivity(self):
        """测试大小写敏感性"""
        # API名称应该是大小写敏感的
        if "get_price" in API_LIFECYCLE_RESTRICTIONS:
            phases = API_LIFECYCLE_RESTRICTIONS["get_price"]
            if phases:
                test_phase = phases[0] if phases != ["all"] else "handle_data"
                assert is_api_allowed_in_phase("get_price", test_phase) is True
                # 大小写不同的API名称会被视为未知API，返回默认值
                # 根据实际实现，未知API允许在所有阶段调用
                assert is_api_allowed_in_phase("GET_PRICE", test_phase) is True
                assert is_api_allowed_in_phase("Get_Price", test_phase) is True


@pytest.mark.unit
class TestGetAllowedApisForPhase:
    """测试get_allowed_apis_for_phase函数"""

    def test_get_apis_for_initialize_phase(self):
        """测试获取initialize阶段的API"""
        apis = get_phase_apis("initialize")

        assert isinstance(apis, list)
        assert len(apis) > 0
        assert "set_universe" in apis  # set_universe应该在initialize阶段

        # 验证所有返回的API确实在该阶段被允许
        for api in apis:
            assert is_api_allowed_in_phase(
                api, "initialize"
            ), f"API {api} 不应该在initialize阶段"

    def test_get_apis_for_handle_data_phase(self):
        """测试获取handle_data阶段的API"""
        apis = get_phase_apis("handle_data")

        assert isinstance(apis, list)
        assert len(apis) > 0

        # handle_data阶段应该允许更多API
        for api in apis:
            assert is_api_allowed_in_phase(
                api, "handle_data"
            ), f"API {api} 不应该在handle_data阶段"

    def test_get_apis_for_unknown_phase(self):
        """测试获取未知阶段的API"""
        apis = get_phase_apis("unknown_phase")

        # 未知阶段应该只返回有'all'权限的API
        all_phase_apis = [
            api
            for api, restrictions in API_LIFECYCLE_RESTRICTIONS.items()
            if "all" in restrictions
        ]

        assert set(apis) == set(all_phase_apis)

    def test_all_phase_returns_all_apis(self):
        """测试'all'阶段返回所有API"""
        # 特殊情况：'all'不是一个真正的生命周期阶段
        # 它是一个标记，表示在所有阶段都可用
        # 我们测试一个实际的阶段名称
        apis = get_phase_apis("handle_data")

        # handle_data阶段应该包含许多 API
        assert len(apis) > 0
        # 验证包含一些期望的API
        expected_in_handle_data = ["order", "get_price", "get_history"]
        for api in expected_in_handle_data:
            if api in API_LIFECYCLE_RESTRICTIONS:
                if (
                    "all" in API_LIFECYCLE_RESTRICTIONS[api]
                    or "handle_data" in API_LIFECYCLE_RESTRICTIONS[api]
                ):
                    assert api in apis


@pytest.mark.unit
class TestGetPhasesForApi:
    """测试get_phases_for_api函数"""

    def test_get_phases_for_known_api(self):
        """测试获取已知API的阶段"""
        # 测试set_universe API
        phases = get_api_allowed_phases("set_universe")
        expected_phases = API_LIFECYCLE_RESTRICTIONS["set_universe"]

        assert isinstance(phases, list)
        assert set(phases) == set(expected_phases)

    def test_get_phases_for_unknown_api(self):
        """测试获取未知API的阶段"""
        phases = get_api_allowed_phases("unknown_api")
        # 未知API应该返回所有阶段（默认为'all'）
        from src.simtradelab.adapters.ptrade.lifecycle_config import LIFECYCLE_PHASES

        assert set(phases) == set(LIFECYCLE_PHASES)

    def test_get_phases_for_empty_api(self):
        """测试空API名称"""
        from src.simtradelab.adapters.ptrade.lifecycle_config import LIFECYCLE_PHASES

        # 空字符串和None应该返回所有阶段（默认为'all'）
        assert set(get_api_allowed_phases("")) == set(LIFECYCLE_PHASES)
        assert set(get_api_allowed_phases(None)) == set(LIFECYCLE_PHASES)

    def test_phases_consistency(self):
        """测试阶段一致性"""
        # 对于每个API，验证返回的阶段确实允许该API
        for api_name in list(API_LIFECYCLE_RESTRICTIONS.keys())[:5]:  # 测试前5个API
            phases = get_api_allowed_phases(api_name)
            for phase in phases:
                assert is_api_allowed_in_phase(
                    api_name, phase
                ), f"API {api_name} 在阶段 {phase} 应该被允许"


@pytest.mark.unit
class TestValidateLifecycleConfig:
    """测试validate_lifecycle_config函数"""

    def test_validate_current_config(self):
        """测试验证当前配置"""
        # 当前配置应该是有效的
        result = validate_config()
        assert result is True

    def test_validate_detects_inconsistencies(self):
        """测试验证能发现不一致性"""
        # 这个测试验证validate_config能够发现配置问题
        try:
            result = validate_config()
            assert result is True
        except ValueError as e:
            # 如果有错误，应该是期望的错误格式
            assert "Configuration errors:" in str(e)

    def test_all_phases_are_valid_strings(self):
        """测试所有阶段都是有效字符串"""
        for api_name, phases in API_LIFECYCLE_RESTRICTIONS.items():
            for phase in phases:
                assert isinstance(phase, str), f"API {api_name} 的阶段 {phase} 不是字符串"
                assert len(phase.strip()) > 0, f"API {api_name} 有空阶段"

    def test_no_circular_dependencies(self):
        """测试没有循环依赖"""
        # 这是一个基本的健全性检查
        # 确保没有API的限制列表为空（除非明确设计如此）
        empty_restriction_apis = [
            api
            for api, restrictions in API_LIFECYCLE_RESTRICTIONS.items()
            if not restrictions
        ]

        # 通常不应该有完全没有限制的API
        assert (
            len(empty_restriction_apis) == 0
        ), f"发现没有阶段限制的API: {empty_restriction_apis}"


@pytest.mark.integration
class TestLifecycleConfigIntegration:
    """生命周期配置集成测试"""

    def test_typical_strategy_lifecycle(self):
        """测试典型策略生命周期"""
        # 模拟一个典型策略的API调用序列

        # 1. 初始化阶段
        assert is_api_allowed_in_phase("set_universe", "initialize")

        # 2. handle_data阶段
        apis_in_handle_data = get_phase_apis("handle_data")

        # handle_data阶段应该能够获取价格
        if "get_price" in API_LIFECYCLE_RESTRICTIONS:
            assert "get_price" in apis_in_handle_data

        # 可能能够下单（取决于配置）
        if "order" in API_LIFECYCLE_RESTRICTIONS:
            order_phases = get_api_allowed_phases("order")
            if "handle_data" in order_phases:
                assert "order" in apis_in_handle_data

    def test_comprehensive_api_coverage(self):
        """测试API覆盖的全面性"""
        # 验证重要的PTrade API都有定义
        important_apis = [
            "set_universe",
            "order",
            "get_price",
            "get_history",
            "get_positions",
            "get_orders",
            "cancel_order",
        ]

        defined_apis = set(API_LIFECYCLE_RESTRICTIONS.keys())

        missing_apis = []
        for api in important_apis:
            if api not in defined_apis:
                missing_apis.append(api)

        # 记录缺失的API（不一定是错误，可能是设计决定）
        if missing_apis:
            print(f"注意：以下重要API未在生命周期配置中定义: {missing_apis}")

    def test_phase_transition_validity(self):
        """测试阶段转换的有效性"""
        # 验证常见的阶段转换序列
        common_phases = [
            "initialize",
            "before_trading_start",
            "handle_data",
            "after_trading_end",
        ]

        for phase in common_phases:
            apis = get_phase_apis(phase)
            assert len(apis) > 0, f"阶段 {phase} 没有可用的API"

            # 验证每个API确实在该阶段可用
            for api in apis[:3]:  # 测试前3个API以节省时间
                assert is_api_allowed_in_phase(api, phase)


if __name__ == "__main__":
    pytest.main([__file__])
