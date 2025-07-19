# -*- coding: utf-8 -*-
"""
PTrade异常类测试

测试PTrade适配器相关异常的功能
"""

import pytest

from simtradelab.adapters.ptrade.utils.exceptions import (
    PTradeAdapterError,
    PTradeAPIError,
    PTradeCompatibilityError,
)
from simtradelab.exceptions import SimTradeLabException as SimTradeLabError


class TestPTradeAdapterError:
    """测试PTrade适配器异常"""

    def test_inheritance(self):
        """测试继承关系"""
        assert issubclass(PTradeAdapterError, SimTradeLabError)

    def test_basic_creation(self):
        """测试基本创建"""
        error = PTradeAdapterError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, SimTradeLabError)

    def test_creation_without_message(self):
        """测试无消息创建"""
        error = PTradeAdapterError()
        assert isinstance(error, PTradeAdapterError)

    def test_creation_with_args(self):
        """测试带参数创建"""
        error = PTradeAdapterError("Message", 123, "extra")
        assert str(error) == "('Message', 123, 'extra')"

    def test_raise_and_catch(self):
        """测试抛出和捕获"""
        with pytest.raises(PTradeAdapterError, match="Test error"):
            raise PTradeAdapterError("Test error")

    def test_catch_as_base_exception(self):
        """测试作为基类异常捕获"""
        with pytest.raises(SimTradeLabError):
            raise PTradeAdapterError("Base catch test")

    def test_error_attributes(self):
        """测试异常属性"""
        message = "Detailed error message"
        error = PTradeAdapterError(message)

        assert hasattr(error, "args")
        assert error.args[0] == message


class TestPTradeCompatibilityError:
    """测试PTrade兼容性异常"""

    def test_inheritance(self):
        """测试继承关系"""
        assert issubclass(PTradeCompatibilityError, PTradeAdapterError)
        assert issubclass(PTradeCompatibilityError, SimTradeLabError)

    def test_basic_creation(self):
        """测试基本创建"""
        error = PTradeCompatibilityError("Compatibility issue")
        assert str(error) == "Compatibility issue"
        assert isinstance(error, PTradeAdapterError)

    def test_specific_use_case(self):
        """测试具体使用场景"""

        # 模拟版本不兼容的情况
        def check_ptrade_version(version):
            if version < "2.0":
                raise PTradeCompatibilityError(
                    f"PTrade version {version} is not supported. "
                    "Please upgrade to version 2.0 or higher."
                )

        with pytest.raises(
            PTradeCompatibilityError, match="version 1.5 is not supported"
        ):
            check_ptrade_version("1.5")

    def test_raise_and_catch_specific(self):
        """测试特定异常捕获"""
        with pytest.raises(PTradeCompatibilityError):
            raise PTradeCompatibilityError("API not compatible")

    def test_catch_as_parent_exception(self):
        """测试作为父类异常捕获"""
        with pytest.raises(PTradeAdapterError):
            raise PTradeCompatibilityError("Parent catch test")


class TestPTradeAPIError:
    """测试PTrade API异常"""

    def test_inheritance(self):
        """测试继承关系"""
        assert issubclass(PTradeAPIError, PTradeAdapterError)
        assert issubclass(PTradeAPIError, SimTradeLabError)

    def test_basic_creation(self):
        """测试基本创建"""
        error = PTradeAPIError("API call failed")
        assert str(error) == "API call failed"
        assert isinstance(error, PTradeAdapterError)

    def test_api_error_scenarios(self):
        """测试API错误场景"""

        # 模拟网络错误
        def simulate_network_error():
            raise PTradeAPIError("Network connection timeout")

        with pytest.raises(PTradeAPIError, match="Network connection timeout"):
            simulate_network_error()

        # 模拟认证错误
        def simulate_auth_error():
            raise PTradeAPIError("Authentication failed: Invalid credentials")

        with pytest.raises(PTradeAPIError, match="Authentication failed"):
            simulate_auth_error()

        # 模拟数据错误
        def simulate_data_error():
            raise PTradeAPIError("Invalid data format in API response")

        with pytest.raises(PTradeAPIError, match="Invalid data format"):
            simulate_data_error()

    def test_error_chaining(self):
        """测试异常链接"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise PTradeAPIError("API wrapper error") from e
        except PTradeAPIError as api_error:
            assert api_error.__cause__ is not None
            assert isinstance(api_error.__cause__, ValueError)
            assert str(api_error.__cause__) == "Original error"

    def test_error_with_context_info(self):
        """测试带上下文信息的错误"""

        def api_call_with_context(endpoint, params):
            error_msg = (
                f"API call to '{endpoint}' failed. "
                f"Parameters: {params}. "
                f"Please check your request and try again."
            )
            raise PTradeAPIError(error_msg)

        with pytest.raises(PTradeAPIError) as exc_info:
            api_call_with_context("/api/v1/orders", {"symbol": "000001.XSHE"})

        error_msg = str(exc_info.value)
        assert "/api/v1/orders" in error_msg
        assert "000001.XSHE" in error_msg
        assert "Please check your request" in error_msg


class TestExceptionInteraction:
    """测试异常交互"""

    def test_exception_hierarchy(self):
        """测试异常层次结构"""
        # 创建异常实例
        base_error = PTradeAdapterError("Base error")
        compat_error = PTradeCompatibilityError("Compatibility error")
        api_error = PTradeAPIError("API error")

        # 测试isinstance关系
        assert isinstance(compat_error, PTradeAdapterError)
        assert isinstance(api_error, PTradeAdapterError)
        assert isinstance(base_error, SimTradeLabError)
        assert isinstance(compat_error, SimTradeLabError)
        assert isinstance(api_error, SimTradeLabError)

        # 测试不是彼此的实例
        assert not isinstance(compat_error, PTradeAPIError)
        assert not isinstance(api_error, PTradeCompatibilityError)

    def test_multiple_exception_catching(self):
        """测试多重异常捕获"""

        def raise_various_errors(error_type):
            if error_type == "base":
                raise PTradeAdapterError("Base error")
            elif error_type == "compat":
                raise PTradeCompatibilityError("Compatibility error")
            elif error_type == "api":
                raise PTradeAPIError("API error")

        # 捕获所有PTrade异常
        for error_type in ["base", "compat", "api"]:
            with pytest.raises(PTradeAdapterError):
                raise_various_errors(error_type)

        # 分别捕获特定异常
        with pytest.raises(PTradeCompatibilityError):
            raise_various_errors("compat")

        with pytest.raises(PTradeAPIError):
            raise_various_errors("api")

    def test_exception_message_preservation(self):
        """测试异常消息保持"""
        original_msg = "Original error message with details"

        # 测试消息在继承链中保持不变
        base_error = PTradeAdapterError(original_msg)
        compat_error = PTradeCompatibilityError(original_msg)
        api_error = PTradeAPIError(original_msg)

        assert str(base_error) == original_msg
        assert str(compat_error) == original_msg
        assert str(api_error) == original_msg

    def test_exception_nesting(self):
        """测试异常嵌套"""

        def level_3():
            raise PTradeAPIError("Level 3: API call failed")

        def level_2():
            try:
                level_3()
            except PTradeAPIError as e:
                raise PTradeCompatibilityError("Level 2: Compatibility issue") from e

        def level_1():
            try:
                level_2()
            except PTradeCompatibilityError as e:
                raise PTradeAdapterError("Level 1: Adapter error") from e

        with pytest.raises(PTradeAdapterError) as exc_info:
            level_1()

        # 检查异常链
        error = exc_info.value
        assert str(error) == "Level 1: Adapter error"
        assert isinstance(error.__cause__, PTradeCompatibilityError)
        assert str(error.__cause__) == "Level 2: Compatibility issue"
        assert isinstance(error.__cause__.__cause__, PTradeAPIError)
        assert str(error.__cause__.__cause__) == "Level 3: API call failed"

    def test_error_code_patterns(self):
        """测试错误代码模式"""

        # 模拟带错误代码的异常
        def create_coded_error(error_type, code, message):
            full_message = f"[{code}] {message}"
            if error_type == "api":
                return PTradeAPIError(full_message)
            elif error_type == "compat":
                return PTradeCompatibilityError(full_message)
            else:
                return PTradeAdapterError(full_message)

        api_error = create_coded_error("api", "API001", "Authentication failed")
        compat_error = create_coded_error("compat", "COMPAT001", "Version mismatch")

        assert "[API001]" in str(api_error)
        assert "Authentication failed" in str(api_error)
        assert "[COMPAT001]" in str(compat_error)
        assert "Version mismatch" in str(compat_error)

    def test_exception_reraising(self):
        """测试异常重新抛出"""

        def process_with_reraise():
            try:
                raise PTradeAPIError("Original API error")
            except PTradeAPIError:
                # 添加上下文后重新抛出
                raise PTradeCompatibilityError("Wrapped with compatibility context")

        # 原始异常应该被新异常替换
        with pytest.raises(
            PTradeCompatibilityError, match="Wrapped with compatibility"
        ):
            process_with_reraise()

    def test_exception_equality(self):
        """测试异常相等性"""
        error1 = PTradeAPIError("Same message")
        error2 = PTradeAPIError("Same message")
        error3 = PTradeAPIError("Different message")

        # 异常实例不应该相等（即使消息相同）
        assert error1 is not error2
        assert error1 is not error3

        # 但是消息应该相等
        assert str(error1) == str(error2)
        assert str(error1) != str(error3)
