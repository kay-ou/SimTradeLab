# -*- coding: utf-8 -*-
"""
lifecycle_controller.py 测试文件

测试PTrade API生命周期控制器
"""

from unittest.mock import MagicMock, patch

import pytest

from src.simtradelab.adapters.ptrade.lifecycle_controller import (
    LifecycleController,
    PTradeLifecycleError,
)


@pytest.mark.unit
class TestLifecycleController:
    """LifecycleController单元测试"""

    def test_init_default_phase(self):
        """测试默认初始化"""
        controller = LifecycleController()
        assert controller.current_phase is None
        assert controller._strategy_mode == "backtest"
        assert controller._call_history == []
        assert controller._api_call_count == {}

    def test_set_phase(self):
        """测试设置生命周期阶段"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()

        # 首先设置初始化阶段（从None开始只能设置INITIALIZE）
        controller.set_phase(LifecyclePhase.INITIALIZE)
        assert controller.current_phase == LifecyclePhase.INITIALIZE

        # 从INITIALIZE可以转换到HANDLE_DATA
        controller.set_phase(LifecyclePhase.HANDLE_DATA)
        assert controller.current_phase == LifecyclePhase.HANDLE_DATA

    def test_get_current_phase(self):
        """测试获取当前阶段"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()
        assert controller.current_phase is None

        # 设置初始化阶段
        controller.set_phase(LifecyclePhase.INITIALIZE)
        assert controller.current_phase == LifecyclePhase.INITIALIZE

        # 转换到handle_data
        controller.set_phase(LifecyclePhase.HANDLE_DATA)
        assert controller.current_phase == LifecyclePhase.HANDLE_DATA

    def test_phase_executed_tracking(self):
        """测试阶段执行追踪"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()

        # 初始状态没有执行过任何阶段
        assert not controller.is_phase_executed(LifecyclePhase.INITIALIZE)

        # 设置阶段后应该标记为已执行
        controller.set_phase(LifecyclePhase.INITIALIZE)
        assert controller.is_phase_executed(LifecyclePhase.INITIALIZE)

        controller.set_phase(LifecyclePhase.HANDLE_DATA)
        assert controller.is_phase_executed(LifecyclePhase.HANDLE_DATA)
        assert controller.is_phase_executed(LifecyclePhase.INITIALIZE)  # 仍然记录

    def test_current_phase_name(self):
        """测试当前阶段名称属性"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()
        assert controller.current_phase_name is None

        controller.set_phase(LifecyclePhase.INITIALIZE)
        assert controller.current_phase_name == "initialize"

        controller.set_phase(LifecyclePhase.HANDLE_DATA)
        assert controller.current_phase_name == "handle_data"

    @patch(
        "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
    )
    def test_validate_api_call_allowed(self, mock_is_allowed):
        """测试API调用验证 - 允许的情况"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        mock_is_allowed.return_value = True

        controller = LifecycleController()
        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 允许的API调用应该返回True
        result = controller.validate_api_call("order")
        assert result is True

        mock_is_allowed.assert_called_once_with("order", "handle_data")

    @patch(
        "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
    )
    def test_validate_api_call_forbidden(self, mock_is_allowed):
        """测试API调用验证 - 禁止的情况"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        mock_is_allowed.return_value = False

        controller = LifecycleController()
        controller.set_phase(LifecyclePhase.INITIALIZE)

        # 禁止的API调用应该抛出异常
        with pytest.raises(
            PTradeLifecycleError,
            match="API 'order' cannot be called in phase 'initialize'",
        ):
            controller.validate_api_call("order")

        mock_is_allowed.assert_called_once_with("order", "initialize")

    def test_record_api_call(self):
        """测试API调用记录"""
        controller = LifecycleController()

        # 记录多个API调用
        controller.record_api_call("get_price", True)
        controller.record_api_call("order", False, error="Order failed")
        controller.record_api_call("get_price", True)  # 重复调用

        # 检查统计
        stats = controller.get_call_statistics()
        assert stats["api_call_count"] == {"get_price": 2, "order": 1}
        assert stats["total_api_calls"] == 3
        assert stats["failed_calls"] == 1

    def test_get_call_statistics(self):
        """测试获取调用统计"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()

        # 初始统计
        stats = controller.get_call_statistics()
        assert stats["current_phase"] is None
        assert stats["total_api_calls"] == 0
        assert stats["api_call_count"] == {}

        # 添加一些调用
        controller.record_api_call("get_price", True)
        controller.record_api_call("order", True)
        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        stats = controller.get_call_statistics()
        assert stats["current_phase"] == "handle_data"
        assert stats["total_api_calls"] == 2
        assert stats["api_call_count"] == {"get_price": 1, "order": 1}

    def test_reset(self):
        """测试重置控制器"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()

        # 添加一些调用和状态
        controller.record_api_call("get_price", True)
        # 正确的阶段转换顺序
        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 重置前的状态
        assert controller._api_call_count == {"get_price": 1}
        assert controller.current_phase == LifecyclePhase.HANDLE_DATA

        # 重置
        controller.reset()

        # 重置后的状态
        assert controller._api_call_count == {}
        assert controller.current_phase is None
        assert controller._call_history == []


@pytest.mark.integration
class TestLifecycleControllerIntegration:
    """LifecycleController集成测试"""

    def test_complete_lifecycle_flow(self):
        """测试完整的生命周期流程"""
        controller = LifecycleController()

        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        # 1. 初始化阶段
        assert controller.current_phase is None

        # 设置初始化阶段
        controller.set_phase(LifecyclePhase.INITIALIZE)

        # 在初始化阶段，只能调用特定API
        with patch(
            "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
        ) as mock_allowed:
            mock_allowed.return_value = True
            controller.validate_api_call("set_universe")
            controller.record_api_call("set_universe", True)
            mock_allowed.assert_called_with("set_universe", "initialize")

        # 2. 切换到handle_data阶段
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 在handle_data阶段可以调用交易API
        with patch(
            "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
        ) as mock_allowed:
            mock_allowed.return_value = True
            controller.validate_api_call("order")
            controller.validate_api_call("get_price")
            controller.record_api_call("order", True)
            controller.record_api_call("get_price", True)

        # 3. 检查统计
        stats = controller.get_call_statistics()
        assert stats["current_phase"] == "handle_data"
        assert stats["total_api_calls"] == 3  # set_universe + order + get_price

    def test_register_phase_callback(self):
        """测试阶段回调注册"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()

        # 注册回调
        callback_called = []

        def test_callback():
            callback_called.append("called")

        controller.register_phase_callback(LifecyclePhase.HANDLE_DATA, test_callback)

        # 首先设置初始化阶段
        controller.set_phase(LifecyclePhase.INITIALIZE)
        assert len(callback_called) == 0  # 初始化阶段不应该触发HANDLE_DATA回调

        # 设置HANDLE_DATA阶段应该触发回调
        controller.set_phase(LifecyclePhase.HANDLE_DATA)
        assert len(callback_called) == 1

    def test_get_recent_calls(self):
        """测试获取最近调用记录"""
        controller = LifecycleController()

        # 记录一些API调用
        controller.record_api_call("get_price", True)
        controller.record_api_call("order", False, error="Failed")
        controller.record_api_call("get_history", True)

        # 获取最近调用记录
        recent_calls = controller.get_recent_calls(limit=2)

        assert len(recent_calls) == 2
        assert recent_calls[-1].api_name == "get_history"  # 最后一个
        assert recent_calls[-2].api_name == "order"  # 倒数第二个


@pytest.mark.unit
class TestLifecycleControllerErrorHandling:
    """测试错误处理"""

    def test_get_phase_apis(self):
        """测试获取阶段可用API"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()
        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        with patch(
            "src.simtradelab.adapters.ptrade.lifecycle_config.get_phase_apis"
        ) as mock_get_apis:
            mock_get_apis.return_value = ["get_price", "order", "get_history"]

            apis = controller.get_phase_apis()
            assert apis == ["get_price", "order", "get_history"]
            mock_get_apis.assert_called_once_with("handle_data")

    def test_validate_without_phase_set(self):
        """测试没有设置阶段时的验证"""
        controller = LifecycleController()

        # 没有设置阶段时应该允许调用（向后兼容）
        result = controller.validate_api_call("get_price")
        assert result is True

    def test_phase_transition_validation(self):
        """测试阶段转换验证"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller = LifecycleController()

        # 有效的转换序列
        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        # 无效的转换应该抛出异常
        # 从HANDLE_DATA不能直接转换到INITIALIZE
        with pytest.raises(PTradeLifecycleError):
            controller._validate_phase_transition(
                LifecyclePhase.HANDLE_DATA, LifecyclePhase.INITIALIZE
            )


if __name__ == "__main__":
    pytest.main([__file__])
