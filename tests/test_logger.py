# -*- coding: utf-8 -*-
"""
Logger模块测试

测试日志记录器的功能
"""

import io
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

from simtradelab.logger import Logger, log


class TestLogger:
    """测试Logger类"""

    @pytest.fixture
    def logger(self):
        """创建Logger实例"""
        return Logger()

    @pytest.fixture
    def capture_output(self):
        """捕获标准输出"""
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            yield captured_output

    def test_logger_initialization(self, logger):
        """测试Logger初始化"""
        assert logger.current_dt is None
        assert hasattr(logger, "LEVEL_INFO")
        assert logger.LEVEL_INFO == "INFO"

    def test_logger_constants(self):
        """测试Logger常量"""
        assert Logger.LEVEL_INFO == "INFO"

    def test_set_log_level(self, logger):
        """测试设置日志级别"""
        # 当前是空实现，主要测试不抛出异常
        logger.set_log_level("DEBUG")
        logger.set_log_level("INFO")
        logger.set_log_level("WARNING")
        logger.set_log_level("ERROR")
        logger.set_log_level("CRITICAL")

    def test_format_timestamp_without_current_dt(self, logger):
        """测试无当前时间时的时间戳格式化"""
        timestamp = logger._format_timestamp()

        # 验证时间戳格式
        assert isinstance(timestamp, str)
        # 验证格式：YYYY-MM-DD HH:MM:SS
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

    def test_format_timestamp_with_current_dt(self, logger):
        """测试有当前时间时的时间戳格式化"""
        test_time = datetime(2023, 12, 29, 14, 30, 45)
        logger.current_dt = test_time

        timestamp = logger._format_timestamp()
        assert timestamp == "2023-12-29 14:30:45"

    def test_info_logging(self, logger, capture_output):
        """测试info级别日志"""
        test_message = "This is an info message"
        logger.info(test_message)

        output = capture_output.getvalue()
        assert "INFO" in output
        assert test_message in output
        assert len(output.strip()) > 0

    def test_warning_logging(self, logger, capture_output):
        """测试warning级别日志"""
        test_message = "This is a warning message"
        logger.warning(test_message)

        output = capture_output.getvalue()
        assert "WARNING" in output
        assert test_message in output

    def test_error_logging(self, logger, capture_output):
        """测试error级别日志"""
        test_message = "This is an error message"
        logger.error(test_message)

        output = capture_output.getvalue()
        assert "ERROR" in output
        assert test_message in output

    def test_debug_logging(self, logger, capture_output):
        """测试debug级别日志"""
        test_message = "This is a debug message"
        logger.debug(test_message)

        output = capture_output.getvalue()
        assert "DEBUG" in output
        assert test_message in output

    def test_critical_logging(self, logger, capture_output):
        """测试critical级别日志"""
        test_message = "This is a critical message"
        logger.critical(test_message)

        output = capture_output.getvalue()
        assert "CRITICAL" in output
        assert test_message in output

    def test_log_output_format(self, logger, capture_output):
        """测试日志输出格式"""
        test_time = datetime(2023, 12, 29, 14, 30, 45)
        logger.current_dt = test_time

        test_message = "Test format message"
        logger.info(test_message)

        output = capture_output.getvalue().strip()
        expected_format = "2023-12-29 14:30:45 - INFO - Test format message"
        assert output == expected_format

    def test_multiple_log_levels(self, logger, capture_output):
        """测试多个日志级别"""
        messages = [
            ("info", "Info message"),
            ("warning", "Warning message"),
            ("error", "Error message"),
            ("debug", "Debug message"),
            ("critical", "Critical message"),
        ]

        for level, message in messages:
            getattr(logger, level)(message)

        output = capture_output.getvalue()

        # 验证所有级别和消息都在输出中
        for level, message in messages:
            assert level.upper() in output
            assert message in output

    def test_timestamp_consistency(self, logger):
        """测试时间戳一致性"""
        test_time = datetime(2023, 12, 29, 14, 30, 45)
        logger.current_dt = test_time

        # 多次调用应该返回相同的时间戳
        timestamp1 = logger._format_timestamp()
        timestamp2 = logger._format_timestamp()

        assert timestamp1 == timestamp2
        assert timestamp1 == "2023-12-29 14:30:45"

    def test_current_dt_modification(self, logger):
        """测试current_dt修改"""
        # 初始为None
        assert logger.current_dt is None

        # 设置时间
        test_time = datetime(2023, 6, 15, 10, 20, 30)
        logger.current_dt = test_time
        assert logger.current_dt == test_time

        # 重置为None
        logger.current_dt = None
        assert logger.current_dt is None

    def test_unicode_message_support(self, logger, capture_output):
        """测试Unicode消息支持"""
        unicode_message = "测试中文消息 🚀"
        logger.info(unicode_message)

        output = capture_output.getvalue()
        assert unicode_message in output
        assert "INFO" in output

    def test_empty_message(self, logger, capture_output):
        """测试空消息"""
        logger.info("")

        output = capture_output.getvalue()
        assert "INFO" in output
        # 应该包含时间戳和级别，即使消息为空

    def test_long_message(self, logger, capture_output):
        """测试长消息"""
        long_message = "A" * 1000  # 1000个字符的长消息
        logger.info(long_message)

        output = capture_output.getvalue()
        assert long_message in output
        assert "INFO" in output

    def test_logger_methods_existence(self, logger):
        """测试Logger方法存在性"""
        required_methods = [
            "info",
            "warning",
            "error",
            "debug",
            "critical",
            "set_log_level",
        ]

        for method_name in required_methods:
            assert hasattr(logger, method_name)
            assert callable(getattr(logger, method_name))


class TestGlobalLogInstance:
    """测试全局日志实例"""

    @pytest.fixture
    def capture_output(self):
        """捕获标准输出"""
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            yield captured_output

    def test_global_log_instance_exists(self):
        """测试全局日志实例存在"""
        assert log is not None
        assert isinstance(log, Logger)

    def test_global_log_instance_functionality(self, capture_output):
        """测试全局日志实例功能"""
        test_message = "Global log test message"
        log.info(test_message)

        output = capture_output.getvalue()
        assert test_message in output
        assert "INFO" in output

    def test_global_log_all_levels(self, capture_output):
        """测试全局日志所有级别"""
        messages = {
            "info": "Global info test",
            "warning": "Global warning test",
            "error": "Global error test",
            "debug": "Global debug test",
            "critical": "Global critical test",
        }

        for level, message in messages.items():
            getattr(log, level)(message)

        output = capture_output.getvalue()

        for level, message in messages.items():
            assert message in output
            assert level.upper() in output
