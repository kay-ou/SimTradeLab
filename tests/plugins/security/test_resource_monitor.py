# -*- coding: utf-8 -*-
"""
ResourceMonitor 测试用例
"""

import time
import threading
from unittest.mock import patch, MagicMock

import pytest

from simtradelab.plugins.security.resource_monitor import ResourceMonitor


class TestResourceMonitor:
    """测试资源监控器"""
    
    def test_resource_monitor_initialization(self):
        """测试资源监控器初始化"""
        monitor = ResourceMonitor()
        
        assert monitor._interval == 60
        assert monitor._running is False
        assert monitor._monitor_thread is None
        assert monitor._plugin_usage == {}
    
    def test_resource_monitor_custom_interval(self):
        """测试自定义间隔初始化"""
        monitor = ResourceMonitor(interval=30)
        
        assert monitor._interval == 30
        assert monitor._running is False
    
    def test_resource_monitor_start_stop(self):
        """测试启动和停止监控器"""
        monitor = ResourceMonitor(interval=1)
        
        # 测试启动
        monitor.start()
        assert monitor._running is True
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()
        
        # 测试重复启动（应该无效）
        original_thread = monitor._monitor_thread
        monitor.start()
        assert monitor._monitor_thread is original_thread
        
        # 测试停止
        monitor.stop()
        assert monitor._running is False
        # 线程应该结束
        original_thread.join(timeout=2)
        assert not original_thread.is_alive()
    
    def test_resource_monitor_stop_without_start(self):
        """测试在未启动情况下停止"""
        monitor = ResourceMonitor()
        
        # 应该能正常停止而不出错
        monitor.stop()
        assert monitor._running is False
    
    def test_get_usage_empty(self):
        """测试获取空插件使用情况"""
        monitor = ResourceMonitor()
        
        usage = monitor.get_usage("nonexistent_plugin")
        assert usage == {}
    
    def test_get_usage_with_data(self):
        """测试获取有数据的插件使用情况"""
        monitor = ResourceMonitor()
        
        # 模拟插件使用数据
        test_usage = {"cpu": 25.5, "memory": 1024}
        monitor._plugin_usage["test_plugin"] = test_usage
        
        usage = monitor.get_usage("test_plugin")
        assert usage == test_usage
    
    @patch('time.sleep')
    def test_monitor_loop_execution(self, mock_sleep):
        """测试监控循环执行"""
        monitor = ResourceMonitor(interval=1)
        
        # 模拟监控循环运行一段时间后停止
        def stop_after_delay():
            time.sleep(0.1)  # 真实的短暂睡眠
            monitor._running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        # 启动监控器
        monitor.start()
        
        # 等待停止
        stop_thread.join()
        monitor.stop()
        
        # 验证sleep被调用
        mock_sleep.assert_called_with(1)
        
    @patch('simtradelab.plugins.security.resource_monitor.time.sleep')
    def test_monitor_loop_interval_usage(self, mock_sleep):
        """测试监控循环使用正确的间隔"""
        monitor = ResourceMonitor(interval=5)
        
        # 模拟监控循环运行一段时间后停止
        def stop_after_delay():
            time.sleep(0.1)  # 真实的短暂睡眠
            monitor._running = False
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        # 启动监控器
        monitor.start()
        
        # 等待停止
        stop_thread.join()
        monitor.stop()
        
        # 验证sleep被调用时使用了正确的间隔
        mock_sleep.assert_called_with(5)
    
    def test_monitor_multiple_plugins(self):
        """测试监控多个插件"""
        monitor = ResourceMonitor()
        
        # 设置多个插件的使用数据
        plugin_data = {
            "plugin1": {"cpu": 10.0, "memory": 512},
            "plugin2": {"cpu": 20.0, "memory": 1024},
            "plugin3": {"cpu": 15.0, "memory": 768}
        }
        
        for plugin_name, usage in plugin_data.items():
            monitor._plugin_usage[plugin_name] = usage
        
        # 验证每个插件的数据都能正确获取
        for plugin_name, expected_usage in plugin_data.items():
            actual_usage = monitor.get_usage(plugin_name)
            assert actual_usage == expected_usage
    
    def test_monitor_thread_daemon_property(self):
        """测试监控线程的daemon属性"""
        monitor = ResourceMonitor()
        
        monitor.start()
        
        # 验证线程是daemon线程
        assert monitor._monitor_thread.daemon is True
        
        monitor.stop()
    
    def test_monitor_stop_thread_join(self):
        """测试停止时线程正确join"""
        monitor = ResourceMonitor(interval=1)
        
        with patch.object(threading.Thread, 'join') as mock_join:
            monitor.start()
            
            # 确保线程已启动
            assert monitor._monitor_thread is not None
            
            monitor.stop()
            
            # 验证join被调用
            mock_join.assert_called_once()
    
    def test_monitor_context_manager_like_usage(self):
        """测试类似上下文管理器的使用方式"""
        monitor = ResourceMonitor(interval=1)
        
        try:
            monitor.start()
            assert monitor._running is True
            
            # 模拟一些操作
            test_data = {"cpu": 30.0, "memory": 2048}
            monitor._plugin_usage["test_plugin"] = test_data
            
            usage = monitor.get_usage("test_plugin")
            assert usage == test_data
            
        finally:
            monitor.stop()
            assert monitor._running is False


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
