# -*- coding: utf-8 -*-
"""
回测运行器

负责加载策略、数据和回测引擎，并执行整个回测流程。
"""

import logging
from typing import Any, Dict, Optional, Type, cast, TypeVar

from .core.plugin_manager import PluginManager
from .backtest.engine import BacktestEngine
from .backtest.plugins.base import (
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    BaseBacktestPlugin,
)
# ... 其他导入 ...

T = TypeVar("T", bound=BaseBacktestPlugin)

class BacktestRunner:
    """
    回测运行器

    负责协调整个回测过程，包括：
    1. 加载和配置回测插件（撮合、滑点、手续费）。
    2. 实例化重构后的 BacktestEngine。
    3. 加载策略和数据。
    4. 运行回测并生成结果。
    """

    def __init__(
        self,
        strategy_file: str,
        config: Dict[str, Any],
        plugin_manager: Optional[PluginManager] = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.strategy_file = strategy_file
        self.config = config
        self.plugin_manager = plugin_manager or PluginManager()

        # 从配置中注册插件
        if "plugins" in self.config:
            self.plugin_manager.register_plugins_from_config(self.config["plugins"])

        # 加载回测插件
        matching_engine_plugin = self._load_backtest_plugin(
            "matching_engine", "simple_matching_engine", BaseMatchingEngine
        )
        slippage_model_plugin = self._load_backtest_plugin(
            "slippage_model", "fixed_slippage_model", BaseSlippageModel
        )
        commission_model_plugin = self._load_backtest_plugin(
            "commission_model", "fixed_commission_model", BaseCommissionModel
        )

        # 实例化重构后的回测引擎，并注入插件
        self.engine = BacktestEngine(
            matching_engine=matching_engine_plugin,
            slippage_model=slippage_model_plugin,
            commission_model=commission_model_plugin,
        )

        self.logger.info("BacktestRunner initialized.")

    def _load_backtest_plugin(
        self, plugin_type: str, default_plugin: str, expected_type: Type[T]
    ) -> T:
        """使用 PluginManager 加载并验证回测插件类型"""
        plugin_name = self.config.get("backtest", {}).get(plugin_type, default_plugin)
        try:
            plugin_instance = self.plugin_manager.load_plugin(plugin_name)
            if not isinstance(plugin_instance, expected_type):
                raise TypeError(
                    f"Plugin {plugin_name} is not of expected type {expected_type.__name__}"
                )
            self.logger.info(f"Successfully loaded {plugin_type}: {plugin_name}")
            return cast(T, plugin_instance)
        except Exception as e:
            self.logger.error(f"Failed to load {plugin_type} '{plugin_name}': {e}")
            raise

    def run(self):
        """运行回测"""
        self.logger.info(f"Starting backtest for strategy: {self.strategy_file}")
        
        # 此处应有加载数据和策略的逻辑
        # ...
        
        with self.engine as engine:
            # 模拟数据流和订单提交
            # for market_data_event in data_stream:
            #     engine.update_market_data(market_data_event.symbol, market_data_event)
            #     strategy.handle_data(...) -> engine.submit_order(...)
            pass

        stats = self.engine.get_statistics()
        self.logger.info(f"Backtest finished. Stats: {stats}")
        return stats

    def __enter__(self) -> "BacktestRunner":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def run_backtest(strategy_file: str, config: Dict[str, Any]):
    """
    运行回测的便捷函数

    Args:
        strategy_file: 策略文件路径
        config: 配置字典
    """
    with BacktestRunner(strategy_file=strategy_file, config=config) as runner:
        return runner.run()
