# -*- coding: utf-8 -*-
"""
Logger模块测试
完整测试日志记录器功能
"""

import sys
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest

from simtradelab.logger import Logger, log


class TestLogger:
    """测试Logger类"""

    def test_logger_creation(self):
        """测试日志记录器创建"""
        logger = Logger()

        assert logger.current_dt is None
        assert logger.LEVEL_INFO == "INFO"

    def test_set_log_level(self):
        """测试设置日志级别"""
        logger = Logger()

        # 测试设置日志级别（虽然当前实现是空的）
        logger.set_log_level("DEBUG")
        # 应该不抛出异常

    def test_format_timestamp_default(self):
        """测试默认时间戳格式化"""
        logger = Logger()

        # 没有设置current_dt时，应该使用当前时间
        timestamp = logger._format_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) == 19  # YYYY-MM-DD HH:MM:SS

    def test_format_timestamp_with_current_dt(self):
        """测试使用current_dt的时间戳格式化"""
        logger = Logger()
        test_dt = datetime(2023, 1, 1, 12, 30, 45)
        logger.current_dt = test_dt

        timestamp = logger._format_timestamp()
        assert timestamp == "2023-01-01 12:30:45"

    @patch("sys.stdout", new_callable=StringIO)
    def test_info_logging(self, mock_stdout):
        """测试info级别日志"""
        logger = Logger()
        logger.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        logger.info("Test info message")

        output = mock_stdout.getvalue()
        assert "2023-01-01 12:30:45 - INFO - Test info message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_warning_logging(self, mock_stdout):
        """测试warning级别日志"""
        logger = Logger()
        logger.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        logger.warning("Test warning message")

        output = mock_stdout.getvalue()
        assert "2023-01-01 12:30:45 - WARNING - Test warning message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_error_logging(self, mock_stdout):
        """测试error级别日志"""
        logger = Logger()
        logger.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        logger.error("Test error message")

        output = mock_stdout.getvalue()
        assert "2023-01-01 12:30:45 - ERROR - Test error message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_debug_logging(self, mock_stdout):
        """测试debug级别日志"""
        logger = Logger()
        logger.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        logger.debug("Test debug message")

        output = mock_stdout.getvalue()
        assert "2023-01-01 12:30:45 - DEBUG - Test debug message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_critical_logging(self, mock_stdout):
        """测试critical级别日志"""
        logger = Logger()
        logger.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        logger.critical("Test critical message")

        output = mock_stdout.getvalue()
        assert "2023-01-01 12:30:45 - CRITICAL - Test critical message" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_logging_without_current_dt(self, mock_stdout):
        """测试没有设置current_dt时的日志记录"""
        logger = Logger()

        # 不设置current_dt，使用默认的datetime.now()
        logger.info("Test message")

        output = mock_stdout.getvalue()
        # 应该包含时间戳和消息
        assert "INFO - Test message" in output
        assert len(output) > 0

    def test_global_log_instance(self):
        """测试全局日志实例"""
        assert isinstance(log, Logger)
        assert log.current_dt is None

    @patch("sys.stdout", new_callable=StringIO)
    def test_global_log_usage(self, mock_stdout):
        """测试全局日志实例的使用"""
        log.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        log.info("Global log test")

        output = mock_stdout.getvalue()
        assert "2023-01-01 12:30:45 - INFO - Global log test" in output

    def test_multiple_log_levels(self):
        """测试多个日志级别"""
        logger = Logger()
        logger.current_dt = datetime(2023, 1, 1, 12, 30, 45)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.debug("Debug message")
            logger.critical("Critical message")

            output = mock_stdout.getvalue()
            assert "INFO - Info message" in output
            assert "WARNING - Warning message" in output
            assert "ERROR - Error message" in output
            assert "DEBUG - Debug message" in output
            assert "CRITICAL - Critical message" in output

    def test_logger_level_constant(self):
        """测试日志级别常量"""
        logger = Logger()

        assert hasattr(logger, "LEVEL_INFO")
        assert logger.LEVEL_INFO == "INFO"
