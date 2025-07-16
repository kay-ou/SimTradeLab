# -*- coding: utf-8 -*-
"""
PTrade API 路由器基类

定义完整的 PTrade API 接口规范
"""

import logging
from typing import Any, Dict, Hashable, List, Optional, Union

import numpy as np
import pandas as pd

from ....core.event_bus import EventBus
from ..api_validator import APIValidator, get_api_validator
from ..context import PTradeContext
from ..lifecycle_controller import LifecycleController, get_lifecycle_controller
from ..models import Order, Position


class BaseAPIRouter:
    """API路由器基类 - 定义完整的 PTrade API 接口"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        lifecycle_controller: Optional[LifecycleController] = None,
        api_validator: Optional[APIValidator] = None,
        plugin_manager: Optional[Any] = None,
    ):
        self.context = context
        self.event_bus = event_bus
        self._logger = logging.getLogger(self.__class__.__name__)
        self._plugin_manager = plugin_manager  # 插件管理器引用

        # 获取策略模式，确保是字符串格式
        strategy_mode = getattr(context, "mode", "backtest")
        if hasattr(strategy_mode, "value"):
            strategy_mode = strategy_mode.value

        # 生命周期控制和API验证
        self._lifecycle_controller = lifecycle_controller or get_lifecycle_controller()
        self._api_validator = api_validator or get_api_validator(strategy_mode)

        # 设置策略模式
        self._lifecycle_controller._strategy_mode = strategy_mode
        self._api_validator.set_strategy_mode(strategy_mode)

        self._logger.info(f"BaseAPIRouter initialized for {strategy_mode} mode")

    # ==========================================
    # 通用API验证和执行方法
    # ==========================================

    def validate_and_execute(
        self, api_name: str, method_func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """验证并执行API调用

        集成了PTrade生命周期验证和API参数验证
        """
        if not self.is_mode_supported(api_name):
            raise ValueError(f"API '{api_name}' is not supported in current mode")

        validation_result = self._api_validator.validate_api_call(
            api_name, *args, **kwargs
        )

        if not validation_result.is_valid:
            self._logger.error(
                f"API validation failed for '{api_name}': "
                f"{validation_result.error_message}"
            )
            raise ValueError(validation_result.error_message)

        try:
            result = method_func(*args, **kwargs)
            self._logger.debug(f"API '{api_name}' executed successfully")
            return result
        except Exception as e:
            self._logger.error(f"API '{api_name}' execution failed: {e}")
            raise

    # ==========================================
    # 交易相关 API (核心方法)
    # ==========================================

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """下单"""
        raise NotImplementedError(
            f"order method not implemented in {self.__class__.__name__}"
        )

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        raise NotImplementedError(
            f"order_value method not implemented in {self.__class__.__name__}"
        )

    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定目标数量买卖"""
        raise NotImplementedError(
            f"order_target method not implemented in {self.__class__.__name__}"
        )

    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定持仓市值买卖"""
        raise NotImplementedError(
            f"order_target_value method not implemented in {self.__class__.__name__}"
        )

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托"""
        raise NotImplementedError(
            f"order_market method not implemented in {self.__class__.__name__}"
        )

    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        raise NotImplementedError(
            f"cancel_order method not implemented in {self.__class__.__name__}"
        )

    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展"""
        raise NotImplementedError(
            f"cancel_order_ex method not implemented in {self.__class__.__name__}"
        )

    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        raise NotImplementedError(
            f"get_all_orders method not implemented in {self.__class__.__name__}"
        )

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        raise NotImplementedError(
            f"ipo_stocks_order method not implemented in {self.__class__.__name__}"
        )

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        raise NotImplementedError(
            f"after_trading_order method not implemented in {self.__class__.__name__}"
        )

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        raise NotImplementedError(
            f"after_trading_cancel_order method not implemented in "
            f"{self.__class__.__name__}"
        )

    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓信息"""
        raise NotImplementedError(
            f"get_position method not implemented in {self.__class__.__name__}"
        )

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息"""
        raise NotImplementedError(
            f"get_positions method not implemented in {self.__class__.__name__}"
        )

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单"""
        raise NotImplementedError(
            f"get_open_orders method not implemented in {self.__class__.__name__}"
        )

    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定订单"""
        raise NotImplementedError(
            f"get_order method not implemented in {self.__class__.__name__}"
        )

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取全部订单"""
        raise NotImplementedError(
            f"get_orders method not implemented in {self.__class__.__name__}"
        )

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单"""
        raise NotImplementedError(
            f"get_trades method not implemented in {self.__class__.__name__}"
        )

    # ==========================================
    # 行情数据 API (插件化实现)
    # ==========================================

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
        """获取历史行情数据"""
        raise NotImplementedError(
            f"get_history method not implemented in {self.__class__.__name__}"
        )

    def get_price(
        self,
        security: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> Union[pd.DataFrame, pd.Series, float, Dict[str, float]]:
        """获取价格数据"""
        raise NotImplementedError(
            f"get_price method not implemented in {self.__class__.__name__}"
        )

    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
        raise NotImplementedError(
            f"get_snapshot method not implemented in {self.__class__.__name__}"
        )

    # ==========================================
    # 基础信息 API (默认实现)
    # ==========================================

    def get_trading_day(self, date: str, offset: int = 0) -> str:
        """获取交易日期"""
        return date

    def get_all_trades_days(self) -> List[str]:
        """获取全部交易日期"""
        return []

    def get_trade_days(self, start_date: str, end_date: str) -> List[str]:
        """获取指定范围交易日期"""
        return []

    # ==========================================
    # 股票信息 API (默认实现)
    # ==========================================

    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息"""
        return {}

    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息"""
        raise NotImplementedError(
            f"get_fundamentals method not implemented in {self.__class__.__name__}"
        )

    def get_stock_name(self, security: str) -> str:
        """获取股票名称"""
        return security  # 默认返回股票代码

    def get_stock_status(self, security: str) -> Dict[str, Any]:
        """获取股票状态信息"""
        return {}  # 默认返回空字典

    def get_stock_exrights(self, security: str) -> pd.DataFrame:
        """获取股票除权除息信息"""
        return pd.DataFrame()  # 默认返回空DataFrame

    def get_stock_blocks(self, security: str) -> List[str]:
        """获取股票所属板块信息"""
        return []  # 默认返回空列表

    def get_index_stocks(self, index_code: str) -> List[str]:
        """获取指数成份股"""
        return []  # 默认返回空列表

    def get_industry_stocks(self, industry_code: str) -> List[str]:
        """获取行业成份股"""
        return []  # 默认返回空列表

    def get_Ashares(self, date: str) -> List[str]:
        """获取指定日期A股代码列表"""
        return []  # 默认返回空列表

    def get_etf_list(self) -> List[str]:
        """获取ETF代码列表"""
        return []  # 默认返回空列表

    def get_ipo_stocks(self, date: str) -> List[str]:
        """获取当日IPO申购标的"""
        return []  # 默认返回空列表

    # ==========================================
    # 设置相关 API (默认实现)
    # ==========================================

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

    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        self._logger.warning("set_commission should be implemented in subclass")

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        self._logger.warning("set_slippage should be implemented in subclass")

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        self._logger.warning("set_fixed_slippage should be implemented in subclass")

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        self._logger.warning("set_volume_ratio should be implemented in subclass")

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        self._logger.warning("set_limit_mode should be implemented in subclass")

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        self._logger.warning("set_yesterday_position should be implemented in subclass")

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        if not hasattr(self.context, "_parameters"):
            setattr(self.context, "_parameters", {})
        getattr(self.context, "_parameters").update(params)
        self._logger.info(f"Parameters set: {params}")

    # ==========================================
    # 技术指标 API (默认实现)
    # ==========================================

    def get_MACD(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标 - 通过技术指标插件实现"""
        return self.validate_and_execute(
            "get_MACD", self._get_MACD_impl, close, short, long, m
        )

    def _get_MACD_impl(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标的实际实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_macd"):
            try:
                # 使用插件计算MACD
                return indicators_plugin.calculate_macd(close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin MACD calculation failed: {e}")

        # 默认返回空DataFrame
        return pd.DataFrame()

    def get_KDJ(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标 - 通过技术指标插件实现"""
        return self.validate_and_execute(
            "get_KDJ", self._get_KDJ_impl, high, low, close, n, m1, m2
        )

    def _get_KDJ_impl(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标的实际实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_kdj"):
            try:
                # 使用插件计算KDJ
                return indicators_plugin.calculate_kdj(high, low, close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin KDJ calculation failed: {e}")

        # 默认返回空DataFrame
        return pd.DataFrame()

    def get_RSI(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标 - 通过技术指标插件实现"""
        return self.validate_and_execute("get_RSI", self._get_RSI_impl, close, n)

    def _get_RSI_impl(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标的实际实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_rsi"):
            try:
                # 使用插件计算RSI
                return indicators_plugin.calculate_rsi(close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin RSI calculation failed: {e}")

        # 默认返回空DataFrame
        return pd.DataFrame()

    def get_CCI(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标 - 通过技术指标插件实现"""
        return self.validate_and_execute(
            "get_CCI", self._get_CCI_impl, high, low, close, n
        )

    def _get_CCI_impl(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标的实际实现"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_cci"):
            try:
                # 使用插件计算CCI
                return indicators_plugin.calculate_cci(high, low, close)
            except Exception as e:
                self._logger.warning(f"Indicators plugin CCI calculation failed: {e}")

        # 默认返回空DataFrame
        return pd.DataFrame()

    # ==========================================
    # 工具函数 API (默认实现)
    # ==========================================

    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, bool]:
        """代码涨跌停状态判断"""
        return {"is_up_limit": False, "is_down_limit": False}  # 默认返回未涨跌停

    def log(self, *args: Any, **kwargs: Any) -> None:
        """日志记录"""
        self._logger.info(" ".join(str(arg) for arg in args))

    def is_trade(self) -> bool:
        """业务代码场景判断"""
        return hasattr(self.context, "mode") and self.context.mode.value == "trading"

    # ==========================================
    # 定时和回调 API (子类实现)
    # ==========================================

    def run_daily(
        self, func: Any, time_str: str = "09:30", *args: Any, **kwargs: Any
    ) -> str:
        """按日周期处理 - 每日定时执行指定函数"""
        raise NotImplementedError(
            f"run_daily method not implemented in {self.__class__.__name__}"
        )

    def run_interval(
        self, func: Any, interval: Union[int, str], *args: Any, **kwargs: Any
    ) -> str:
        """按设定周期处理 - 按指定间隔重复执行函数"""
        raise NotImplementedError(
            f"run_interval method not implemented in {self.__class__.__name__}"
        )

    def tick_data(self, func: Any) -> bool:
        """tick级别处理 - 注册tick数据回调函数"""
        raise NotImplementedError(
            f"tick_data method not implemented in {self.__class__.__name__}"
        )

    def on_order_response(self, func: Any) -> bool:
        """委托回报 - 注册订单状态变化回调函数"""
        raise NotImplementedError(
            f"on_order_response method not implemented in {self.__class__.__name__}"
        )

    def on_trade_response(self, func: Any) -> bool:
        """成交回报 - 注册成交确认回调函数"""
        raise NotImplementedError(
            f"on_trade_response method not implemented in {self.__class__.__name__}"
        )

    def handle_data(self, data: Dict[str, Any]) -> None:
        """处理市场数据"""
        raise NotImplementedError(
            f"handle_data method not implemented in {self.__class__.__name__}"
        )

    # ==========================================
    # 模式支持检查 (子类必须实现)
    # ==========================================

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在当前模式下支持"""
        # 使用API验证器检查模式支持
        if self._api_validator:
            try:
                mode_result = self._api_validator._validate_mode_restriction(api_name)
                return mode_result.is_valid
            except Exception as e:
                self._logger.warning(f"Mode validation error for {api_name}: {e}")
                return True  # 默认允许，向后兼容

        # 如果没有验证器，默认允许所有API
        return True
