# -*- coding: utf-8 -*-
"""
PTrade基础路由器测试

测试BaseAPIRouter抽象基类的功能
"""

from typing import Any, Dict, List, Optional, Union

import pytest

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio
from simtradelab.adapters.ptrade.routers.base import BaseAPIRouter
from simtradelab.core.event_bus import EventBus


class ConcreteAPIRouter(BaseAPIRouter):
    """具体实现的API路由器用于测试"""

    def __init__(
        self, context: PTradeContext, event_bus: Optional[EventBus] = None
    ) -> None:
        super().__init__(context, event_bus)
        self._supported_apis = {"get_history", "get_price", "order", "log"}

    # 交易相关API实现（简化版）
    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> str:
        return f"order_{security}_{amount}"

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> str:
        return f"order_value_{security}_{value}"

    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> str:
        return f"order_target_{security}_{target_amount}"

    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> str:
        return f"order_target_value_{security}_{target_value}"

    def order_market(self, security: str, amount: int) -> str:
        return f"order_market_{security}_{amount}"

    def cancel_order(self, order_id: str) -> bool:
        return True

    def cancel_order_ex(self, order_id: str) -> bool:
        return True

    def get_all_orders(self) -> List[Any]:
        return []

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[Any]:
        return []

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> str:
        return f"after_trading_order_{security}"

    def after_trading_cancel_order(self, order_id: str) -> bool:
        return True

    def get_position(self, security: str) -> Optional[Any]:
        return None

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        return {}

    def get_open_orders(self, security: Optional[str] = None) -> List[Any]:
        return []

    def get_order(self, order_id: str) -> Optional[Any]:
        return None

    def get_orders(self, security: Optional[str] = None) -> List[Any]:
        return []

    def get_trades(self, security: Optional[str] = None) -> List[Any]:
        return []

    # 数据获取API实现（简化版）
    def get_history(
        self,
        count: int,
        frequency: str = "1d",
        field: Optional[Union[str, List[str]]] = None,
        security_list: Optional[List[str]] = None,
        fq: Optional[str] = None,
        include: bool = True,
        fill: str = "ffill",
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[Any, Dict[str, Any]]:
        return f"history_data_{count}_{frequency}"

    def get_price(
        self,
        security: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        if isinstance(security, list):
            security_str = ",".join(security)
        else:
            security_str = security
        return f"price_data_{security_str}"

    def get_snapshot(self, security_list: List[str]) -> str:
        return f"snapshot_data_{len(security_list)}"

    def get_trading_day(self, date: str, offset: int = 0) -> str:
        return "2023-12-29"

    def get_all_trades_days(self) -> List[str]:
        return ["2023-12-28", "2023-12-29"]

    def get_trade_days(self, start_date: str, end_date: str) -> List[str]:
        return ["2023-12-28", "2023-12-29"]

    def get_stock_info(self, security_list: List[str]) -> Dict[str, Dict[str, str]]:
        return {sec: {"name": f"Stock_{sec}"} for sec in security_list}

    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> str:
        return f"fundamentals_{table}_{date}"

    # 股票信息API实现（简化版）
    def get_stock_name(self, security: str) -> str:
        return f"Name_{security}"

    def get_stock_status(self, security: str) -> Dict[str, str]:
        return {"status": "normal"}

    def get_stock_exrights(self, security: str) -> str:
        return f"exrights_{security}"

    def get_stock_blocks(self, security: str) -> List[str]:
        return [f"block1_{security}"]

    def get_index_stocks(self, index_code: str) -> List[str]:
        return [f"stock1_{index_code}"]

    def get_industry_stocks(self, industry_code: str) -> List[str]:
        return [f"stock1_{industry_code}"]

    def get_Ashares(self, date: str) -> List[str]:
        return [f"ashare_{date}"]

    def get_etf_list(self) -> List[str]:
        return ["etf1", "etf2"]

    def get_ipo_stocks(self, date: str) -> List[str]:
        return [f"ipo_{date}"]

    # 设置函数API实现（简化版）
    def set_universe(self, securities: List[str]) -> None:
        self.context.universe = securities

    def set_benchmark(self, benchmark: str) -> None:
        self.context.benchmark = benchmark

    def set_commission(self, commission: float) -> None:
        pass

    def set_slippage(self, slippage: float) -> None:
        pass

    def set_fixed_slippage(self, slippage: float) -> None:
        pass

    def set_volume_ratio(self, ratio: float) -> None:
        pass

    def set_limit_mode(self, mode: str) -> None:
        pass

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        pass

    def set_parameters(self, params: Dict[str, Any]) -> None:
        pass

    # 计算函数API实现（简化版）
    def get_MACD(self, close: Any, short: int = 12, long: int = 26, m: int = 9) -> str:
        return "macd_result"

    def get_KDJ(
        self, high: Any, low: Any, close: Any, n: int = 9, m1: int = 3, m2: int = 3
    ) -> str:
        return "kdj_result"

    def get_RSI(self, close: Any, n: int = 6) -> str:
        return "rsi_result"

    def get_CCI(self, high: Any, low: Any, close: Any, n: int = 14) -> str:
        return "cci_result"

    # 工具函数API实现（简化版）
    def log(self, content: str, level: str = "info") -> None:
        pass

    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Dict[str, bool]]:
        return {security: {"limit_up": False, "limit_down": False}}

    # 定时和回调API实现（简化版）
    def run_daily(
        self, func: Any, time_str: str = "09:30", *args: Any, **kwargs: Any
    ) -> str:
        return f"daily_job_{func.__name__}"

    def run_interval(
        self, func: Any, interval: Union[int, str], *args: Any, **kwargs: Any
    ) -> str:
        return f"interval_job_{func.__name__}"

    def tick_data(self, func: Any) -> bool:
        return True

    def on_order_response(self, func: Any) -> bool:
        return True

    def on_trade_response(self, func: Any) -> bool:
        return True

    # 模式相关的处理方法
    def handle_data(self, data: Any) -> None:
        pass

    def is_mode_supported(self, api_name: str) -> bool:
        return api_name in self._supported_apis


class TestBaseAPIRouter:
    """测试基础API路由器"""

    @pytest.fixture
    def context(self) -> PTradeContext:
        """创建测试上下文"""
        portfolio = Portfolio(cash=1000000)
        blotter = Blotter()
        context = PTradeContext(portfolio=portfolio, blotter=blotter)
        context.universe = ["000001.XSHE", "000002.XSHE"]
        context.benchmark = "000300.SH"
        return context

    @pytest.fixture
    def event_bus(self) -> EventBus:
        """创建事件总线"""
        return EventBus()

    @pytest.fixture
    def router(self, context: PTradeContext, event_bus: EventBus) -> ConcreteAPIRouter:
        """创建路由器实例"""
        return ConcreteAPIRouter(context=context, event_bus=event_bus)

    def test_router_initialization(
        self, router: ConcreteAPIRouter, context: PTradeContext, event_bus: EventBus
    ) -> None:
        """测试路由器初始化"""
        assert router.context is context
        assert router.event_bus is event_bus
        assert hasattr(router, "_logger")
        assert router._logger is not None

    def test_router_initialization_without_event_bus(
        self, context: PTradeContext
    ) -> None:
        """测试无事件总线的路由器初始化"""
        router = ConcreteAPIRouter(context=context)
        assert router.context is context
        assert router.event_bus is None

    def test_base_class_instantiation(self) -> None:
        """测试基类可以直接实例化（现在是具体类）"""
        portfolio = Portfolio(cash=1000000)
        blotter = Blotter()
        context = PTradeContext(portfolio=portfolio, blotter=blotter)

        # BaseAPIRouter 现在是具体类，应该可以实例化
        router = BaseAPIRouter(context=context)
        assert router is not None
        assert router.context is context

    def test_validate_and_execute_supported_api(
        self, router: ConcreteAPIRouter
    ) -> None:
        """测试验证并执行支持的API"""

        # 模拟一个支持的API方法
        def mock_method(count: int) -> str:
            return f"executed_count_{count}"

        result = router.validate_and_execute("get_history", mock_method, count=20)

        assert result == "executed_count_20"

    def test_validate_and_execute_unsupported_api(
        self, router: ConcreteAPIRouter
    ) -> None:
        """测试验证并执行不支持的API"""

        def mock_method() -> str:
            return "should_not_execute"

        with pytest.raises(ValueError, match="API 'unsupported_api' is not supported"):
            router.validate_and_execute("unsupported_api", mock_method)

    def test_validate_and_execute_with_exception(
        self, router: ConcreteAPIRouter
    ) -> None:
        """测试验证并执行时的异常处理"""

        def error_method() -> None:
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            router.validate_and_execute("get_history", error_method)

    def test_all_trading_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有交易API都已定义"""
        trading_apis = [
            "order",
            "order_value",
            "order_target",
            "order_target_value",
            "order_market",
            "cancel_order",
            "cancel_order_ex",
            "get_all_orders",
            "ipo_stocks_order",
            "after_trading_order",
            "after_trading_cancel_order",
            "get_position",
            "get_positions",
            "get_open_orders",
            "get_order",
            "get_orders",
            "get_trades",
        ]

        for api in trading_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_all_data_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有数据API都已定义"""
        data_apis = [
            "get_history",
            "get_price",
            "get_snapshot",
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            "get_stock_info",
            "get_fundamentals",
        ]

        for api in data_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_all_stock_info_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有股票信息API都已定义"""
        stock_info_apis = [
            "get_stock_name",
            "get_stock_status",
            "get_stock_exrights",
            "get_stock_blocks",
            "get_index_stocks",
            "get_industry_stocks",
            "get_Ashares",
            "get_etf_list",
            "get_ipo_stocks",
        ]

        for api in stock_info_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_all_settings_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有设置API都已定义"""
        settings_apis = [
            "set_universe",
            "set_benchmark",
            "set_commission",
            "set_slippage",
            "set_fixed_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
            "set_parameters",
        ]

        for api in settings_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_all_calculation_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有计算API都已定义"""
        calculation_apis = ["get_MACD", "get_KDJ", "get_RSI", "get_CCI"]

        for api in calculation_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_all_utility_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有工具API都已定义"""
        utility_apis = ["log", "check_limit"]

        for api in utility_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_all_timing_callback_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试所有定时和回调API都已定义"""
        timing_apis = [
            "run_daily",
            "run_interval",
            "tick_data",
            "on_order_response",
            "on_trade_response",
        ]

        for api in timing_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_framework_apis_defined(self, router: ConcreteAPIRouter) -> None:
        """测试框架API都已定义"""
        framework_apis = ["handle_data", "is_mode_supported"]

        for api in framework_apis:
            assert hasattr(router, api)
            assert callable(getattr(router, api))

    def test_basic_trading_operations(self, router: ConcreteAPIRouter) -> None:
        """测试基本交易操作"""
        # 测试下单
        order_id = router.order("000001.XSHE", 1000, 10.0)
        assert "order_000001.XSHE_1000" in order_id

        # 测试按价值下单
        order_id = router.order_value("000001.XSHE", 50000, 10.0)
        assert "order_value_000001.XSHE_50000" in order_id

        # 测试撤单
        result = router.cancel_order("test_order_id")
        assert result is True

    def test_basic_data_operations(self, router: ConcreteAPIRouter) -> None:
        """测试基本数据操作"""
        # 测试获取历史数据
        history = router.get_history(count=10)
        assert "history_data_10_1d" in history

        # 测试获取价格
        price = router.get_price("000001.XSHE")
        assert "price_data_000001.XSHE" in price

        # 测试获取快照
        snapshot = router.get_snapshot(["000001.XSHE", "000002.XSHE"])
        assert "snapshot_data_2" in snapshot

    def test_basic_settings_operations(self, router: ConcreteAPIRouter) -> None:
        """测试基本设置操作"""
        # 测试设置股票池
        securities = ["000001.XSHE", "000002.XSHE"]
        router.set_universe(securities)
        assert router.context.universe == securities

        # 测试设置基准
        benchmark = "000300.SH"
        router.set_benchmark(benchmark)
        assert router.context.benchmark == benchmark

    def test_basic_calculation_operations(self, router: ConcreteAPIRouter) -> None:
        """测试基本计算操作"""
        import numpy as np

        close_data = np.array([10.0, 10.1, 10.2, 9.9, 10.3])

        # 测试MACD
        macd = router.get_MACD(close_data)
        assert macd == "macd_result"

        # 测试RSI
        rsi = router.get_RSI(close_data)
        assert rsi == "rsi_result"

    def test_basic_utility_operations(self, router: ConcreteAPIRouter) -> None:
        """测试基本工具操作"""
        # 测试日志
        router.log("Test message", "info")  # 不应该抛出异常

        # 测试涨跌停检查
        limit_info = router.check_limit("000001.XSHE")
        assert "000001.XSHE" in limit_info

    def test_basic_timing_operations(self, router: ConcreteAPIRouter) -> None:
        """测试基本定时操作"""

        def test_func() -> str:
            return "test"

        # 测试每日任务
        job_id = router.run_daily(test_func, "09:30")
        assert "daily_job_test_func" in job_id

        # 测试间隔任务
        job_id = router.run_interval(test_func, 60)
        assert "interval_job_test_func" in job_id

        # 测试回调注册
        assert router.tick_data(test_func) is True
        assert router.on_order_response(test_func) is True
        assert router.on_trade_response(test_func) is True

    def test_mode_support_checking(self, router: ConcreteAPIRouter) -> None:
        """测试模式支持检查"""
        # 支持的API
        assert router.is_mode_supported("get_history") is True
        assert router.is_mode_supported("get_price") is True
        assert router.is_mode_supported("order") is True
        assert router.is_mode_supported("log") is True

        # 不支持的API
        assert router.is_mode_supported("unsupported_api") is False

    def test_context_access(self, router: ConcreteAPIRouter) -> None:
        """测试上下文访问"""
        # 路由器应该能访问上下文
        assert router.context is not None
        assert hasattr(router.context, "portfolio")
        assert hasattr(router.context, "blotter")
        assert hasattr(router.context, "universe")
        assert hasattr(router.context, "benchmark")

    def test_event_bus_access(self, router: ConcreteAPIRouter) -> None:
        """测试事件总线访问"""
        # 路由器应该能访问事件总线
        assert router.event_bus is not None
        assert hasattr(router.event_bus, "publish")
        assert hasattr(router.event_bus, "subscribe")

    def test_logger_functionality(self, router: ConcreteAPIRouter) -> None:
        """测试日志功能"""
        # 路由器应该有日志记录器
        assert router._logger is not None
        assert hasattr(router._logger, "info")
        assert hasattr(router._logger, "warning")
        assert hasattr(router._logger, "error")

    def test_router_inheritance(self) -> None:
        """测试路由器继承"""
        # 具体路由器应该继承自基类
        assert issubclass(ConcreteAPIRouter, BaseAPIRouter)

    def test_method_signatures(self, router: ConcreteAPIRouter) -> None:
        """测试方法签名"""
        import inspect

        # 检查关键方法的签名
        order_sig = inspect.signature(router.order)
        assert "security" in order_sig.parameters
        assert "amount" in order_sig.parameters
        assert "limit_price" in order_sig.parameters

        get_history_sig = inspect.signature(router.get_history)
        assert "count" in get_history_sig.parameters

    def test_error_handling_in_validate_and_execute(
        self, router: ConcreteAPIRouter
    ) -> None:
        """测试validate_and_execute中的错误处理"""

        def error_method() -> None:
            raise ValueError("Validation error")

        # 测试错误被正确传播
        with pytest.raises(ValueError, match="Validation error"):
            router.validate_and_execute("get_history", error_method)

    def test_context_modification_through_router(
        self, router: ConcreteAPIRouter
    ) -> None:
        """测试通过路由器修改上下文"""
        # 测试通过路由器方法修改上下文
        original_universe = router.context.universe.copy()
        new_universe = ["600000.XSHG", "600036.XSHG"]

        router.set_universe(new_universe)
        assert router.context.universe == new_universe
        assert router.context.universe != original_universe

        original_benchmark = router.context.benchmark
        new_benchmark = "000905.SH"

        router.set_benchmark(new_benchmark)
        assert router.context.benchmark == new_benchmark
        assert router.context.benchmark != original_benchmark
