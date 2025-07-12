# -*- coding: utf-8 -*-
"""
PTrade 兼容层适配器

根据PTrade API文档提供标准的API函数兼容接口，
支持回测、交易、研究三种模式，符合PTrade规范。
"""

import importlib
import importlib.util
import types
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ...core.event_bus import EventBus
from ...plugins.base import BasePlugin, PluginConfig, PluginMetadata
from .context import PTradeContext, PTradeMode
from .lifecycle_controller import PTradeLifecycleError
from .models import Portfolio
from .routers import BacktestAPIRouter, TradingAPIRouter, ResearchAPIRouter

# 数据源优先级定义
DATA_SOURCE_PRIORITIES = {
    "csv_data_plugin": 30,
    "akshare_plugin": 25,
    "tushare_plugin": 20,
    "mock_data_plugin": 10,
}
from .utils import PTradeAdapterError, PTradeAPIError, PTradeCompatibilityError


class PTradeAdapter(BasePlugin):
    """
    PTrade 兼容层适配器

    提供标准的 PTrade API 兼容性，支持研究、回测、交易三种模式。
    采用 v4.0 架构的模式感知适配器设计，通过 API 路由器实现不同模式的功能。
    """

    METADATA = PluginMetadata(
        name="ptrade_adapter",
        version="2.0.0",
        description="PTrade API Compatibility Adapter",
        author="SimTradeLab",
        dependencies=[
            # 移除硬编码的插件依赖，改为通过服务发现机制
        ],  # PTrade适配器不应该硬编码插件依赖
        tags=["ptrade", "compatibility", "adapter", "complete"],
        category="adapter",
        priority=10,  # 高优先级，确保早期加载
    )

    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)

        # PTrade 适配器状态
        self._ptrade_context: Optional[PTradeContext] = None
        self._strategy_module: Optional[types.ModuleType] = None
        self._api_router: Optional[
            Union[BacktestAPIRouter, TradingAPIRouter, ResearchAPIRouter]
        ] = None  # 核心：API路由器
        self._data_cache: Dict[str, Any] = {}
        self._current_data: Dict[str, Dict[str, float]] = {}

        # 插件引用（通过服务发现动态获取）
        self._available_data_plugins: List[Dict[str, Any]] = []  # 所有可用的数据源插件
        self._indicators_plugin = None

        # 设置PTrade支持的模式
        self._set_supported_modes(
            {
                PTradeMode.RESEARCH,
                PTradeMode.BACKTEST,
                PTradeMode.TRADING,
                PTradeMode.MARGIN_TRADING,
            }
        )

        # 默认回测模式
        self._current_mode = PTradeMode.BACKTEST

        # 配置选项 - 支持PTrade兼容的键名
        self._initial_cash = self._config.config.get("initial_cash", 1000000.0)
        # 支持PTrade标准键名和兼容键名
        self._commission_rate = self._config.config.get(
            "commission_rate"
        ) or self._config.config.get("commission", 0.0003)
        self._slippage_rate = self._config.config.get(
            "slippage_rate"
        ) or self._config.config.get("slippage", 0.001)

        # 数据源配置
        self._use_mock_data = self._config.config.get("use_mock_data", False)
        self._mock_data_enabled = self._config.config.get("mock_data_enabled", True)

        # 策略生命周期钩子
        self._strategy_hooks: Dict[str, Optional[Callable[..., Any]]] = {
            "initialize": None,
            "handle_data": None,
            "before_trading_start": None,
            "after_trading_end": None,
            "tick_data": None,
            "on_order_response": None,
            "on_trade_response": None,
        }

        # 事件监听器列表
        self._event_listeners: List[str] = []

        # 事件总线引用 - 将在插件管理器中设置
        self._event_bus_ref: Optional[EventBus] = None

        # 生命周期控制器 - 用于管理策略执行阶段
        self._lifecycle_controller: Optional[Any] = None

    def set_event_bus(self, event_bus: EventBus) -> None:
        """
        Set the event bus reference (called by plugin manager)

        Args:
            event_bus: The event bus instance
        """
        self._event_bus_ref = event_bus

    def _init_api_router(
        self,
    ) -> Union[BacktestAPIRouter, TradingAPIRouter, ResearchAPIRouter]:
        """根据当前模式初始化 API 路由器"""
        current_mode = self.get_current_mode()

        # 确保上下文已初始化
        if self._ptrade_context is None:
            raise PTradeAdapterError(
                "PTrade context must be initialized before API router"
            )

        # 获取当前活跃的数据插件
        active_data_plugin = self._get_active_data_plugin()

        if current_mode == PTradeMode.BACKTEST:
            router = BacktestAPIRouter(
                self._ptrade_context,
                self._event_bus_ref,
                slippage_rate=self._slippage_rate,
                commission_rate=self._commission_rate,
            )
            # 传递活跃数据插件引用给回测模式路由器
            if active_data_plugin:
                router.set_data_plugin(active_data_plugin)
            return router
        elif current_mode == PTradeMode.TRADING:
            live_router = TradingAPIRouter(
                self._ptrade_context, self._event_bus_ref
            )
            # 传递活跃数据插件引用给实盘交易模式路由器
            if active_data_plugin:
                live_router.set_data_plugin(active_data_plugin)
            return live_router
        elif current_mode == PTradeMode.RESEARCH:
            research_router = ResearchAPIRouter(
                self._ptrade_context,
                self._event_bus_ref,
                plugin_manager=self._plugin_manager,
            )
            return research_router
        else:
            raise PTradeAdapterError(f"Unsupported mode: {current_mode}")

    def _on_mode_change(self, new_mode: PTradeMode) -> None:
        """模式切换时重新初始化API路由器"""
        if self._ptrade_context is not None:
            self._api_router = self._init_api_router()
            self._logger.info(f"API router switched to {new_mode.value} mode")

    def _setup_plugin_proxies(self) -> None:
        """设置插件代理机制"""
        # 为技术指标插件创建代理方法
        if self._indicators_plugin:
            # 自动让PTrade adapter获得插件的所有公共方法
            plugin_methods = [
                name
                for name in dir(self._indicators_plugin)
                if not name.startswith("_")
                and callable(getattr(self._indicators_plugin, name))
            ]

            for method_name in plugin_methods:
                if not hasattr(self, method_name):  # 避免覆盖现有方法
                    plugin_method = getattr(self._indicators_plugin, method_name)
                    # 创建代理方法
                    setattr(self, method_name, plugin_method)

            self._logger.debug(
                "Created proxy methods for technical indicators plugin: "
                f"{plugin_methods}"
            )

    def _cleanup_plugin_proxies(self) -> None:
        """清理插件代理方法"""
        # 这里可以添加清理逻辑，但由于我们是直接设置属性，不需要特别清理
        pass

    def _on_initialize(self) -> None:
        """初始化适配器"""
        self._logger.info("Initializing PTrade Adapter")

        # 初始化PTrade上下文
        portfolio = Portfolio(cash=self._initial_cash)
        self._ptrade_context = PTradeContext(
            portfolio=portfolio, capital_base=self._initial_cash
        )

        # 初始化 API 路由器
        self._api_router = self._init_api_router()

        # 获取API路由器的lifecycle controller
        if self._api_router and hasattr(self._api_router, "_lifecycle_controller"):
            self._lifecycle_controller = self._api_router._lifecycle_controller

        # 设置插件代理机制
        self._setup_plugin_proxies()

        # 监听插件系统事件
        if self._event_bus_ref is not None:
            self._setup_event_listeners()

        mode_name = self._current_mode.value if self._current_mode else "unknown"
        self._logger.info(f"PTrade Adapter initialized with {mode_name} mode")

    def set_plugin_manager(self, plugin_manager: Any) -> None:
        """设置插件管理器引用"""
        self._plugin_manager = plugin_manager

        # 使用服务发现机制查找所有数据源插件
        self._discover_data_source_plugins()

        # 查找技术指标插件
        self._discover_indicator_plugins()

    def _discover_data_source_plugins(self) -> None:
        """通过服务发现机制查找所有数据源插件"""
        if not self._plugin_manager:
            self._logger.warning("Plugin manager not available for service discovery")
            return

        # 获取所有已加载的插件
        all_plugins = self._plugin_manager.get_all_plugins()

        # 查找实现了数据源接口的插件
        data_source_plugins = []
        for plugin_name, plugin_instance in all_plugins.items():
            if self._is_data_source_plugin(plugin_instance):
                data_source_plugins.append(
                    {
                        "name": plugin_name,
                        "instance": plugin_instance,
                        "priority": getattr(plugin_instance.metadata, "priority", 100),
                        "category": getattr(
                            plugin_instance.metadata, "category", "unknown"
                        ),
                    }
                )

        # 按优先级排序（优先级高的排前面）
        data_source_plugins.sort(key=lambda x: x["priority"], reverse=True)
        self._available_data_plugins = data_source_plugins

        self._logger.info(
            f"Discovered {len(data_source_plugins)} data source plugins: "
            f"{[p['name'] for p in data_source_plugins]}"
        )

    def _discover_indicator_plugins(self) -> None:
        """发现技术指标插件"""
        if not self._plugin_manager:
            return

        # 查找技术指标插件（可以根据category、名称或特定接口判断）
        all_plugins = self._plugin_manager.get_all_plugins()
        for plugin_name, plugin_instance in all_plugins.items():
            # 检查多种条件来识别技术指标插件
            is_indicators_plugin = (
                # 通过名称识别
                plugin_name == "technical_indicators_plugin"
                # 通过category识别
                or (
                    hasattr(plugin_instance.metadata, "category")
                    and plugin_instance.metadata.category in ["indicators", "analysis"]
                )
                # 通过标签识别
                or (
                    hasattr(plugin_instance.metadata, "tags")
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

            if is_indicators_plugin:
                self._indicators_plugin = plugin_instance
                self._logger.info(f"Found technical indicators plugin: {plugin_name}")
                break

    def _is_data_source_plugin(self, plugin_instance: Any) -> bool:
        """
        判断插件是否为数据源插件

        检查插件是否实现了数据源接口的核心方法
        """
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

    def _get_active_data_plugin(self) -> Optional[Any]:
        """
        获取当前活跃的数据插件

        按优先级自动选择最佳数据源：
        1. 按优先级排序所有可用数据源
        2. 选择优先级最高且可用的数据源
        3. Mock插件作为最后的fallback
        """
        # 如果没有发现任何数据源插件，返回None
        if not self._available_data_plugins:
            self._logger.warning(
                "No data source plugins discovered. Please ensure data plugins are registered."
            )
            return None

        # 按优先级重新排序插件（优先级高的在前）
        sorted_plugins = self._sort_plugins_by_priority(self._available_data_plugins)

        # 尝试使用优先级最高的可用插件
        for plugin_info in sorted_plugins:
            plugin_instance = plugin_info["instance"]
            plugin_name = plugin_info["name"]

            # 检查插件是否可用并尝试启动
            if self._try_activate_plugin(plugin_instance, plugin_name):
                self._logger.debug(
                    f"Using data plugin '{plugin_name}' (priority: {plugin_info.get('priority', 0)})"
                )
                return plugin_instance

        self._logger.warning("No usable data plugin found among discovered plugins")
        return None

    def _sort_plugins_by_priority(
        self, plugins: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """按优先级排序插件"""

        def get_priority(plugin_info: Dict[str, Any]) -> int:
            plugin_name = plugin_info["name"]
            # 从预定义优先级获取，如果没有则使用插件自身的优先级
            return DATA_SOURCE_PRIORITIES.get(
                plugin_name, plugin_info.get("priority", 0) or 0
            )

        return sorted(plugins, key=get_priority, reverse=True)

    def _try_activate_plugin(self, plugin_instance: Any, plugin_name: str) -> bool:
        """尝试激活插件"""
        try:
            # 检查插件状态
            if hasattr(plugin_instance, "state"):
                state = plugin_instance.state.value
                if state == "started":
                    return True
                elif state == "initialized":
                    # 尝试启动插件
                    plugin_instance.start()
                    self._logger.debug(f"Started data plugin '{plugin_name}'")
                    return True

            # 对于Mock插件，检查是否启用
            if (
                hasattr(plugin_instance, "metadata")
                and plugin_instance.metadata.name == "mock_data_plugin"
            ):
                if (
                    hasattr(plugin_instance, "is_enabled")
                    and plugin_instance.is_enabled()
                ):
                    return True
                elif hasattr(plugin_instance, "enable"):
                    plugin_instance.enable()
                    self._logger.debug("Enabled mock data plugin")
                    return True

            return False

        except Exception as e:
            self._logger.warning(f"Failed to activate data plugin '{plugin_name}': {e}")
            return False

    def switch_data_source(self, plugin_name: str) -> bool:
        """
        切换数据源插件

        Args:
            plugin_name: 目标插件名称

        Returns:
            是否成功切换
        """
        # 查找目标插件
        target_plugin = None
        for plugin_info in self._available_data_plugins:
            if plugin_info["name"] == plugin_name:
                target_plugin = plugin_info["instance"]
                break

        if not target_plugin:
            self._logger.error(
                f"Data plugin '{plugin_name}' not found in discovered plugins"
            )
            return False

        try:
            # 如果是Mock插件，使用Mock模式
            if (
                hasattr(target_plugin, "metadata")
                and target_plugin.metadata.name == "mock_data_plugin"
            ):
                if hasattr(target_plugin, "enable"):
                    target_plugin.enable()
                self._use_mock_data = True
                self._mock_data_enabled = True
            else:
                # 对于其他插件，确保Mock模式关闭
                self._use_mock_data = False
                # 启动目标插件（如果需要）
                if (
                    hasattr(target_plugin, "state")
                    and target_plugin.state.value != "started"
                ):
                    target_plugin.start()

            # 重新初始化API路由器以使用新的数据源
            if self._ptrade_context:
                self._api_router = self._init_api_router()

            self._logger.info(f"Successfully switched to data plugin: {plugin_name}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to switch to data plugin '{plugin_name}': {e}")
            return False

    def get_data_source_status(self) -> Dict[str, Any]:
        """
        获取数据源状态信息

        Returns:
            数据源状态字典
        """
        active_plugin = self._get_active_data_plugin()

        # 收集所有发现的数据源插件信息
        discovered_plugins = []
        mock_plugin_available = False
        mock_plugin_enabled = False

        for plugin_info in self._available_data_plugins:
            plugin_instance = plugin_info["instance"]
            plugin_name = plugin_info["name"]

            plugin_status = {
                "name": plugin_name,
                "category": plugin_info["category"],
                "priority": plugin_info["priority"],
                "state": plugin_instance.state.value
                if hasattr(plugin_instance, "state")
                else "unknown",
            }

            # 检查是否为Mock插件
            if (
                hasattr(plugin_instance, "metadata")
                and plugin_instance.metadata.name == "mock_data_plugin"
            ):
                mock_plugin_available = True
                if hasattr(plugin_instance, "is_enabled"):
                    mock_plugin_enabled = plugin_instance.is_enabled()
                plugin_status["is_mock_plugin"] = True
                plugin_status["enabled"] = mock_plugin_enabled
            else:
                plugin_status["is_mock_plugin"] = False

            discovered_plugins.append(plugin_status)

        return {
            "active_data_source": active_plugin.__class__.__name__
            if active_plugin
            else "None",
            "active_plugin_name": (
                active_plugin.metadata.name
                if active_plugin and hasattr(active_plugin, "metadata")
                else "Unknown"
            ),
            "discovered_plugins_count": len(self._available_data_plugins),
            "discovered_plugins": discovered_plugins,
            "mock_plugin_available": mock_plugin_available,
            "mock_plugin_enabled": mock_plugin_enabled,
            "use_mock_data_config": self._use_mock_data,
            "mock_data_enabled_config": self._mock_data_enabled,
        }

    def list_available_data_plugins(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的数据源插件

        Returns:
            可用数据源插件列表
        """
        return [
            {
                "name": plugin_info["name"],
                "category": plugin_info["category"],
                "priority": plugin_info["priority"],
                "state": plugin_info["instance"].state.value
                if hasattr(plugin_info["instance"], "state")
                else "unknown",
                "metadata": {
                    "version": plugin_info["instance"].metadata.version
                    if hasattr(plugin_info["instance"], "metadata")
                    else "unknown",
                    "description": plugin_info["instance"].metadata.description
                    if hasattr(plugin_info["instance"], "metadata")
                    else "No description",
                    "author": plugin_info["instance"].metadata.author
                    if hasattr(plugin_info["instance"], "metadata")
                    else "Unknown",
                },
            }
            for plugin_info in self._available_data_plugins
        ]

    def _on_start(self) -> None:
        """启动适配器"""
        self._logger.info("Starting PTrade Adapter")

        # 发布适配器启动事件
        if self._event_bus_ref is not None:
            self._event_bus_ref.publish(
                "ptrade.adapter.started",
                data={"adapter": self, "context": self._ptrade_context},
                source="ptrade_adapter",
            )

    def _on_stop(self) -> None:
        """停止适配器"""
        self._logger.info("Stopping PTrade Adapter")

        # 清理资源
        self._cleanup_strategy()

        # 清理插件代理
        self._cleanup_plugin_proxies()

        # 清理事件监听器
        self._cleanup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        # 监听插件系统事件
        pass

    def _cleanup_event_listeners(self) -> None:
        """清理事件监听器"""
        if self._event_bus_ref is not None:
            for listener_id in self._event_listeners:
                self._event_bus_ref.unsubscribe(listener_id)
        self._event_listeners.clear()

    def _cleanup_strategy(self) -> None:
        """清理策略资源"""
        if self._strategy_module:
            # 清理策略模块引用
            self._strategy_module = None

        # 重置策略钩子
        for hook_name in self._strategy_hooks:
            self._strategy_hooks[hook_name] = None

        # 清理缓存
        self._data_cache.clear()
        self._current_data.clear()

    # =========================================
    # 策略执行和生命周期管理
    # =========================================

    def run_strategy(self, data: Optional[Dict[str, Any]] = None) -> None:
        """
        运行策略主循环

        Args:
            data: 市场数据，如果为None则使用模拟数据
        """
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")

        if not self._strategy_module:
            raise PTradeAPIError("No strategy loaded")

        # 更新当前时间
        self._ptrade_context.current_dt = datetime.now()

        # 如果没有提供数据，生成模拟数据
        if data is None:
            data = self._generate_market_data()

        # 执行盘前处理
        if self._strategy_hooks["before_trading_start"]:
            try:
                # 设置生命周期阶段
                if (
                    hasattr(self, "_lifecycle_controller")
                    and self._lifecycle_controller
                ):
                    from .lifecycle_controller import LifecyclePhase

                    self._lifecycle_controller.set_phase(
                        LifecyclePhase.BEFORE_TRADING_START
                    )
                    self._strategy_hooks["before_trading_start"](
                        self._ptrade_context, data
                    )
            except Exception as e:
                self._logger.error(f"Error in before_trading_start: {e}")

        # 执行主策略逻辑
        if self._strategy_hooks["handle_data"]:
            try:
                # 设置生命周期阶段
                if (
                    hasattr(self, "_lifecycle_controller")
                    and self._lifecycle_controller
                ):
                    from .lifecycle_controller import LifecyclePhase

                    self._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
                    self._strategy_hooks["handle_data"](self._ptrade_context, data)
            except Exception as e:
                self._logger.error(f"Error in handle_data: {e}")

        # 执行盘后处理
        if self._strategy_hooks["after_trading_end"]:
            try:
                # 设置生命周期阶段
                if (
                    hasattr(self, "_lifecycle_controller")
                    and self._lifecycle_controller
                ):
                    from .lifecycle_controller import LifecyclePhase

                    self._lifecycle_controller.set_phase(
                        LifecyclePhase.AFTER_TRADING_END
                    )
                    self._strategy_hooks["after_trading_end"](
                        self._ptrade_context, data
                    )
            except Exception as e:
                self._logger.error(f"Error in after_trading_end: {e}")

        # 更新投资组合价值
        self._ptrade_context.portfolio.update_portfolio_value()

        # 发布策略运行事件
        if self._event_bus_ref is not None:
            self._event_bus_ref.publish(
                "ptrade.strategy.run",
                data={
                    "portfolio_value": self._ptrade_context.portfolio.portfolio_value,
                    "cash": self._ptrade_context.portfolio.cash,
                    "returns": self._ptrade_context.portfolio.returns,
                    "positions_count": len(self._ptrade_context.portfolio.positions),
                },
                source="ptrade_adapter",
            )

    def _generate_market_data(self) -> Dict[str, Any]:
        """生成模拟市场数据"""
        if self._ptrade_context is None or not self._ptrade_context.universe:
            return {}

        # 优先使用API路由器的数据获取方法
        if self._api_router and hasattr(self._api_router, "get_current_data"):
            try:
                current_data = self._api_router.get_current_data(
                    list(self._ptrade_context.universe)
                )
                # 更新当前数据缓存
                self._current_data.update(current_data)
                return current_data
            except Exception as e:
                self._logger.warning(f"API router data generation failed: {e}")

        # 回退到直接使用数据插件
        active_data_plugin = self._get_active_data_plugin()
        if not active_data_plugin:
            raise RuntimeError("No data plugin available for market data generation")

        try:
            # 使用PTrade标准API：get_snapshot
            snapshot: Dict[str, Any] = active_data_plugin.get_snapshot(
                self._ptrade_context.universe
            )
            # 更新当前数据缓存
            self._current_data.update(snapshot)
            return snapshot
        except Exception as e:
            # 数据插件失败时抛出异常，不使用fallback
            raise RuntimeError(f"Failed to generate market data: {e}")

    def _get_current_price(self, security: str) -> float:
        """获取股票当前价格"""
        # 先从缓存查找
        if security in self._current_data:
            return self._current_data[security].get("last_price", 10.0)

        # 使用活跃数据插件获取
        active_data_plugin = self._get_active_data_plugin()
        if not active_data_plugin:
            raise RuntimeError(
                f"No data plugin available for current price of {security}"
            )

        try:
            price: Optional[float] = active_data_plugin.get_current_price(security)
            if price is not None:
                return float(price)
            else:
                raise ValueError(f"No price data available for {security}")
        except Exception as e:
            # 数据插件失败时抛出异常，不使用fallback
            raise RuntimeError(f"Failed to get current price for {security}: {e}")

    def get_strategy_performance(self) -> Dict[str, Any]:
        """获取策略性能统计"""
        if self._ptrade_context is None:
            return {}

        portfolio = self._ptrade_context.portfolio

        # 计算基本性能指标
        return {
            "portfolio_value": portfolio.portfolio_value,
            "cash": portfolio.cash,
            "positions_value": portfolio.positions_value,
            "returns": portfolio.returns,
            "pnl": portfolio.pnl,
            "positions_count": len(portfolio.positions),
            "total_trades": len(self._ptrade_context.blotter.orders)
            if self._ptrade_context.blotter
            else 0,
            "winning_trades": len(
                [
                    o
                    for o in self._ptrade_context.blotter.orders.values()
                    if o.status == "filled" and o.filled > 0
                ]
            )
            if self._ptrade_context.blotter
            else 0,
            "starting_cash": portfolio._starting_cash,
            "current_datetime": self._ptrade_context.current_dt,
        }

    def execute_strategy_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        执行策略钩子函数

        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            钩子函数返回值
        """
        if hook_name not in self._strategy_hooks:
            raise PTradeAPIError(f"Unknown strategy hook: {hook_name}")

        hook_func = self._strategy_hooks[hook_name]
        if not hook_func:
            self._logger.warning(f"Strategy hook {hook_name} is not implemented")
            return None

        try:
            # 使用API使用限制上下文执行钩子函数
            # 设置生命周期阶段
            if hasattr(self, "_lifecycle_controller"):
                self._lifecycle_controller.set_phase(hook_name)
                return hook_func(*args, **kwargs)
        except Exception as e:
            self._logger.error(f"Error executing strategy hook {hook_name}: {e}")
            raise PTradeAPIError(f"Strategy hook {hook_name} failed: {e}")

    # =========================================
    # 策略加载和管理
    # =========================================

    def load_strategy(self, strategy_file: Union[str, Path]) -> bool:
        """
        加载PTrade策略文件

        Args:
            strategy_file: 策略文件路径

        Returns:
            是否成功加载
        """
        try:
            strategy_path = Path(strategy_file)
            if not strategy_path.exists():
                raise PTradeCompatibilityError(
                    f"Strategy file not found: {strategy_path}"
                )

            self._logger.info(f"Loading PTrade strategy: {strategy_path}")

            # 重置生命周期控制器状态以避免旧状态干扰
            if (
                hasattr(self, "_lifecycle_controller")
                and self._lifecycle_controller
            ):
                self._lifecycle_controller.reset()
                self._logger.debug("Reset lifecycle controller before loading strategy")

            # 加载策略模块
            spec = importlib.util.spec_from_file_location("strategy", strategy_path)
            if spec is None or spec.loader is None:
                raise PTradeCompatibilityError(
                    f"Failed to load strategy spec: {strategy_path}"
                )

            strategy_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(strategy_module)

            # 注入PTrade API和全局对象
            self._inject_ptrade_apis(strategy_module)

            # 提取策略钩子函数
            self._logger.info("Extracting strategy hooks...")
            self._extract_strategy_hooks(strategy_module)
            self._logger.info(f"Extracted hooks: {list(self._strategy_hooks.keys())}")
            self._logger.info(
                f"Available hooks: {[name for name, func in self._strategy_hooks.items() if func is not None]}"
            )

            # 保存策略模块引用
            self._strategy_module = strategy_module

            # 执行策略初始化
            if self._strategy_hooks["initialize"]:
                # 设置生命周期阶段
                if (
                    hasattr(self, "_lifecycle_controller")
                    and self._lifecycle_controller
                ):
                    from .lifecycle_controller import LifecyclePhase

                    self._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
                    self._logger.info("Executing strategy initialize function...")
                    try:
                        self._strategy_hooks["initialize"](self._ptrade_context)
                        self._logger.info(
                            "Strategy initialize function completed successfully"
                        )

                        if self._ptrade_context:
                            self._ptrade_context.initialized = True

                            # 调试：显示初始化后的状态
                            self._logger.info(
                                f"After initialize - securities: {getattr(self._ptrade_context, 'securities', 'Not found')}"
                            )
                            self._logger.info(
                                f"After initialize - universe: {self._ptrade_context.universe}"
                            )

                            # 同步策略中设置的securities到universe
                            if (
                                hasattr(self._ptrade_context, "securities")
                                and self._ptrade_context.securities
                            ):
                                self._ptrade_context.set_universe(
                                    self._ptrade_context.securities
                                )
                                self._logger.info(
                                    f"Synced securities to universe: {self._ptrade_context.securities}"
                                )
                            else:
                                self._logger.warning(
                                    "No securities found in context after initialize"
                                )
                    except Exception as e:
                        self._logger.error(f"Error in strategy initialize: {e}")
                        import traceback

                        self._logger.error(
                            f"Initialize traceback: {traceback.format_exc()}"
                        )
                        raise

            self._logger.info(f"PTrade strategy loaded successfully: {strategy_path}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to load PTrade strategy: {e}")
            raise PTradeCompatibilityError(f"Strategy loading failed: {e}")

    def _inject_ptrade_apis(self, strategy_module: types.ModuleType) -> None:
        """向策略模块注入PTrade API"""

        # 注入全局对象 - 直接设置为context.g的引用
        if self._ptrade_context is not None:
            setattr(strategy_module, "g", self._ptrade_context.g)
        else:
            # 如果上下文不存在，创建一个空的全局对象
            setattr(strategy_module, "g", types.SimpleNamespace())

        # 获取策略钩子函数名称列表
        strategy_hook_names = set(self._strategy_hooks.keys())

        # 通过API路由器注入API方法
        if self._api_router is not None:
            # 获取路由器支持的所有API方法
            api_methods = [
                method_name
                for method_name in dir(self._api_router)
                if not method_name.startswith("_")
                and callable(getattr(self._api_router, method_name))
            ]

            injected_count = 0
            for api_name in api_methods:
                # 如果是策略钩子函数，跳过注入
                if api_name in strategy_hook_names:
                    continue

                # 跳过路由器内部方法
                if api_name in [
                    "validate_and_execute",
                    "is_mode_supported",
                    "handle_data",
                ]:
                    continue

                # 特殊处理log属性
                if api_name == "log":
                    # 直接注入log对象，不进行包装
                    log_obj = getattr(self._api_router, api_name)
                    setattr(strategy_module, api_name, log_obj)
                    injected_count += 1
                    continue

                api_func = getattr(self._api_router, api_name)
                if api_func:
                    # 创建API包装器，自动注入适配器引用
                    wrapped_func = self._create_api_wrapper(api_func, api_name)
                    setattr(strategy_module, api_name, wrapped_func)
                    injected_count += 1

            self._logger.debug(
                f"Injected {injected_count} PTrade APIs via "
                f"{self._api_router.__class__.__name__}"
            )
        else:
            self._logger.warning("No API router available for API injection")

    def _create_api_wrapper(
        self, api_func: Callable[..., Any], api_name: str
    ) -> Callable[..., Any]:
        """创建API包装器函数"""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 检查API使用限制
                # 检查API调用权限
                if hasattr(self, "_lifecycle_controller"):
                    self._lifecycle_controller.validate_api_call(api_name)

                # 自动注入适配器引用作为第一个参数
                return api_func(*args, **kwargs)
            except PTradeLifecycleError as e:
                self._logger.error(f"PTrade API '{api_name}' access denied: {e}")
                raise PTradeAPIError(f"API access denied: {api_name}: {e}")
            except Exception as e:
                self._logger.error(f"PTrade API '{api_name}' failed: {e}")
                raise PTradeAPIError(f"API call failed: {api_name}: {e}")

        # 保留原函数的文档
        wrapper.__name__ = api_name
        wrapper.__doc__ = api_func.__doc__
        return wrapper

    def _extract_strategy_hooks(self, strategy_module: types.ModuleType) -> None:
        """提取策略钩子函数"""
        for hook_name in self._strategy_hooks:
            if hasattr(strategy_module, hook_name):
                hook_func = getattr(strategy_module, hook_name)
                if callable(hook_func):
                    self._strategy_hooks[hook_name] = hook_func
                    self._logger.debug(f"Found strategy hook: {hook_name}")

    # =========================================
    # 公共接口
    # =========================================

    def get_ptrade_context(self) -> Optional[PTradeContext]:
        """获取PTrade上下文"""
        return self._ptrade_context

    def get_portfolio(self) -> Optional[Portfolio]:
        """获取投资组合"""
        return self._ptrade_context.portfolio if self._ptrade_context else None

    def get_api_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        current_mode = self.get_current_mode()

        # 通过API路由器获取统计信息
        if self._api_router is not None:
            # 获取路由器支持的所有API方法
            api_methods = [
                method_name
                for method_name in dir(self._api_router)
                if not method_name.startswith("_")
                and callable(getattr(self._api_router, method_name))
                and method_name
                not in ["validate_and_execute", "is_mode_supported", "handle_data"]
            ]

            # 按类别统计API数量（简化版）
            trading_apis = [
                api
                for api in api_methods
                if api.startswith(("order", "cancel", "get_position", "get_trades"))
            ]
            data_apis = [
                api
                for api in api_methods
                if api.startswith(("get_history", "get_price", "get_snapshot"))
            ]
            calc_apis = [
                api
                for api in api_methods
                if api.startswith(("get_MACD", "get_KDJ", "get_RSI", "get_CCI"))
            ]
            util_apis = [api for api in api_methods if api in ["log", "check_limit"]]
            setting_apis = [api for api in api_methods if api.startswith("set_")]

            return {
                "total_apis": len(api_methods),
                "trading_apis": len(trading_apis),
                "market_data_apis": len(data_apis),
                "calculations_apis": len(calc_apis),
                "utils_apis": len(util_apis),
                "settings_apis": len(setting_apis),
                "current_mode": current_mode.value if current_mode else None,
                "api_router_type": self._api_router.__class__.__name__,
                "strategy_loaded": self._strategy_module is not None,
                "portfolio_value": self._ptrade_context.portfolio.portfolio_value
                if self._ptrade_context
                else 0,
                "data_source_status": self.get_data_source_status(),
            }
        else:
            return {
                "total_apis": 0,
                "trading_apis": 0,
                "market_data_apis": 0,
                "calculations_apis": 0,
                "utils_apis": 0,
                "settings_apis": 0,
                "current_mode": current_mode.value if current_mode else None,
                "api_router_type": "None",
                "strategy_loaded": self._strategy_module is not None,
                "portfolio_value": self._ptrade_context.portfolio.portfolio_value
                if self._ptrade_context
                else 0,
                "data_source_status": self.get_data_source_status(),
            }

    def __enter__(self) -> "PTradeAdapter":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """上下文管理器出口"""
        self.shutdown()
