# -*- coding: utf-8 -*-
"""
回测运行器

负责加载策略、数据和回测引擎，并执行整个回测流程。

更新为使用统一插件管理的BacktestEngine
"""

import importlib
import logging
from typing import Any, Dict, Optional

from .backtest.engine import BacktestEngine
from .core.plugin_manager import PluginManager, PluginRegistrationError


class BacktestRunner:
    """
    回测运行器

    使用统一插件管理的BacktestEngine
    负责协调整个回测过程，包括：
    1. 初始化PluginManager并注册回测插件
    2. 实例化使用统一插件管理的BacktestEngine
    3. 加载策略和数据
    4. 运行回测并生成结果
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
        self._plugin_manager = plugin_manager or PluginManager()

        # 确保所有内置的回测插件都已显式注册
        self._ensure_backtest_plugins_registered()

        # 从配置中注册额外插件
        if "plugins" in self.config:
            self._plugin_manager.register_plugins_from_config(self.config["plugins"])

        # 实例化使用统一插件管理的回测引擎
        backtest_config = self.config.get("backtest", {})
        self._engine = BacktestEngine(
            plugin_manager=self._plugin_manager,
            config=backtest_config,
        )

        self.logger.info("BacktestRunner initialized with unified plugin management.")

    def _ensure_backtest_plugins_registered(self) -> None:
        """
        显式导入并注册所有内置的回测插件。
        这是最可靠的方法，避免了动态发现的复杂性和不确定性。
        """
        try:
            from simtradelab.backtest.plugins.commission_models import (
                FixedCommissionModel,
            )
            from simtradelab.backtest.plugins.latency_models.default_latency_model import (
                DefaultLatencyModel,
            )
            from simtradelab.backtest.plugins.matching_engines import (
                DepthMatchingEngine,
            )
            from simtradelab.backtest.plugins.slippage_models import FixedSlippageModel

            plugins_to_register = [
                DepthMatchingEngine,
                FixedSlippageModel,
                FixedCommissionModel,
                DefaultLatencyModel,
            ]

            for plugin_class in plugins_to_register:
                try:
                    # 使用插件元数据中的名称进行注册
                    plugin_name = plugin_class.METADATA.name
                    # 检查插件是否已注册
                    if self._plugin_manager.get_plugin_info(plugin_name) is None:
                        self._plugin_manager.register_plugin(plugin_class)
                        self.logger.info(
                            f"Explicitly registered backtest plugin: {plugin_name}"
                        )
                except PluginRegistrationError as e:
                    self.logger.warning(
                        f"Could not register {plugin_class.__name__}: {e}"
                    )
        except ImportError as e:
            self.logger.error(
                f"Failed to import backtest plugins for registration: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during plugin registration: {e}"
            )

    def run(self):
        """运行回测"""
        self.logger.info(f"Starting backtest for strategy: {self.strategy_file}")

        # 此处应有加载数据和策略的逻辑
        # ...

        with self._engine as _:
            # 模拟数据流和订单提交
            # for market_data_event in data_stream:
            #     engine.update_market_data(market_data_event.symbol, market_data_event)
            #     strategy.handle_data(...) -> engine.submit_order(...)
            pass

        stats = self._engine.get_statistics()
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
