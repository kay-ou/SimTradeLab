# -*- coding: utf-8 -*-
"""
PTrade研究模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ....core.event_bus import EventBus
from ..api_validator import APIValidator
from ..lifecycle_controller import LifecycleController
from ..scheduling.scheduler import PTradeScheduler
from .base import BaseAPIRouter

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class ResearchAPIRouter(BaseAPIRouter):
    """研究模式API路由器"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        lifecycle_controller: Optional[LifecycleController] = None,
        api_validator: Optional[APIValidator] = None,
        plugin_manager: Optional[Any] = None,
    ):
        super().__init__(context, event_bus, lifecycle_controller, api_validator)
        self._plugin_manager = plugin_manager  # 插件管理器引用
        self._scheduler = PTradeScheduler(event_bus)  # 初始化调度器
        self._supported_apis = {
            # === 实际已实现的API ===
            # 基础信息 (3个) - 通过父类BaseRouter实现
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            # 行情信息 - 通过父类BaseRouter实现
            "get_price",  # [研究/回测/交易]
            "get_history",  # [研究/回测/交易]
            "get_snapshot",  # [研究/回测/交易]
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
            "check_limit",  # [研究/回测/交易]
            "handle_data",  # 数据处理接口
            # 研究模式下的配置方法 (仅用于分析参数存储)
            "set_commission",
            "set_slippage",
            "set_fixed_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
            "set_parameters",
            "set_universe",
            "set_benchmark",
            # 定时和回调API (研究模式下用于数据分析流程)
            "run_daily",
            "run_interval",
            "tick_data",
            "on_order_response",
            "on_trade_response",
        }

    def _get_data_plugin(self) -> Optional[Any]:
        """通过插件管理器获取数据源插件"""
        if not self._plugin_manager:
            return None

        # 查找数据源插件
        all_plugins = self._plugin_manager.get_all_plugins()
        for plugin_name, plugin_instance in all_plugins.items():
            if self._is_data_source_plugin(plugin_instance):
                return plugin_instance
        return None

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

    def _is_data_source_plugin(self, plugin_instance: Any) -> bool:
        """判断插件是否为数据源插件"""
        required_methods = [
            "get_history_data",
            "get_current_price",
            "get_snapshot",
            "get_multiple_history_data",
        ]
        return all(
            hasattr(plugin_instance, method)
            and callable(getattr(plugin_instance, method))
            for method in required_methods
        )

    def _is_indicators_plugin(self, plugin_instance: Any) -> bool:
        """判断插件是否为技术指标插件"""
        # 通过多种条件识别技术指标插件
        is_indicators_plugin = (
            # 通过名称识别
            (
                hasattr(plugin_instance, "metadata")
                and plugin_instance.metadata.name == "technical_indicators_plugin"
            )
            # 通过category识别
            or (
                hasattr(plugin_instance, "metadata")
                and hasattr(plugin_instance.metadata, "category")
                and plugin_instance.metadata.category in ["indicators", "analysis"]
            )
            # 通过标签识别
            or (
                hasattr(plugin_instance, "metadata")
                and hasattr(plugin_instance.metadata, "tags")
                and "indicators" in plugin_instance.metadata.tags
            )
            # 通过方法识别
            or (
                hasattr(plugin_instance, "calculate_macd")
                and hasattr(plugin_instance, "calculate_kdj")
                and hasattr(plugin_instance, "calculate_rsi")
                and hasattr(plugin_instance, "calculate_cci")
            )
        )
        return is_indicators_plugin

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

    def handle_data(self, data: Dict[str, Any]) -> None:
        """研究模式数据处理"""
        # 研究模式主要用于数据分析，不涉及交易
        pass

    # ==============================================
    # 数据获取API - 通过数据插件实现
    # ==============================================

    def get_history(
        self,
        count: Optional[int] = None,
        frequency: str = "1d",
        field: Optional[Union[str, List[str]]] = None,
        security_list: Optional[List[str]] = None,
        fq: str = "pre",
        include: bool = True,
        fill: bool = True,
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Union[Any, Dict[str, Any]]:
        """获取历史行情数据 - 通过数据插件"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_history_data"):
            try:
                # 处理参数：如果只有一个证券且以字符串形式传递
                if security_list and len(security_list) == 1:
                    security = security_list[0]
                    count_val = count or 10

                    # 使用数据插件获取历史数据
                    df_result = data_plugin.get_history_data(security, count_val)

                    if not df_result.empty:
                        if is_dict:
                            # 转换为字典格式
                            return df_result.to_dict("records")
                        else:
                            return df_result
                    else:
                        return {} if is_dict else pd.DataFrame()
                else:
                    # 多证券处理
                    if security_list and count:
                        all_data = []
                        for security in security_list:
                            df_result = data_plugin.get_history_data(security, count)
                            if not df_result.empty:
                                all_data.append(df_result)

                        if all_data:
                            combined_df = pd.concat(all_data, ignore_index=True)
                            return (
                                combined_df.to_dict("records")
                                if is_dict
                                else combined_df
                            )

                    return {} if is_dict else pd.DataFrame()
            except Exception as e:
                self._logger.warning(f"Data plugin get_history failed: {e}")

        # 回退到父类的默认实现
        return super().get_history(
            count,
            frequency,
            field,
            security_list,
            fq,
            include,
            fill,
            is_dict,
            start_date,
            end_date,
        )

    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取当前行情快照 - 通过数据插件"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_snapshot"):
            try:
                # 使用数据插件获取行情快照
                snapshot = data_plugin.get_snapshot(security_list)
                if snapshot:
                    # 转换为DataFrame格式
                    rows = []
                    for security, data_dict in snapshot.items():
                        row = {"security": security}
                        row.update(data_dict)
                        rows.append(row)
                    return pd.DataFrame(rows)
                else:
                    return pd.DataFrame()
            except Exception as e:
                self._logger.warning(f"Data plugin get_snapshot failed: {e}")

        # 回退到父类的默认实现
        return super().get_snapshot(security_list)

    def get_price(
        self,
        security: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> Union[Any, float]:
        """获取价格数据 - 通过数据插件"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_history_data") and security:
            try:
                # 处理单个证券的情况
                if isinstance(security, str):
                    count_val = count or 1
                    df_result = data_plugin.get_history_data(security, count_val)

                    if not df_result.empty:
                        # 返回最新的收盘价
                        return float(df_result.iloc[-1]["close"])
                    else:
                        return 0.0
                # 处理多个证券的情况（返回字典）
                elif isinstance(security, list):
                    count_val = count or 1
                    prices = {}
                    for sec in security:
                        df_result = data_plugin.get_history_data(sec, count_val)
                        if not df_result.empty:
                            prices[sec] = float(df_result.iloc[-1]["close"])
                        else:
                            prices[sec] = 0.0
                    return prices
            except Exception as e:
                self._logger.warning(f"Data plugin get_price failed: {e}")

        # 回退到父类的默认实现
        return super().get_price(
            security, start_date, end_date, frequency, fields, count
        )

    def get_current_data(
        self, security_list: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """获取当前数据 - 策略中data参数的数据源"""
        if security_list is None:
            # 如果没有指定股票列表，使用上下文中的universe
            security_list = list(self.context.universe) if self.context.universe else []

        if not security_list:
            return {}

        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_snapshot"):
            try:
                # 使用数据插件获取行情快照
                snapshot = data_plugin.get_snapshot(security_list)

                # 转换为策略期望的格式: {security: {field: value}}
                current_data: Dict[str, Dict[str, Any]] = {}
                for security, data_dict in snapshot.items():
                    current_data[security] = {
                        "price": data_dict.get(
                            "price", data_dict.get("last_price", 0.0)
                        ),
                        "close": data_dict.get(
                            "last_price", data_dict.get("price", 0.0)
                        ),
                        "open": data_dict.get("open", 0.0),
                        "high": data_dict.get("high", 0.0),
                        "low": data_dict.get("low", 0.0),
                        "volume": data_dict.get("volume", 0),
                        "money": data_dict.get("money", 0.0),
                    }

                return current_data
            except Exception as e:
                self._logger.warning(f"Data plugin get_current_data failed: {e}")

        # 如果数据插件不可用，返回空字典
        return {}

    # ==============================================
    # 技术指标API - 通过插件系统实现
    # ==============================================

    def get_MACD(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标 - 通过技术指标插件"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_macd"):
            try:
                # 使用插件计算MACD
                return indicators_plugin.calculate_macd(close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin MACD calculation failed: {e}")

        # 如果插件不可用，调用父类默认实现
        return super().get_MACD(close, short, long, m)

    def get_KDJ(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标 - 通过技术指标插件"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_kdj"):
            try:
                # 使用插件计算KDJ
                return indicators_plugin.calculate_kdj(high, low, close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin KDJ calculation failed: {e}")

        # 如果插件不可用，调用父类默认实现
        return super().get_KDJ(high, low, close, n, m1, m2)

    def get_RSI(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标 - 通过技术指标插件"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_rsi"):
            try:
                # 使用插件计算RSI
                return indicators_plugin.calculate_rsi(close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin RSI calculation failed: {e}")

        # 如果插件不可用，调用父类默认实现
        return super().get_RSI(close, n)

    def get_CCI(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标 - 通过技术指标插件"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_cci"):
            try:
                # 使用插件计算CCI
                return indicators_plugin.calculate_cci(high, low, close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin CCI calculation failed: {e}")

        # 如果插件不可用，调用父类默认实现
        return super().get_CCI(high, low, close, n)

    def log(self, *args: Any, **kwargs: Any) -> None:
        """日志记录 - 研究模式不支持"""
        raise NotImplementedError("log function is not supported in research mode")
