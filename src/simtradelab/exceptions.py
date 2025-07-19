# -*- coding: utf-8 -*-
"""
SimTradeLab 核心异常
"""


class SimTradeLabException(Exception):
    """所有 SimTradeLab 自定义异常的基类。"""

    pass


# region 插件异常


class PluginError(SimTradeLabException):
    """与插件相关的错误的基类。"""

    pass


class PluginNotFoundError(PluginError, KeyError):
    """当找不到指定的插件时引发。"""

    pass


class PluginLoadError(PluginError, ImportError):
    """当无法加载插件时引发，例如由于依赖项缺失或导入错误。"""

    pass


class PluginConfigurationError(PluginError, ValueError):
    """当插件配置无效时引发。"""

    pass


class PluginRegistrationError(PluginError):
    """当插件注册失败时引发。"""

    pass


# endregion

# region 数据异常


class DataSourceError(SimTradeLabException):
    """与数据源操作相关的错误的基类。"""

    pass


class DataLoadError(DataSourceError):
    """在数据加载过程中发生错误时引发。"""

    pass


class DataValidationError(DataSourceError):
    """当数据未能通过验证检查时引发。"""

    pass


# endregion

# region 交易异常


class TradingError(SimTradeLabException):
    """与交易操作相关的错误的基类。"""

    pass


class InsufficientFundsError(TradingError):
    """当没有足够的资金来执行交易时引发。"""

    pass


class InsufficientPositionError(TradingError):
    """当没有足够的持仓来执行卖出交易时引发。"""

    pass


class InvalidOrderError(TradingError):
    """当订单参数无效时引发。"""

    pass


# endregion

# region 引擎和策略异常


class EngineError(SimTradeLabException):
    """与回测引擎操作相关的错误的基类。"""

    pass


class StrategyError(EngineError):
    """在策略执行过程中发生错误时引发。"""

    pass


class StrategyNotFoundException(SimTradeLabException, FileNotFoundError):
    """当策略文件不存在时引发。"""

    pass


class StrategySyntaxError(SimTradeLabException, SyntaxError):
    """当策略文件存在语法错误时引发。"""

    pass


# endregion

# region 其他异常


class ReportGenerationError(SimTradeLabException):
    """在报告生成过程中发生错误时引发。"""

    pass


# endregion
