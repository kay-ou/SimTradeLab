# -*- coding: utf-8 -*-
"""
PTrade回测模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ....core.event_bus import EventBus
from ..api_validator import APIValidator
from ..lifecycle_controller import LifecycleController
from ..services import BacktestService
from .base import BaseAPIRouter

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class BacktestAPIRouter(BaseAPIRouter):
    """回测模式API路由器"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        slippage_rate: float = 0.0,
        commission_rate: float = 0.0,
        lifecycle_controller: Optional[LifecycleController] = None,
        api_validator: Optional[APIValidator] = None,
    ):
        super().__init__(context, event_bus, lifecycle_controller, api_validator)

        # 保存配置参数
        self._slippage_rate = slippage_rate
        self._commission_rate = commission_rate

        # 初始化回测服务
        self._trading_service = BacktestService(context=context, event_bus=event_bus)
        self._trading_service.set_commission(commission_rate)
        self._trading_service.set_slippage(slippage_rate)

        self._data_plugin = None  # 将在设置时从适配器获取
        self._supported_apis = {
            # === 已实际实现的API ===
            # 基础信息 (3个) - 通过父类BaseRouter实现
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            # 行情信息 - 通过父类BaseRouter实现
            "get_history",  # [回测/交易]
            "get_price",  # [研究/回测/交易]
            "get_snapshot",  # 在父类BaseRouter中实现，但回测模式下通常不可用
            "get_stock_info",  # [研究/回测/交易]
            "get_fundamentals",  # [研究/回测/交易]
            # 股票信息 (9个) - 通过父类BaseRouter实现
            "get_stock_name",
            "get_stock_status",
            "get_stock_exrights",
            "get_stock_blocks",
            "get_index_stocks",
            "get_industry_stocks",
            "get_Ashares",
            "get_etf_list",
            "get_ipo_stocks",
            # 技术指标 (4个) - 通过父类BaseRouter实现
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            # 工具函数 - 通过父类BaseRouter实现
            "log",  # 通过父类BaseRouter实现
            "is_trade",  # 通过父类BaseRouter实现
            "check_limit",  # 通过父类BaseRouter实现
            "set_universe",  # 通过父类BaseRouter实现
            "set_benchmark",  # 通过父类BaseRouter实现
            # 回测模式特有的配置方法 (在路由器中直接实现)
            "set_commission",
            "set_fixed_slippage",
            "set_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
            "set_parameters",
            "run_daily",
            # 交易相关函数 (在路由器中直接实现)
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

    def set_data_plugin(self, data_plugin: Any) -> None:
        """设置数据插件引用"""
        self._data_plugin = data_plugin
        self._logger.info("Data plugin set for backtest mode")

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在回测模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """回测模式下单逻辑 - 委托给交易服务"""
        return self._trading_service.execute_order(security, amount, limit_price)

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单 - 委托给交易服务"""
        return self._trading_service.execute_order_value(security, value, limit_price)

    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定目标数量买卖 - 委托给交易服务"""
        return self._trading_service.execute_order_target(
            security, target_amount, limit_price
        )

    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定持仓市值买卖 - 委托给交易服务"""
        return self._trading_service.execute_order_target_value(
            security, target_value, limit_price
        )

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托 - 委托给交易服务"""
        return self._trading_service.execute_market_order(security, amount)

    def cancel_order(self, order_id: str) -> bool:
        """回测模式撤单 - 委托给交易服务"""
        return self._trading_service.cancel_order(order_id)

    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展 - 委托给交易服务"""
        return self._trading_service.cancel_order_ex(order_id)

    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        # 在回测模式下，返回所有订单
        return self.get_orders()

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        # 回测模式下不支持新股申购，返回空列表
        self._logger.warning("IPO orders are not supported in backtest mode")
        return []

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        # 回测模式下不支持盘后交易，返回None
        self._logger.warning("After trading orders are not supported in backtest mode")
        return None

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        # 回测模式下不支持盘后交易，返回False
        self._logger.warning(
            "After trading cancel orders are not supported in backtest mode"
        )
        return False

    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓信息 - 委托给交易服务"""
        return self._trading_service.get_position(security)

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息 - 委托给交易服务"""
        return self._trading_service.get_positions(security_list)

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单 - 委托给交易服务"""
        return self._trading_service.get_open_orders(security)

    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定订单 - 委托给交易服务"""
        return self._trading_service.get_order(order_id)

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取全部订单 - 委托给交易服务"""
        return self._trading_service.get_orders(security)

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单 - 委托给交易服务"""
        return self._trading_service.get_trades(security)

    # 回测模式特有的配置方法 - 委托给交易服务
    def set_commission(self, commission: float) -> None:
        """设置佣金费率 - 委托给交易服务"""
        self._trading_service.set_commission(commission)

    def set_slippage(self, slippage: float) -> None:
        """设置滑点 - 委托给交易服务"""
        self._trading_service.set_slippage(slippage)

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点 - 委托给交易服务"""
        self._trading_service.set_slippage(slippage)

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例 - 委托给交易服务"""
        self._trading_service.set_volume_ratio(ratio)

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式 - 委托给交易服务"""
        self._trading_service.set_limit_mode(mode)

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓 - 委托给交易服务"""
        self._trading_service.set_yesterday_position(positions)

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数 - 委托给交易服务"""
        self._trading_service.set_parameters(params)

    def handle_data(self, data: Dict[str, Any]) -> None:
        """回测模式数据处理 - 委托给交易服务"""
        self._trading_service.handle_data_update(data)

    # ==========================================
    # 定时和回调 API 实现 - 保持在路由器层（涉及调度逻辑）
    # ==========================================

    def run_daily(
        self, func: Any, time_str: str = "09:30", *args: Any, **kwargs: Any
    ) -> str:
        """按日周期处理 - 每日定时执行指定函数"""
        self._logger.warning(
            "run_daily is not fully supported in backtest mode, "
            "function will be stored but not scheduled"
        )
        # 在回测模式下，我们只是记录这个函数，实际的执行由回测引擎控制
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
        """按设定周期处理 - 按指定间隔重复执行函数"""
        self._logger.warning(
            "run_interval is not fully supported in backtest mode, "
            "function will be stored but not scheduled"
        )
        # 在回测模式下，我们只是记录这个函数
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

    def tick_data(self, func: Any) -> bool:
        """tick级别处理 - 注册tick数据回调函数"""
        self._logger.warning(
            "tick_data is not supported in backtest mode as it uses bar data"
        )
        # 回测模式通常使用K线数据而不是tick数据
        return False

    def on_order_response(self, func: Any) -> bool:
        """委托回报 - 注册订单状态变化回调函数"""
        if not hasattr(self.context, "_order_response_callbacks"):
            setattr(self.context, "_order_response_callbacks", [])
        getattr(self.context, "_order_response_callbacks").append(func)
        self._logger.info("Order response callback registered")
        return True

    def on_trade_response(self, func: Any) -> bool:
        """成交回报 - 注册成交确认回调函数"""
        if not hasattr(self.context, "_trade_response_callbacks"):
            setattr(self.context, "_trade_response_callbacks", [])
        getattr(self.context, "_trade_response_callbacks").append(func)
        self._logger.info("Trade response callback registered")
        return True

    def get_current_data(
        self, security_list: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取当前数据 - 回测模式下必须使用真实数据源

        Args:
            security_list: 证券代码列表，如果为None则使用context.universe

        Returns:
            包含当前数据的字典，格式: {security: {field: value}}

        Raises:
            RuntimeError: 当没有可用的数据源时抛出异常
        """
        if security_list is None:
            security_list = list(self.context.universe) if self.context.universe else []

        if not security_list:
            return {}

        # 回测模式：必须使用真实数据源，不允许模拟数据回退
        current_data = {}

        # 获取数据插件
        data_plugin = self._get_data_plugin()
        if not data_plugin:
            raise RuntimeError(
                "No data plugin available for backtest mode. "
                "Simulated data fallback is not allowed in backtest environment."
            )

        if not hasattr(data_plugin, "get_history_data"):
            raise RuntimeError(
                f"Data plugin {type(data_plugin).__name__} "
                "does not support get_history_data method"
            )

        try:
            for security in security_list:
                # 获取最近1天的历史数据作为"当前"数据
                history_data = data_plugin.get_history_data(
                    security=security, count=1, frequency="1d"
                )

                if history_data.empty:
                    self._logger.error(
                        f"No historical data available for {security} in backtest mode"
                    )
                    raise RuntimeError(
                        f"No historical data available for {security}. "
                        "Cannot proceed with backtest without real data."
                    )

                latest_data = history_data.iloc[-1]
                current_data[security] = {
                    "price": float(latest_data["close"]),
                    "close": float(latest_data["close"]),
                    "open": float(latest_data["open"]),
                    "high": float(latest_data["high"]),
                    "low": float(latest_data["low"]),
                    "volume": int(latest_data["volume"]),
                    "last_price": float(latest_data["close"]),
                }

        except Exception as e:
            self._logger.error(f"Critical error accessing data in backtest mode: {e}")
            raise RuntimeError(
                f"Failed to get real data for backtest: {e}. "
                "Backtest cannot proceed without valid data sources."
            )

        return current_data
