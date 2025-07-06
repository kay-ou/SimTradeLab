# -*- coding: utf-8 -*-
"""
日志记录器模块
"""
from datetime import datetime

class Logger:
    """模拟日志记录器，支持ptrade风格的时间戳格式"""
    LEVEL_INFO = "INFO"

    def __init__(self):
        self.current_dt = None

    def set_log_level(self, level):
        """设置日志级别"""
        pass

    def _format_timestamp(self):
        """格式化时间戳"""
        if self.current_dt:
            return self.current_dt.strftime("%Y-%m-%d %H:%M:%S")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def info(self, msg):
        """记录info级别日志"""
        timestamp = self._format_timestamp()
        print(f"{timestamp} - INFO - {msg}")

    def warning(self, msg):
        """记录warning级别日志"""
        timestamp = self._format_timestamp()
        print(f"{timestamp} - WARNING - {msg}")

    def error(self, msg):
        """记录error级别日志"""
        timestamp = self._format_timestamp()
        print(f"{timestamp} - ERROR - {msg}")

    def debug(self, msg):
        """记录debug级别日志"""
        timestamp = self._format_timestamp()
        print(f"{timestamp} - DEBUG - {msg}")
        
    def critical(self, msg):
        """记录critical级别日志"""
        timestamp = self._format_timestamp()
        print(f"{timestamp} - CRITICAL - {msg}")


# 全局日志实例
log = Logger()
