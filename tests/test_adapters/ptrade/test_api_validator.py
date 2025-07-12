# -*- coding: utf-8 -*-
"""
api_validator.py 测试文件

测试PTrade API验证器
"""

from unittest.mock import MagicMock, patch

import pytest

from src.simtradelab.adapters.ptrade.api_validator import APIValidator
from src.simtradelab.adapters.ptrade.lifecycle_controller import PTradeLifecycleError


@pytest.mark.unit
class TestAPIValidator:
    """APIValidator单元测试"""

    def test_init(self):
        """测试初始化"""
        mock_controller = MagicMock()
        validator = APIValidator(mock_controller)

        assert validator._lifecycle_controller == mock_controller
        assert validator._validation_count == 0
        assert validator._validation_failures == 0
        assert validator._api_usage_stats == {}

    def test_validate_api_call_success(self):
        """测试API调用验证成功"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.return_value = True

        validator = APIValidator(mock_controller)

        result = validator.validate_api_call("get_price", "handle_data")

        assert result.is_valid is True
        assert result.error_message is None
        mock_controller.validate_api_call.assert_called_once_with("get_price")

        # 检查统计
        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == 1
        assert stats["validation_failures"] == 0
        assert stats["api_usage_stats"] == {"get_price": 1}

    def test_validate_api_call_failure(self):
        """测试API调用验证失败"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.side_effect = PTradeLifecycleError(
            "API not allowed"
        )

        validator = APIValidator(mock_controller)

        result = validator.validate_api_call("order", "initialize")

        assert result.is_valid is False
        assert "API not allowed" in result.error_message
        mock_controller.validate_api_call.assert_called_once_with("order")

        # 检查统计
        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == 1
        assert stats["validation_failures"] == 0  # lifecycle错误不计入failure
        assert stats["api_usage_stats"] == {}  # 失败的调用不计入使用统计

    def test_validate_api_call_with_args(self):
        """测试带参数的API调用验证"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.return_value = True

        validator = APIValidator(mock_controller)

        result = validator.validate_api_call("order", "000001.XSHE", 100, price=10.5)

        assert result.is_valid is True
        mock_controller.validate_api_call.assert_called_once_with("order")

    def test_validate_multiple_calls(self):
        """测试多次API调用验证"""
        mock_controller = MagicMock()

        # 设置不同的返回值
        def side_effect(api_name):
            if api_name == "get_price":
                return True
            elif api_name == "order":
                raise PTradeLifecycleError("Order not allowed in current phase")
            else:
                return True

        mock_controller.validate_api_call.side_effect = side_effect

        validator = APIValidator(mock_controller)

        # 成功的调用
        result1 = validator.validate_api_call("get_price")
        assert result1.is_valid is True

        result2 = validator.validate_api_call("get_history")
        assert result2.is_valid is True

        # 失败的调用
        result3 = validator.validate_api_call("order")
        assert result3.is_valid is False

        # 再一次成功的调用
        result4 = validator.validate_api_call("log")
        assert result4.is_valid is True

        # 检查统计
        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == 4
        assert stats["validation_failures"] == 0  # lifecycle错误不计入failure
        # 成功的API调用会计入使用统计
        assert "get_price" in stats["api_usage_stats"]
        assert "get_history" in stats["api_usage_stats"]
        assert "log" in stats["api_usage_stats"]
        assert "order" not in stats["api_usage_stats"]  # 失败的不计入

    def test_get_validation_statistics_structure(self):
        """测试验证统计结构"""
        mock_controller = MagicMock()
        validator = APIValidator(mock_controller)

        stats = validator.get_validation_statistics()

        # 验证统计结构
        required_keys = [
            "total_validations",
            "validation_failures",
            "success_rate",
            "api_usage_stats",
            "most_used_apis",
        ]
        for key in required_keys:
            assert key in stats

        assert isinstance(stats["total_validations"], int)
        assert isinstance(stats["validation_failures"], int)
        assert isinstance(stats["success_rate"], float)
        assert isinstance(stats["api_usage_stats"], dict)
        assert isinstance(stats["most_used_apis"], list)

    def test_reset_statistics(self):
        """测试重置统计"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.return_value = True

        validator = APIValidator(mock_controller)

        # 添加一些验证
        validator.validate_api_call("get_price")
        validator.validate_api_call("get_history")

        # 验证有统计数据
        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == 2
        assert len(stats["api_usage_stats"]) == 2

        # 重置统计
        validator.reset_statistics()

        # 验证统计被重置
        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == 0
        assert stats["validation_failures"] == 0
        assert len(stats["api_usage_stats"]) == 0

    def test_error_logging_details(self):
        """测试错误日志详情"""
        mock_controller = MagicMock()
        error_message = "Custom error message"
        mock_controller.validate_api_call.side_effect = PTradeLifecycleError(
            error_message
        )

        validator = APIValidator(mock_controller)

        result = validator.validate_api_call("order", "initialize")

        # 验证错误被正确处理
        assert result.is_valid is False
        assert error_message in result.error_message

    def test_validation_with_none_controller(self):
        """测试控制器为None的情况"""
        # 传入None时会使用全局控制器
        validator = APIValidator(None)

        # 应该能够正常初始化，不会抛出错误
        assert validator._lifecycle_controller is not None


@pytest.mark.integration
class TestAPIValidatorIntegration:
    """APIValidator集成测试"""

    def test_with_real_lifecycle_controller(self):
        """测试与真实生命周期控制器的集成"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import (
            LifecycleController,
        )

        controller = LifecycleController()
        validator = APIValidator(controller)

        # 设置为handle_data阶段
        from src.simtradelab.adapters.ptrade.lifecycle_controller import LifecyclePhase

        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        with patch(
            "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
        ) as mock_allowed:
            # 允许的API
            mock_allowed.return_value = True
            result = validator.validate_api_call("get_price")
            assert result.is_valid is True

            # 禁止的API
            mock_allowed.return_value = False
            result = validator.validate_api_call("set_universe")
            assert result.is_valid is False

    def test_validation_flow_in_strategy_execution(self):
        """测试在策略执行流程中的验证"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import (
            LifecycleController,
            LifecyclePhase,
        )

        controller = LifecycleController()
        validator = APIValidator(controller)

        # 模拟策略执行流程
        with patch(
            "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
        ) as mock_allowed:
            mock_allowed.return_value = True

            # 1. 初始化阶段
            controller.set_phase(LifecyclePhase.INITIALIZE)
            result1 = validator.validate_api_call("set_universe")
            assert result1.is_valid is True

            # 2. handle_data阶段
            controller.set_phase(LifecyclePhase.HANDLE_DATA)
            result2 = validator.validate_api_call("get_price")
            assert result2.is_valid is True
            result3 = validator.validate_api_call("order")
            assert result3.is_valid is True

            # 3. 检查统计
            stats = validator.get_validation_statistics()
            assert stats["total_validations"] == 3
            assert stats["validation_failures"] == 0

    def test_error_accumulation_over_time(self):
        """测试错误随时间积累"""
        from src.simtradelab.adapters.ptrade.lifecycle_controller import (
            LifecycleController,
            LifecyclePhase,
        )

        controller = LifecycleController()
        validator = APIValidator(controller)

        # 设置一个阶段以避免警告
        controller.set_phase(LifecyclePhase.INITIALIZE)
        controller.set_phase(LifecyclePhase.HANDLE_DATA)

        with patch(
            "src.simtradelab.adapters.ptrade.lifecycle_controller.is_api_allowed_in_phase"
        ) as mock_allowed:
            # 模拟一系列成功和失败的验证（使用不需要参数验证的API）
            test_cases = [
                ("get_price", True),
                ("get_price", False),  # 同API但生命周期验证失败
                ("get_history", True),
                ("log", False),
                ("log", True),
            ]

            successful_count = 0
            for api_name, should_succeed in test_cases:
                mock_allowed.return_value = should_succeed

                result = validator.validate_api_call(api_name)
                if should_succeed:
                    assert result.is_valid is True
                    successful_count += 1
                else:
                    assert result.is_valid is False

            # 验证最终统计
            stats = validator.get_validation_statistics()
            assert stats["total_validations"] == 5
            assert stats["validation_failures"] == 0  # lifecycle错误不计入failure
            # 只有成功的API调用会计入使用统计
            assert len(stats["api_usage_stats"]) <= successful_count  # 可能有重复的API


@pytest.mark.unit
class TestAPIValidatorEdgeCases:
    """测试边界情况"""

    def test_empty_api_name(self):
        """测试空API名称"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.return_value = True

        validator = APIValidator(mock_controller)

        # 空字符串
        validator.validate_api_call("")
        mock_controller.validate_api_call.assert_called_with("")

        # None值
        validator.validate_api_call(None)
        mock_controller.validate_api_call.assert_called_with(None)

    def test_very_long_api_name(self):
        """测试很长的API名称"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.return_value = True

        validator = APIValidator(mock_controller)

        long_api_name = "a" * 1000
        validator.validate_api_call(long_api_name)
        mock_controller.validate_api_call.assert_called_with(long_api_name)

    def test_special_characters_in_api_name(self):
        """测试API名称中的特殊字符"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.return_value = True

        validator = APIValidator(mock_controller)

        special_names = ["api-name", "api.name", "api_name_123", "API_NAME"]
        for name in special_names:
            validator.validate_api_call(name)
            mock_controller.validate_api_call.assert_called_with(name)

    def test_exception_in_lifecycle_controller(self):
        """测试生命周期控制器抛出异常"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.side_effect = Exception("Unexpected error")

        validator = APIValidator(mock_controller)

        # 应该捕获异常并返回验证成功结果（但带有警告）
        result = validator.validate_api_call("get_price")
        # APIValidator的实际实现中，非 PTradeLifecycleError 的异常会被视为警告
        assert result.is_valid is True
        assert len(result.warnings) > 0

        # 统计中不会记录为失败（因为最终返回的是成功）
        stats = validator.get_validation_statistics()
        assert stats["validation_failures"] == 0

    def test_maximum_error_accumulation(self):
        """测试错误积累的上限"""
        mock_controller = MagicMock()
        mock_controller.validate_api_call.side_effect = PTradeLifecycleError("Error")

        validator = APIValidator(mock_controller)

        # 生成大量错误
        error_count = 100
        for i in range(error_count):
            result = validator.validate_api_call(f"api_{i}")
            assert result.is_valid is False

        stats = validator.get_validation_statistics()
        assert stats["total_validations"] == error_count
        assert stats["validation_failures"] == 0  # lifecycle错误不计入failure
        assert len(stats["api_usage_stats"]) == 0  # 失败的不计入使用统计


if __name__ == "__main__":
    pytest.main([__file__])
