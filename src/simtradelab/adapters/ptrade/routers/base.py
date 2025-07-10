# -*- coding: utf-8 -*-
"""
PTrade API 路由器基类

定义完整的 PTrade API 接口规范
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ....core.event_bus import EventBus

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class BaseAPIRouter(ABC):
    """API路由器基类 - 定义完整的 PTrade API 接口"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        self.context = context
        self.event_bus = event_bus
        self._logger = logging.getLogger(self.__class__.__name__)

    # ==========================================
    # 交易相关 API (核心方法)
    # ==========================================

    @abstractmethod
    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """下单"""
        pass

    @abstractmethod
    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        pass

    @abstractmethod
    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定目标数量买卖"""
        pass

    @abstractmethod
    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定持仓市值买卖"""
        pass

    @abstractmethod
    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        pass

    @abstractmethod
    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展"""
        pass

    @abstractmethod
    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        pass

    @abstractmethod
    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        pass

    @abstractmethod
    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        pass

    @abstractmethod
    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        pass

    @abstractmethod
    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓信息"""
        pass

    @abstractmethod
    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息"""
        pass

    @abstractmethod
    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单"""
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定订单"""
        pass

    @abstractmethod
    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取全部订单"""
        pass

    @abstractmethod
    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单"""
        pass

    # ==========================================
    # 数据获取 API (核心方法)
    # ==========================================

    @abstractmethod
    def get_history(
        self,
        count: int,
        frequency: str = "1d",
        field: Union[str, List[str]] = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "money",
            "price",
        ],
        security_list: Optional[List[str]] = None,
        fq: Optional[str] = None,
        include: bool = False,
        fill: str = "nan",
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """获取历史行情数据"""
        pass

    @abstractmethod
    def get_price(
        self,
        security: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取价格数据"""
        pass

    @abstractmethod
    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
        pass

    @abstractmethod
    def get_trading_day(self, date: str, offset: int = 0) -> str:
        """获取交易日期"""
        pass

    @abstractmethod
    def get_all_trades_days(self) -> List[str]:
        """获取全部交易日期"""
        pass

    @abstractmethod
    def get_trade_days(self, start_date: str, end_date: str) -> List[str]:
        """获取指定范围交易日期"""
        pass

    @abstractmethod
    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息"""
        pass

    @abstractmethod
    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息"""
        pass

    # ==========================================
    # 股票信息获取 API
    # ==========================================

    @abstractmethod
    def get_stock_name(self, security: str) -> str:
        """获取股票名称"""
        pass

    @abstractmethod
    def get_stock_status(self, security: str) -> Dict[str, Any]:
        """获取股票状态信息"""
        pass

    @abstractmethod
    def get_stock_exrights(self, security: str) -> pd.DataFrame:
        """获取股票除权除息信息"""
        pass

    @abstractmethod
    def get_stock_blocks(self, security: str) -> List[str]:
        """获取股票所属板块信息"""
        pass

    @abstractmethod
    def get_index_stocks(self, index_code: str) -> List[str]:
        """获取指数成份股"""
        pass

    @abstractmethod
    def get_industry_stocks(self, industry_code: str) -> List[str]:
        """获取行业成份股"""
        pass

    @abstractmethod
    def get_Ashares(self, date: str) -> List[str]:
        """获取指定日期A股代码列表"""
        pass

    @abstractmethod
    def get_etf_list(self) -> List[str]:
        """获取ETF代码列表"""
        pass

    @abstractmethod
    def get_ipo_stocks(self, date: str) -> List[str]:
        """获取当日IPO申购标的"""
        pass

    # ==========================================
    # 设置函数 API
    # ==========================================

    @abstractmethod
    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        pass

    @abstractmethod
    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        pass

    @abstractmethod
    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        pass

    @abstractmethod
    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        pass

    @abstractmethod
    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        pass

    @abstractmethod
    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        pass

    @abstractmethod
    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        pass

    @abstractmethod
    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        pass

    @abstractmethod
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        pass

    # ==========================================
    # 计算函数 API
    # ==========================================

    @abstractmethod
    def get_MACD(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标"""
        pass

    @abstractmethod
    def get_KDJ(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标"""
        pass

    @abstractmethod
    def get_RSI(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标"""
        pass

    @abstractmethod
    def get_CCI(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标"""
        pass

    # ==========================================
    # 工具函数 API
    # ==========================================

    @abstractmethod
    def log(self, content: str, level: str = "info") -> None:
        """日志记录"""
        pass

    @abstractmethod
    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """代码涨跌停状态判断"""
        pass

    # ==========================================
    # 模式相关的处理方法
    # ==========================================

    @abstractmethod
    def handle_data(self, data: Dict[str, Any]) -> None:
        """处理市场数据"""
        pass

    @abstractmethod
    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在当前模式下支持"""
        pass

    def validate_and_execute(
        self, api_name: str, method_func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """验证并执行API调用"""
        if not self.is_mode_supported(api_name):
            raise ValueError(f"API '{api_name}' is not supported in current mode")

        try:
            return method_func(*args, **kwargs)
        except Exception as e:
            self._logger.error(f"Error executing API '{api_name}': {e}")
            raise
