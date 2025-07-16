# -*- coding: utf-8 -*-
"""
PTrade回测模式API路由器
"""

from typing import Any, Dict, List, Optional, Union

from ....core.event_bus import EventBus
from ..api_validator import APIValidator
from ..context import PTradeContext
from ..lifecycle_controller import LifecycleController
from ..models import Order, Position
from ..services.backtest_service import BacktestService
from .base import BaseAPIRouter


class BacktestAPIRouter(BaseAPIRouter):
    """回测模式API路由器"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        lifecycle_controller: Optional[LifecycleController] = None,
        api_validator: Optional[APIValidator] = None,
        plugin_manager: Optional[Any] = None,
    ):
        super().__init__(
            context, event_bus, lifecycle_controller, api_validator, plugin_manager
        )

        # 初始化回测服务
        self._service = BacktestService(
            context=context, event_bus=event_bus, plugin_manager=plugin_manager
        )

        self._supported_apis = {
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            "get_history",
            "get_price",
            "get_snapshot",
            "get_stock_info",
            "get_fundamentals",
            "get_stock_name",
            "get_stock_status",
            "get_stock_exrights",
            "get_stock_blocks",
            "get_index_stocks",
            "get_industry_stocks",
            "get_Ashares",
            "get_etf_list",
            "get_ipo_stocks",
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            "log",
            "is_trade",
            "check_limit",
            "set_universe",
            "set_benchmark",
            "set_commission",
            "set_fixed_slippage",
            "set_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
            "set_parameters",
            "run_daily",
            "run_interval",
            "order",
            "order_target",
            "order_value",
            "order_target_value",
            "order_market",
            "cancel_order",
            "cancel_order_ex",
            "get_all_orders",
            "get_position",
            "get_positions",
            "get_open_orders",
            "get_order",
            "get_orders",
            "get_trades",
            "handle_data",
        }

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在回测模式下支持"""
        return api_name in self._supported_apis

    def set_data_plugin(self, data_plugin: Any) -> None:
        """设置数据插件引用"""
        self._data_plugin = data_plugin
        self._logger.info("Data plugin set for backtest mode")

    def _get_indicators_plugin(self) -> Optional[Any]:
        """通过插件管理器获取技术指标插件"""
        if not self._plugin_manager:
            return None

        # 查找技术指标插件
        all_plugins = self._plugin_manager.get_all_plugins()
        for plugin_name, plugin_instance in all_plugins.items():
            if self._is_indicators_plugin(plugin_instance):
                return plugin_instance
        return None

    def _is_indicators_plugin(self, plugin_instance: Any) -> bool:
        """判断插件是否为技术指标插件"""
        required_methods = [
            "calculate_macd",
            "calculate_kdj",
            "calculate_rsi",
            "calculate_cci",
        ]
        is_indicators_plugin = all(
            hasattr(plugin_instance, method)
            and callable(getattr(plugin_instance, method))
            for method in required_methods
        )
        return is_indicators_plugin

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        return self.validate_and_execute(
            "order", self._service.execute_order, security, amount, limit_price
        )

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        return self.validate_and_execute(
            "order_value",
            self._service.execute_order_value,
            security,
            value,
            limit_price,
        )

    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        return self.validate_and_execute(
            "order_target",
            self._service.execute_order_target,
            security,
            target_amount,
            limit_price,
        )

    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        return self.validate_and_execute(
            "order_target_value",
            self._service.execute_order_target_value,
            security,
            target_value,
            limit_price,
        )

    def order_market(self, security: str, amount: int) -> Optional[str]:
        return self.validate_and_execute(
            "order_market", self._service.execute_market_order, security, amount
        )

    def cancel_order(self, order_id: str) -> bool:
        return self.validate_and_execute(
            "cancel_order", self._service.cancel_order, order_id
        )

    def cancel_order_ex(self, order_id: str) -> bool:
        return self.validate_and_execute(
            "cancel_order_ex", self._service.cancel_order_ex, order_id
        )

    def get_all_orders(self) -> List["Order"]:
        return self.validate_and_execute("get_all_orders", self._service.get_orders)

    def get_position(self, security: str) -> Optional["Position"]:
        return self.validate_and_execute(
            "get_position", self._service.get_position, security
        )

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        return self.validate_and_execute(
            "get_positions", self._service.get_positions, security_list
        )

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        return self.validate_and_execute(
            "get_open_orders", self._service.get_open_orders, security
        )

    def get_order(self, order_id: str) -> Optional["Order"]:
        return self.validate_and_execute("get_order", self._service.get_order, order_id)

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        return self.validate_and_execute(
            "get_orders", self._service.get_orders, security
        )

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.validate_and_execute(
            "get_trades", self._service.get_trades, security
        )

    def set_commission(self, commission: float) -> None:
        self.validate_and_execute(
            "set_commission", self._service.set_commission, commission
        )

    def set_slippage(self, slippage: float) -> None:
        self.validate_and_execute("set_slippage", self._service.set_slippage, slippage)

    def set_fixed_slippage(self, slippage: float) -> None:
        self.validate_and_execute(
            "set_fixed_slippage", self._service.set_slippage, slippage
        )

    def set_volume_ratio(self, ratio: float) -> None:
        self.validate_and_execute(
            "set_volume_ratio", self._service.set_volume_ratio, ratio
        )

    def set_limit_mode(self, mode: str) -> None:
        self.validate_and_execute("set_limit_mode", self._service.set_limit_mode, mode)

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        self.validate_and_execute(
            "set_yesterday_position", self._service.set_yesterday_position, positions
        )

    def set_parameters(self, params: Dict[str, Any]) -> None:
        self.validate_and_execute(
            "set_parameters", self._service.set_parameters, params
        )

    def handle_data(self, data: Dict[str, Any]) -> None:
        self.validate_and_execute("handle_data", self._service.handle_data_update, data)

    def run_daily(
        self, func: Any, time_str: str = "09:30", *args: Any, **kwargs: Any
    ) -> str:
        self._logger.warning(
            "run_daily is not fully supported in backtest mode, "
            "function will be stored but not scheduled"
        )
        job_id = f"daily_{id(func)}_{time_str}"
        if not hasattr(self.context, "_daily_functions"):
            setattr(self.context, "_daily_functions", {})
        getattr(self.context, "_daily_functions")[job_id] = {
            "func": func,
            "time": time_str,
            "args": args,
            "kwargs": kwargs,
        }
        return job_id

    def run_interval(
        self, func: Any, interval: Union[int, str], *args: Any, **kwargs: Any
    ) -> str:
        self._logger.warning(
            "run_interval is not fully supported in backtest mode, "
            "function will be stored but not scheduled"
        )
        job_id = f"interval_{id(func)}_{interval}"
        if not hasattr(self.context, "_interval_functions"):
            setattr(self.context, "_interval_functions", {})
        getattr(self.context, "_interval_functions")[job_id] = {
            "func": func,
            "interval": interval,
            "args": args,
            "kwargs": kwargs,
        }
        return job_id
