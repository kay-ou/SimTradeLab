# -*- coding: utf-8 -*-
"""
PTrade异常类定义
"""

from ....exceptions import SimTradeLabError


class PTradeAdapterError(SimTradeLabError):
    """PTrade适配器异常"""

    pass


class PTradeCompatibilityError(PTradeAdapterError):
    """PTrade兼容性异常"""

    pass


class PTradeAPIError(PTradeAdapterError):
    """PTrade API调用异常"""

    pass
