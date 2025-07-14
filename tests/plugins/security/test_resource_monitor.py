# -*- coding: utf-8 -*-
"""
ResourceMonitor 的单元测试
"""
import time
from unittest.mock import patch
from simtradelab.plugins.security.resource_monitor import ResourceMonitor

def test_resource_monitor_start_stop():
    """
    测试：资源监控器可以正确启动和停止。
    """
    monitor = ResourceMonitor(interval=1)
    assert not monitor._running
    
    monitor.start()
    assert monitor._running
    if monitor._monitor_thread:
        assert monitor._monitor_thread.is_alive()
    
    monitor.stop()
    assert not monitor._running
    # The thread might take a moment to join
    time.sleep(0.2)
    if monitor._monitor_thread:
        assert not monitor._monitor_thread.is_alive()

def test_get_usage_returns_empty_dict_for_unknown_plugin():
    """
    测试：对于未知的插件，get_usage 应返回一个空字典。
    """
    monitor = ResourceMonitor()
    assert monitor.get_usage("unknown_plugin") == {}
