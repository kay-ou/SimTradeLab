# -*- coding: utf-8 -*-
"""
PTrade研究模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ....core.event_bus import EventBus
from .base import BaseAPIRouter
from .common_utils_mixin import CommonUtilsMixin
from .data_retrieval_mixin import DataRetrievalMixin
from .stock_info_mixin import StockInfoMixin
from .technical_indicator_mixin import TechnicalIndicatorMixin

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class ResearchAPIRouter(
    BaseAPIRouter,
    StockInfoMixin,
    TechnicalIndicatorMixin,
    DataRetrievalMixin,
    CommonUtilsMixin,
):
    """研究模式API路由器"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        super().__init__(context, event_bus)
        self._data_plugin = None  # 将在设置时从适配器获取
        self._supported_apis = {
            # 数据获取API
            "get_history",
            "get_price",
            "get_snapshot",
            "get_stock_info",
            "get_fundamentals",
            # 股票信息API (新增的9个API)
            "get_stock_name",
            "get_stock_status",
            "get_stock_exrights",
            "get_stock_blocks",
            "get_index_stocks",
            "get_industry_stocks",
            "get_Ashares",
            "get_etf_list",
            "get_ipo_stocks",
            # 技术指标API
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            # 交易日期API
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            # 配置API
            "set_universe",
            "set_benchmark",
            "set_commission",
            "set_slippage",
            "set_fixed_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
            "set_parameters",
            # 工具API
            "log",
            "check_limit",
            "handle_data",
        }

    def set_data_plugin(self, data_plugin: Any) -> None:
        """设置数据插件引用"""
        self._data_plugin = data_plugin
        self._logger.info("Data plugin set for research mode")

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在研究模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def order_target(
        self,
        security: str,
        target_amount: int,
        limit_price: Optional[float] = None,
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def order_target_value(
        self,
        security: str,
        target_value: float,
        limit_price: Optional[float] = None,
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def cancel_order(self, order_id: str) -> bool:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def cancel_order_ex(self, order_id: str) -> bool:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def get_all_orders(self) -> List["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def get_position(self, security: str) -> Optional["Position"]:
        """研究模式不支持持仓查询"""
        raise NotImplementedError("Position queries are not supported in research mode")

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """研究模式不支持持仓查询"""
        raise NotImplementedError("Position queries are not supported in research mode")

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def get_order(self, order_id: str) -> Optional["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """研究模式不支持交易查询"""
        raise NotImplementedError("Trade queries are not supported in research mode")

    # 这些方法现在由Mixin提供，无需在这里重复实现
    # get_MACD, get_KDJ, get_RSI, get_CCI
    # log, check_limit

    # 研究模式下的配置方法需要特殊处理（存储在context中）
    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        # 研究模式下支持设置佣金费率用于分析
        setattr(self.context, "_commission_rate", commission)
        self._logger.info(f"Research commission rate set to {commission}")

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        # 研究模式下支持设置滑点用于分析
        setattr(self.context, "_slippage_rate", slippage)
        self._logger.info(f"Research slippage rate set to {slippage}")

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        # 研究模式下支持设置固定滑点用于分析
        setattr(self.context, "_fixed_slippage_rate", slippage)
        self._logger.info(f"Research fixed slippage rate set to {slippage}")

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        # 研究模式下支持设置成交比例用于分析
        if not 0 < ratio <= 1:
            self._logger.warning(f"Volume ratio {ratio} should be between 0 and 1")
            return

        setattr(self.context, "_volume_ratio", ratio)
        self._logger.info(f"Research volume ratio set to {ratio}")

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        # 研究模式下支持设置限制模式用于分析
        valid_modes = ["volume", "order", "none"]
        if mode not in valid_modes:
            self._logger.warning(
                f"Invalid limit mode: {mode}. Valid modes: {valid_modes}"
            )
            return

        setattr(self.context, "_limit_mode", mode)
        self._logger.info(f"Research limit mode set to {mode}")

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        # 研究模式下支持设置底仓用于分析
        if not isinstance(positions, dict):
            self._logger.warning("Yesterday position must be a dictionary")
            return

        setattr(self.context, "_yesterday_position", positions)
        self._logger.info(
            f"Research yesterday position set with {len(positions)} positions"
        )

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        # 研究模式下支持设置参数
        if not hasattr(self.context, "_parameters"):
            setattr(self.context, "_parameters", {})
        getattr(self.context, "_parameters").update(params)
        self._logger.info(f"Research parameters set: {params}")

    def handle_data(self, data: Dict[str, Any]) -> None:
        """研究模式数据处理"""
        # 研究模式主要用于数据分析，不涉及交易
        pass
