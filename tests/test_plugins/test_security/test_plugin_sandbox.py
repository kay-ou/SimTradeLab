# -*- coding: utf-8 -*-
"""
PluginSandbox 的单元测试
"""
import pytest
from unittest.mock import MagicMock
from simtradelab.plugins.security.plugin_sandbox import ThreadSandbox, SandboxError

def test_thread_sandbox_executes_successfully():
    """
    测试：ThreadSandbox 能够成功执行一个无异常的函数。
    """
    plugin_mock = MagicMock()
    sandbox = ThreadSandbox(plugin=plugin_mock)
    
    def sample_function(a, b):
        return a + b
        
    result = sandbox.execute(sample_function, 1, b=2)
    assert result == 3

def test_thread_sandbox_handles_exception():
    """
    测试：ThreadSandbox 能够捕获并重新抛出在沙箱中执行的函数所引发的异常。
    """
    plugin_mock = MagicMock()
    sandbox = ThreadSandbox(plugin=plugin_mock)
    
    def error_function():
        raise ValueError("Test error")
        
    with pytest.raises(SandboxError, match="Error executing in thread sandbox: Test error"):
        sandbox.execute(error_function)
