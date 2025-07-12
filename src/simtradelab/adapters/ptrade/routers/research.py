# -*- coding: utf-8 -*-
"""
PTrade研究模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Optional, Union

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
        super().__init__(
            context, event_bus, lifecycle_controller, api_validator, plugin_manager
        )
        self._scheduler = PTradeScheduler(event_bus)  # 初始化调度器

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
        # 使用统一配置中心检查模式支持
        from ..lifecycle_config import is_api_supported_in_mode

        return is_api_supported_in_mode(api_name, "research")

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

    # 研究模式下的配置方法需要通过验证器
    def set_commission(self, commission: float) -> None:
        """设置佣金费率 - 研究模式下不支持，需要通过父类的验证"""
        return self.validate_and_execute(
            "set_commission", super().set_commission, commission
        )

    def set_slippage(self, slippage: float) -> None:
        """设置滑点 - 研究模式下不支持，需要通过父类的验证"""
        return self.validate_and_execute(
            "set_slippage", super().set_slippage, slippage
        )

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点 - 研究模式下不支持，需要通过父类的验证"""
        return self.validate_and_execute(
            "set_fixed_slippage", super().set_fixed_slippage, slippage
        )

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例 - 研究模式下不支持，需要通过父类的验证"""
        return self.validate_and_execute(
            "set_volume_ratio", super().set_volume_ratio, ratio
        )

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式 - 研究模式下不支持，需要通过父类的验证"""
        return self.validate_and_execute(
            "set_limit_mode", super().set_limit_mode, mode
        )

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓 - 研究模式下不支持，需要通过父类的验证"""
        return self.validate_and_execute(
            "set_yesterday_position", super().set_yesterday_position, positions
        )

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数 - 研究模式下不支持，需要通过父类的验证"""
        # 调用父类的set_parameters，这会触发validate_and_execute验证
        return self.validate_and_execute(
            "set_parameters", super().set_parameters, params
        )

    def set_universe(self, securities: List[str]) -> None:
        """设置股票池 - 研究模式下不支持，需要通过父类的验证"""
        # 调用父类的set_universe，这会触发validate_and_execute验证
        return self.validate_and_execute(
            "set_universe", super().set_universe, securities
        )

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准 - 研究模式下不支持，需要通过父类的验证"""
        # 调用父类的set_benchmark，这会触发validate_and_execute验证
        return self.validate_and_execute(
            "set_benchmark", super().set_benchmark, benchmark
        )

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
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[Hashable, Any]]]:
        """获取历史行情数据 - 研究模式下不支持，需要通过父类的验证"""
        # 调用父类的get_history，这会触发validate_and_execute验证
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
    ) -> Union[pd.DataFrame, pd.Series, float, Dict[str, float]]:
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
        """获取MACD指标 - 研究模式模拟实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_macd"):
            try:
                # 使用插件计算MACD
                result = indicators_plugin.calculate_macd(close)
                # 确保返回DataFrame而不是MagicMock
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin MACD calculation failed: {e}")

        # 如果插件不可用或返回非DataFrame，调用父类默认实现
        return super()._get_MACD_impl(close, short, long, m)

    def get_KDJ(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标 - 研究模式模拟实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_kdj"):
            try:
                # 使用插件计算KDJ
                result = indicators_plugin.calculate_kdj(high, low, close)
                # 确保返回DataFrame而不是MagicMock
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin KDJ calculation failed: {e}")

        # 如果插件不可用或返回非DataFrame，调用父类默认实现
        return super()._get_KDJ_impl(high, low, close, n, m1, m2)

    def get_RSI(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标 - 研究模式模拟实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_rsi"):
            try:
                # 使用插件计算RSI
                result = indicators_plugin.calculate_rsi(close)
                # 确保返回DataFrame而不是MagicMock
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin RSI calculation failed: {e}")

        # 如果插件不可用或返回非DataFrame，调用父类默认实现
        return super()._get_RSI_impl(close, n)

    def get_CCI(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标 - 研究模式模拟实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_cci"):
            try:
                # 使用插件计算CCI
                result = indicators_plugin.calculate_cci(high, low, close)
                # 确保返回DataFrame而不是MagicMock
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin CCI calculation failed: {e}")

        # 如果插件不可用或返回非DataFrame，调用父类默认实现
        return super()._get_CCI_impl(high, low, close, n)

    # ==============================================
    # 股票信息和工具API - 直接使用父类实现
    # ==============================================
    
    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息 - 研究模式模拟实现"""
        result = {}
        for security in security_list:
            if security.endswith(".XSHE"):
                market = "SZSE"
            elif security.endswith(".XSHG"):
                market = "SSE"
            else:
                market = "UNKNOWN"
            
            result[security] = {
                "market": market,
                "type": "stock",
                "name": f"股票{security[:6]}",
                "listed_date": "2000-01-01",
                "delist_date": None
            }
        return result

    def get_trading_day(self, date: str, offset: int = 0) -> str:
        """获取交易日期 - 研究模式模拟实现"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_trading_day"):
            try:
                return data_plugin.get_trading_day(date, offset)
            except Exception as e:
                self._logger.warning(f"Data plugin get_trading_day failed: {e}")
        # 默认返回原日期
        return date
        
    def get_all_trades_days(self) -> List[str]:
        """获取全部交易日期 - 研究模式模拟实现"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_all_trading_days"):
            try:
                return data_plugin.get_all_trading_days()
            except Exception as e:
                self._logger.warning(f"Data plugin get_all_trading_days failed: {e}")
        # 默认返回模拟数据
        return ["2023-01-03", "2023-01-04", "2023-01-05"]
        
    def get_trade_days(self, start_date: str, end_date: str) -> List[str]:
        """获取指定范围交易日期 - 研究模式模拟实现"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_trading_days_range"):
            try:
                return data_plugin.get_trading_days_range(start_date, end_date)
            except Exception as e:
                self._logger.warning(f"Data plugin get_trading_days_range failed: {e}")
        # 默认返回模拟数据
        return ["2023-12-25", "2023-12-26", "2023-12-27", "2023-12-28", "2023-12-29"]

    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, bool]:
        """代码涨跌停状态判断 - 研究模式模拟实现"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "check_limit_status"):
            try:
                limit_data = data_plugin.check_limit_status([security])
                if security in limit_data:
                    security_limit_data = limit_data[security]
                    return {
                        security: {
                            "limit_up": security_limit_data.get("limit_up", False),
                            "limit_down": security_limit_data.get("limit_down", False),
                            "limit_up_price": security_limit_data.get("limit_up_price", 0.0),
                            "limit_down_price": security_limit_data.get("limit_down_price", 0.0),
                            "current_price": security_limit_data.get("current_price", 0.0),
                        }
                    }
            except Exception as e:
                self._logger.warning(f"Data plugin check_limit_status failed: {e}")
        
        # 默认返回模拟数据（无涨跌停）
        return {
            security: {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": 16.5,
                "limit_down_price": 13.5,
                "current_price": 15.0,
            }
        }
        
    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息 - 研究模式模拟实现"""
        data_plugin = self._get_data_plugin()
        if data_plugin and hasattr(data_plugin, "get_fundamentals"):
            try:
                # 使用数据插件获取财务数据
                result = data_plugin.get_fundamentals(stocks, table, fields, date)
                if not result.empty:
                    return result
            except Exception as e:
                self._logger.warning(f"Data plugin get_fundamentals failed: {e}")

        # 默认返回模拟基本面数据
        if not stocks:
            # 如果没有股票，返回空DataFrame但包含必要列
            basic_columns = ["code", "date"] + fields
            return pd.DataFrame(columns=basic_columns)
        
        if not fields:
            # 如果没有字段但有股票，返回只包含基本信息的DataFrame
            rows = []
            for stock in stocks:
                row = {"code": stock, "date": date}
                rows.append(row)
            return pd.DataFrame(rows)
        
        # 生成模拟基本面数据
        rows = []
        for stock in stocks:
            row = {"code": stock, "date": date}
            # 为每个字段生成默认值
            for field in fields:
                if field in ["revenue", "total_assets", "total_liab"]:
                    row[field] = 0.0  # 金额类字段默认为0
                elif field in ["pe_ratio", "pb_ratio", "roe", "eps"]:
                    row[field] = 0.0  # 比率类字段默认为0
                else:
                    row[field] = 0.0  # 其他字段默认为0
            rows.append(row)
        
        return pd.DataFrame(rows)

    def log(self, *args: Any, **kwargs: Any) -> None:
        """日志记录 - 研究模式不支持"""
        raise NotImplementedError("log function is not supported in research mode")
