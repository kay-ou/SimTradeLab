# -*- coding: utf-8 -*-
"""
PTrade 全局 API 类型定义
扩展 Python builtins，将 ptrade API 注入全局作用域
"""

from __future__ import annotations
from typing import Any, Callable, Optional
import pandas as pd

# ==================== 基础 API ====================

def get_research_path() -> str:
    """返回研究目录路径"""
    ...

def get_Ashares(date: Optional[str] = ...) -> list[str]:
    """返回A股代码列表，支持历史查询

    Args:
        date: 查询日期，None表示当前回测日期
    """
    ...

def get_trade_days(start_date: Optional[str] = ..., end_date: Optional[str] = ..., count: Optional[int] = ...) -> list[str]:
    """获取指定范围交易日列表

    Args:
        start_date: 开始日期（与count二选一）
        end_date: 结束日期（默认当前回测日期）
        count: 往前count个交易日（与start_date二选一）
    """
    ...

def get_all_trades_days(date: Optional[str] = ...) -> list[str]:
    """获取某日期之前的所有交易日列表

    Args:
        date: 截止日期（默认当前回测日期）
    """
    ...

def get_trading_day(day: int = ...) -> Optional[str]:
    """获取当前时间数天前或数天后的交易日期

    Args:
        day: 偏移天数（正数向后，负数向前，0表示当天或上一交易日）

    Returns:
        交易日期字符串，如 '2024-01-15'
    """
    ...

# ==================== 基本面 API ====================

def get_fundamentals(stocks: list[str], table: str, fields: list[str], date: Optional[str] = ...) -> pd.DataFrame:
    """获取基本面数据

    Args:
        stocks: 股票代码列表
        table: 表名 (valuation/profit_ability/growth_ability/operating_ability/debt_paying_ability)
        fields: 字段列表
        date: 查询日期（默认为回测当前日期）

    Returns:
        基本面数据 DataFrame，index 为股票代码
    """
    ...

# ==================== 行情 API ====================

def get_price(
    security: str | list[str],
    start_date: Optional[str] = ...,
    end_date: Optional[str] = ...,
    frequency: str = ...,
    fields: Optional[str | list[str]] = ...,
    fq: Optional[str] = ...,
    count: Optional[int] = ...
) -> pd.DataFrame | dict:
    """获取历史行情数据

    Args:
        security: 股票代码或代码列表
        start_date: 开始日期
        end_date: 结束日期
        frequency: 频率，默认 '1d'
        fields: 字段名或字段列表
        fq: 复权类型 ('pre'-前复权, None-不复权)
        count: 获取 count 个数据点
    """
    ...

def get_history(
    count: int,
    frequency: str = ...,
    field: str | list[str] = ...,
    security_list: Optional[str | list[str]] = ...,
    fq: Optional[str] = ...,
    include: bool = ...,
    fill: str = ...,
    is_dict: bool = ...
) -> pd.DataFrame | dict:
    """获取历史数据

    Args:
        count: 获取多少个数据点
        frequency: 频率，默认 '1d'
        field: 字段名或字段列表，默认 'close'
        security_list: 股票代码或代码列表
        fq: 复权类型 ('pre'-前复权, None-不复权)
        include: 是否包含当前bar，默认 False
        fill: 填充方式，默认 'nan'
        is_dict: 是否返回字典格式，默认 False
    """
    ...

# ==================== 股票信息 API ====================

def get_stock_blocks(stock: str) -> dict:
    """获取股票所属板块

    Args:
        stock: 股票代码
    """
    ...

def get_stock_info(stocks: str | list[str], field: Optional[str | list[str]] = ...) -> dict[str, dict]:
    """获取股票基础信息

    Args:
        stocks: 股票代码或代码列表
        field: 字段名或字段列表，如 ['stock_name', 'listed_date']
    """
    ...

def get_stock_name(stocks: str | list[str]) -> str | dict[str, str]:
    """获取股票名称

    Args:
        stocks: 股票代码或代码列表

    Returns:
        单个股票返回字符串，多个股票返回字典
    """
    ...

def get_stock_status(stocks: str | list[str], query_type: str = ..., query_date: Optional[str] = ...) -> dict[str, bool]:
    """获取股票状态

    Args:
        stocks: 股票代码或代码列表
        query_type: 查询类型 ('ST', 'HALT', 'DELISTING')，默认 'ST'
        query_date: 查询日期
    """
    ...

def get_stock_exrights(stock_code: str, date: Optional[str] = ...) -> Optional[pd.DataFrame]:
    """获取股票除权除息信息

    Args:
        stock_code: 股票代码
        date: 查询日期
    """
    ...

# ==================== 指数/行业 API ====================

def get_index_stocks(index_code: str, date: Optional[str] = ...) -> list[str]:
    """获取指数成份股

    Args:
        index_code: 指数代码，如 '000300.SS'
        date: 查询日期
    """
    ...

def get_industry_stocks(industry_code: Optional[str] = ...) -> dict | list[str]:
    """获取行业成份股

    Args:
        industry_code: 行业代码，None 返回所有行业
    """
    ...

# ==================== 涨跌停 API ====================

def check_limit(security: str | list[str], query_date: Optional[str] = ...) -> dict[str, int]:
    """检查涨跌停状态

    Args:
        security: 股票代码或代码列表
        query_date: 查询日期

    Returns:
        {股票代码: 状态} 字典，状态: 1=涨停, -1=跌停, 0=正常
    """
    ...

# ==================== 交易 API ====================

def order(security: str, amount: int, limit_price: Optional[float] = ...) -> Optional[str]:
    """买卖指定数量的股票

    Args:
        security: 股票代码
        amount: 交易数量，正数表示买入，负数表示卖出
        limit_price: 买卖限价

    Returns:
        订单id或None
    """
    ...

def order_target(stock: str, amount: int, limit_price: Optional[float] = ...) -> Optional[str]:
    """下单到目标数量

    Args:
        stock: 股票代码
        amount: 期望的最终数量
        limit_price: 买卖限价
    """
    ...

def order_value(stock: str, value: float, limit_price: Optional[float] = ...) -> Optional[str]:
    """按金额下单

    Args:
        stock: 股票代码
        value: 股票价值（元）
        limit_price: 买卖限价
    """
    ...

def order_target_value(stock: str, value: float, limit_price: Optional[float] = ...) -> Optional[str]:
    """调整股票持仓市值到目标价值

    Args:
        stock: 股票代码
        value: 期望的股票最终价值（元）
        limit_price: 买卖限价
    """
    ...

def get_open_orders() -> list:
    """获取未成交订单"""
    ...

def get_orders(security: Optional[str] = ...) -> list:
    """获取当日全部订单

    Args:
        security: 股票代码，None表示获取所有订单
    """
    ...

def get_order(order_id: str) -> Optional[Any]:
    """获取指定订单

    Args:
        order_id: 订单id
    """
    ...

def get_trades() -> list:
    """获取当日成交订单"""
    ...

def get_position(security: str) -> Optional[Any]:
    """获取持仓信息

    Args:
        security: 股票代码
    """
    ...

def cancel_order(order: Any) -> bool:
    """取消订单

    Args:
        order: Order对象
    """
    ...

# ==================== 配置 API ====================

def set_benchmark(benchmark: str) -> None:
    """设置基准（支持指数和普通股票）

    Args:
        benchmark: 基准代码，如 '000300.SS'
    """
    ...

def set_universe(stocks: str | list[str]) -> None:
    """设置股票池并预加载数据

    Args:
        stocks: 股票代码或代码列表
    """
    ...

def is_trade() -> bool:
    """是否实盘

    Returns:
        回测环境总是返回 False
    """
    ...

def set_commission(commission_ratio: float = ..., min_commission: float = ..., type: str = ...) -> None:
    """设置交易佣金

    Args:
        commission_ratio: 佣金费率，默认万三
        min_commission: 最低佣金，默认5元
        type: 类型，默认 "STOCK"
    """
    ...

def set_slippage(slippage: float = ...) -> None:
    """设置滑点

    Args:
        slippage: 滑点比例
    """
    ...

def set_fixed_slippage(fixedslippage: float = ...) -> None:
    """设置固定滑点

    Args:
        fixedslippage: 固定滑点比例，默认 0.001
    """
    ...

def set_limit_mode(limit_mode: str = ...) -> None:
    """设置下单限制模式

    Args:
        limit_mode: 限制模式 ('LIMIT', 'UNLIMITED')，默认 'LIMIT'
    """
    ...

def set_volume_ratio(volume_ratio: float = ...) -> None:
    """设置成交比例

    Args:
        volume_ratio: 成交比例，默认0.25
    """
    ...

def set_yesterday_position(poslist: list[dict]) -> None:
    """设置底仓（回测用）

    Args:
        poslist: 持仓列表，每个元素为字典 {'security': 股票代码, 'amount': 数量, 'cost_basis': 成本价}
    """
    ...

def run_interval(context: Any, func: Callable, seconds: int = ...) -> None:
    """定时运行函数（秒级，仅实盘）

    Args:
        context: Context对象
        func: 自定义函数
        seconds: 时间间隔（秒），默认10秒
    """
    ...

def run_daily(context: Any, func: Callable, time: str = ...) -> None:
    """定时运行函数

    Args:
        context: Context对象
        func: 自定义函数
        time: 触发时间，格式HH:MM，默认 '9:31'
    """
    ...

# ==================== 全局对象 ====================

class _Global:
    """全局变量容器，可存储策略自定义变量"""
    def __setattr__(self, name: str, value: Any) -> None: ...
    def __getattr__(self, name: str) -> Any: ...

class _Log:
    """日志对象"""
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def debug(self, msg: str) -> None: ...

class _Context:
    """策略上下文对象"""
    current_dt: pd.Timestamp
    portfolio: Any
    benchmark: str

class _Data:
    """市场数据对象"""
    def __getitem__(self, key: str) -> dict[str, Any]: ...

g: _Global
log: _Log
context: _Context
data: _Data
