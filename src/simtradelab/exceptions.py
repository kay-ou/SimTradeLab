# -*- coding: utf-8 -*-
"""
SimTradeLab 异常定义模块
"""


class SimTradeLabError(Exception):
    """SimTradeLab 基础异常类"""
    pass


class DataSourceError(SimTradeLabError):
    """数据源相关异常"""
    pass


class DataLoadError(DataSourceError):
    """数据加载异常"""
    pass


class DataValidationError(DataSourceError):
    """数据验证异常"""
    pass


class TradingError(SimTradeLabError):
    """交易相关异常"""
    pass


class InsufficientFundsError(TradingError):
    """资金不足异常"""
    pass


class InsufficientPositionError(TradingError):
    """持仓不足异常"""
    pass


class InvalidOrderError(TradingError):
    """无效订单异常"""
    pass


class EngineError(SimTradeLabError):
    """引擎相关异常"""
    pass


class StrategyError(EngineError):
    """策略相关异常"""
    pass


class ConfigurationError(SimTradeLabError):
    """配置相关异常"""
    pass


class ReportGenerationError(SimTradeLabError):
    """报告生成异常"""
    pass