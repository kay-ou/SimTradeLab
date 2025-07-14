# -*- coding: utf-8 -*-
"""
SimTradeLab 插件安全沙箱系统

本文件定义了多级插件沙箱系统，用于隔离插件的运行环境，保障系统安全。
"""

import abc
import threading
from typing import Any, Callable

from ..base import BasePlugin


class SandboxError(Exception):
    """沙箱相关异常"""

    pass


class BaseSandbox(abc.ABC):
    """
    沙箱抽象基类
    """

    def __init__(self, plugin: BasePlugin):
        self.plugin = plugin

    @abc.abstractmethod
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        在沙箱环境中执行一个函数。

        Args:
            func: 要执行的函数。
            *args: 函数的位置参数。
            **kwargs: 函数的关键字参数。

        Returns:
            函数的执行结果。
        """
        raise NotImplementedError


class ThreadSandbox(BaseSandbox):
    """
    线程级沙箱

    为每个插件提供一个独立的线程来执行其代码，实现基础的隔离。
    """

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        在一个新的线程中执行函数。
        """
        result = None
        exception = None

        def target():
            nonlocal result, exception
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                exception = e

        thread = threading.Thread(target=target)
        thread.start()
        thread.join()  # 等待线程执行完毕

        if exception:
            raise SandboxError(
                f"Error executing in thread sandbox: {exception}"
            ) from exception

        return result
