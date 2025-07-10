# -*- coding: utf-8 -*-
"""
PTrade研究模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ....core.event_bus import EventBus
from ..scheduling.scheduler import PTradeScheduler
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
        self._scheduler = PTradeScheduler(event_bus)  # 初始化调度器
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
            # 定时和回调API
            "run_daily",
            "run_interval",
            "tick_data",
            "on_order_response",
            "on_trade_response",
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

    # ==============================================
    # 明确委托给Mixin的抽象方法实现
    # 由于Python多重继承中抽象方法标记的持久性问题，
    # 需要明确重写这些方法以消除抽象方法标记
    # ==============================================

    # 数据获取方法 - 委托给DataRetrievalMixin
    def get_history(self, *args, **kwargs):
        return DataRetrievalMixin.get_history(self, *args, **kwargs)

    def get_price(self, *args, **kwargs):
        return DataRetrievalMixin.get_price(self, *args, **kwargs)

    def get_snapshot(self, *args, **kwargs):
        return DataRetrievalMixin.get_snapshot(self, *args, **kwargs)

    def get_stock_info(self, *args, **kwargs):
        return DataRetrievalMixin.get_stock_info(self, *args, **kwargs)

    def get_fundamentals(self, *args, **kwargs):
        return DataRetrievalMixin.get_fundamentals(self, *args, **kwargs)

    # 股票信息方法 - 委托给StockInfoMixin
    def get_stock_name(self, *args, **kwargs):
        return StockInfoMixin.get_stock_name(self, *args, **kwargs)

    def get_stock_status(self, *args, **kwargs):
        return StockInfoMixin.get_stock_status(self, *args, **kwargs)

    def get_stock_exrights(self, *args, **kwargs):
        return StockInfoMixin.get_stock_exrights(self, *args, **kwargs)

    def get_stock_blocks(self, *args, **kwargs):
        return StockInfoMixin.get_stock_blocks(self, *args, **kwargs)

    def get_index_stocks(self, *args, **kwargs):
        return StockInfoMixin.get_index_stocks(self, *args, **kwargs)

    def get_industry_stocks(self, *args, **kwargs):
        return StockInfoMixin.get_industry_stocks(self, *args, **kwargs)

    def get_Ashares(self, *args, **kwargs):
        return StockInfoMixin.get_Ashares(self, *args, **kwargs)

    def get_etf_list(self, *args, **kwargs):
        return StockInfoMixin.get_etf_list(self, *args, **kwargs)

    def get_ipo_stocks(self, *args, **kwargs):
        return StockInfoMixin.get_ipo_stocks(self, *args, **kwargs)

    # 技术指标方法 - 委托给TechnicalIndicatorMixin
    def get_MACD(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_MACD(self, *args, **kwargs)

    def get_KDJ(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_KDJ(self, *args, **kwargs)

    def get_RSI(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_RSI(self, *args, **kwargs)

    def get_CCI(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_CCI(self, *args, **kwargs)

    # 工具函数方法 - 委托给CommonUtilsMixin
    def log(self, *args, **kwargs):
        return CommonUtilsMixin.log(self, *args, **kwargs)

    def check_limit(self, *args, **kwargs):
        return CommonUtilsMixin.check_limit(self, *args, **kwargs)

    def get_trading_day(self, *args, **kwargs):
        return CommonUtilsMixin.get_trading_day(self, *args, **kwargs)

    def get_all_trades_days(self, *args, **kwargs):
        return CommonUtilsMixin.get_all_trades_days(self, *args, **kwargs)

    def get_trade_days(self, *args, **kwargs):
        return CommonUtilsMixin.get_trade_days(self, *args, **kwargs)

    # 设置方法 - 委托给BaseAPIRouter或已实现
    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        if hasattr(self.context, "universe"):
            self.context.universe = securities
        else:
            setattr(self.context, "universe", securities)
        self._logger.info(f"Universe set to {len(securities)} securities")

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        if hasattr(self.context, "benchmark"):
            self.context.benchmark = benchmark
        else:
            setattr(self.context, "benchmark", benchmark)
        self._logger.info(f"Benchmark set to {benchmark}")

    # ==============================================
    # 定时和回调API实现
    # ==============================================

    def run_daily(
        self, func: Any, time_str: str = "09:30", *args: Any, **kwargs: Any
    ) -> str:
        """按日周期处理 - 每日定时执行指定函数"""
        try:
            # 启动调度器（如果尚未启动）
            if not self._scheduler._running:
                self._scheduler.start()

            # 生成唯一任务ID
            job_id = f"daily_{func.__name__}_{time_str.replace(':', '')}"

            # 添加日常任务
            actual_job_id = self._scheduler.add_daily_job(
                job_id=job_id, func=func, time_str=time_str, args=args, kwargs=kwargs
            )

            self._logger.info(f"Added daily job {actual_job_id} at {time_str}")
            return actual_job_id

        except Exception as e:
            self._logger.error(f"Error adding daily job: {e}")
            raise RuntimeError(f"Failed to add daily job: {e}")

    def run_interval(
        self, func: Any, interval: Union[int, str], *args: Any, **kwargs: Any
    ) -> str:
        """按设定周期处理 - 按指定间隔重复执行函数"""
        try:
            # 启动调度器（如果尚未启动）
            if not self._scheduler._running:
                self._scheduler.start()

            # 生成唯一任务ID
            job_id = f"interval_{func.__name__}_{interval}"

            # 添加间隔任务
            actual_job_id = self._scheduler.add_interval_job(
                job_id=job_id, func=func, interval=interval, args=args, kwargs=kwargs
            )

            self._logger.info(f"Added interval job {actual_job_id} every {interval}")
            return actual_job_id

        except Exception as e:
            self._logger.error(f"Error adding interval job: {e}")
            raise RuntimeError(f"Failed to add interval job: {e}")

    def tick_data(self, func: Any) -> bool:
        """tick级别处理 - 注册tick数据回调函数"""
        try:
            self._scheduler.add_tick_callback(func)
            self._logger.info(f"Added tick data callback: {func.__name__}")
            return True

        except Exception as e:
            self._logger.error(f"Error adding tick callback: {e}")
            return False

    def on_order_response(self, func: Any) -> bool:
        """委托回报 - 注册订单状态变化回调函数"""
        try:
            self._scheduler.add_order_response_callback(func)
            self._logger.info(f"Added order response callback: {func.__name__}")
            return True

        except Exception as e:
            self._logger.error(f"Error adding order response callback: {e}")
            return False

    def on_trade_response(self, func: Any) -> bool:
        """成交回报 - 注册成交确认回调函数"""
        try:
            self._scheduler.add_trade_response_callback(func)
            self._logger.info(f"Added trade response callback: {func.__name__}")
            return True

        except Exception as e:
            self._logger.error(f"Error adding trade response callback: {e}")
            return False

    # ==============================================
    # 调度器生命周期管理
    # ==============================================

    def start_scheduler(self) -> None:
        """启动调度器"""
        if not self._scheduler._running:
            self._scheduler.start()
            self._logger.info("Scheduler started")

    def stop_scheduler(self) -> None:
        """停止调度器"""
        if self._scheduler._running:
            self._scheduler.stop()
            self._logger.info("Scheduler stopped")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self._scheduler._running,
            "jobs": self._scheduler.get_jobs(),
            "tick_callbacks": len(self._scheduler._tick_callbacks),
            "order_callbacks": len(self._scheduler._order_response_callbacks),
            "trade_callbacks": len(self._scheduler._trade_response_callbacks),
        }

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
