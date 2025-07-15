# -*- coding: utf-8 -*-
"""
lifecycle_config.py 测试文件

测试PTrade API生命周期配置
"""

import pytest

from simtradelab.adapters.ptrade.lifecycle_config import (
    API_LIFECYCLE_RESTRICTIONS,
    EXCLUSIVE_PHASE_APIS,
    LIFECYCLE_PHASES,
    PHASE_API_COUNT,
    get_api_allowed_phases,
    get_phase_apis,
    is_api_allowed_in_phase,
    validate_config,
)


@pytest.mark.unit
class TestLifecycleConfig:
    """生命周期配置单元测试"""

    def test_api_lifecycle_restrictions_structure(self):
        """测试API_LIFECYCLE_RESTRICTIONS结构"""
        assert isinstance(API_LIFECYCLE_RESTRICTIONS, dict)
        for api, phases in API_LIFECYCLE_RESTRICTIONS.items():
            assert isinstance(api, str)
            assert isinstance(phases, list)
            for phase in phases:
                assert isinstance(phase, str)
                assert phase == "all" or phase in LIFECYCLE_PHASES

    def test_lifecycle_phases_structure(self):
        """测试LIFECYCLE_PHASES结构"""
        assert isinstance(LIFECYCLE_PHASES, list)
        assert all(isinstance(phase, str) for phase in LIFECYCLE_PHASES)

    def test_get_api_allowed_phases(self):
        """测试get_api_allowed_phases函数"""
        # 1. API在配置中，且不是'all'
        assert get_api_allowed_phases("set_universe") == ["initialize"]
        assert get_api_allowed_phases("order") == ["handle_data", "tick_data"]

        # 2. API在配置中，且是'all'
        all_phases_api = "get_positions"
        assert get_api_allowed_phases(all_phases_api) == LIFECYCLE_PHASES

        # 3. API不在配置中，应返回所有阶段
        unknown_api = "this_api_does_not_exist"
        assert get_api_allowed_phases(unknown_api) == LIFECYCLE_PHASES

    def test_is_api_allowed_in_phase(self):
        """测试is_api_allowed_in_phase函数"""
        # 1. 允许的场景
        assert is_api_allowed_in_phase("set_universe", "initialize") is True
        assert is_api_allowed_in_phase("order", "handle_data") is True
        assert is_api_allowed_in_phase("get_positions", "any_phase") is True

        # 2. 禁止的场景
        assert is_api_allowed_in_phase("set_universe", "handle_data") is False
        assert is_api_allowed_in_phase("order", "initialize") is False

        # 3. 未知API，应返回True（默认为'all'）
        assert is_api_allowed_in_phase("unknown_api_123", "any_phase") is True

    def test_get_phase_apis(self):
        """测试get_phase_apis函数"""
        # 1. 'initialize'阶段
        init_apis = get_phase_apis("initialize")
        assert "set_universe" in init_apis
        assert "order" not in init_apis
        assert "get_positions" in init_apis  # 'all' 应该包含在内

        # 2. 'handle_data'阶段
        handle_data_apis = get_phase_apis("handle_data")
        assert "order" in handle_data_apis
        assert "set_universe" not in handle_data_apis
        assert "get_positions" in handle_data_apis

        # 3. 未知阶段，应只返回'all'的API
        unknown_phase_apis = get_phase_apis("unknown_phase")
        assert all(
            API_LIFECYCLE_RESTRICTIONS.get(api) == ["all"] for api in unknown_phase_apis
        )

    def test_phase_api_count(self):
        """测试PHASE_API_COUNT结构"""
        assert isinstance(PHASE_API_COUNT, dict)
        for phase, count in PHASE_API_COUNT.items():
            assert phase in LIFECYCLE_PHASES
            assert isinstance(count, int)
            assert count == len(get_phase_apis(phase))

    def test_exclusive_phase_apis(self):
        """测试EXCLUSIVE_PHASE_APIS结构"""
        assert isinstance(EXCLUSIVE_PHASE_APIS, dict)
        for phase, apis in EXCLUSIVE_PHASE_APIS.items():
            assert phase in LIFECYCLE_PHASES
            assert isinstance(apis, list)
            for api in apis:
                assert API_LIFECYCLE_RESTRICTIONS[api] == [phase]

    def test_validate_config(self):
        """测试validate_config函数"""
        # 正常情况，不应抛出异常
        assert validate_config() is True

        # 模拟错误配置
        original_config = API_LIFECYCLE_RESTRICTIONS.copy()
        try:
            # 错误1: 引用未定义的阶段
            API_LIFECYCLE_RESTRICTIONS["test_api_1"] = ["undefined_phase"]
            with pytest.raises(ValueError, match="undefined phase"):
                validate_config()

            # 错误2: 关键API缺失
            API_LIFECYCLE_RESTRICTIONS.pop("order", None)
            with pytest.raises(ValueError, match="not configured"):
                validate_config()

        finally:
            # 恢复原始配置
            API_LIFECYCLE_RESTRICTIONS.clear()
            API_LIFECYCLE_RESTRICTIONS.update(original_config)
            validate_config()  # 确保恢复成功

    def test_all_phases_apis_logic(self):
        """测试'all'阶段API的逻辑"""
        from simtradelab.adapters.ptrade.lifecycle_config import ALL_PHASES_APIS

        for api in ALL_PHASES_APIS:
            assert API_LIFECYCLE_RESTRICTIONS[api] == ["all"]
            for phase in LIFECYCLE_PHASES:
                assert is_api_allowed_in_phase(api, phase) is True

    def test_edge_cases(self):
        """测试边界情况"""
        # 1. 空API名称
        # is_api_allowed_in_phase(None, "handle_data") 应该返回 True
        assert is_api_allowed_in_phase("non_existent_api", "handle_data") is True

        # 2. 空阶段名称
        assert is_api_allowed_in_phase("order", "") is False

        # 3. API名称和阶段名称都为空
        assert is_api_allowed_in_phase("", "") is False

    def test_get_api_allowed_phases_edge_cases(self):
        """测试get_api_allowed_phases的边界情况"""
        # 1. 未知API应该返回所有阶段（默认为'all'）
        from simtradelab.adapters.ptrade.lifecycle_config import LIFECYCLE_PHASES

        assert set(get_api_allowed_phases("non_existent_api")) == set(LIFECYCLE_PHASES)

        # 2. 空API名称应该返回所有阶段
        assert set(get_api_allowed_phases("")) == set(LIFECYCLE_PHASES)

        # 3. 测试None作为API名称
        assert set(get_api_allowed_phases("non_existent_api")) == set(LIFECYCLE_PHASES)

    def test_empty_api_name(self):
        """测试空API名称"""
        from simtradelab.adapters.ptrade.lifecycle_config import LIFECYCLE_PHASES

        # 未知API应该返回所有阶段（默认为'all'）
        assert set(get_api_allowed_phases("")) == set(LIFECYCLE_PHASES)

        # 测试None作为API名称
        # Pylance Error: 无法将“None”类型的参数分配给函数“get_api_allowed_phases”中类型为“str”的参数“api_name”
        assert set(get_api_allowed_phases("non_existent_api")) == set(LIFECYCLE_PHASES)


if __name__ == "__main__":
    pytest.main([__file__])
