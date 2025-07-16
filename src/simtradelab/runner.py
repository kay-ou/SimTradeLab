# -*- coding: utf-8 -*-
"""
回测运行器

负责加载策略、数据和回测引擎，并执行整个回测流程。

更新为使用统一插件管理的BacktestEngine
"""

import logging
from typing import Any, Dict, Optional

from .backtest.engine import BacktestEngine
from .core.plugin_manager import PluginManager


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
        self.plugin_manager = plugin_manager or PluginManager()

        # 确保回测插件已注册
        self._ensure_backtest_plugins_registered()

        # 从配置中注册额外插件
        if "plugins" in self.config:
            self.plugin_manager.register_plugins_from_config(self.config["plugins"])

        # 实例化使用统一插件管理的回测引擎
        backtest_config = self.config.get("backtest", {})
        self.engine = BacktestEngine(
            plugin_manager=self.plugin_manager,
            config=backtest_config,
        )

        self.logger.info("BacktestRunner initialized with unified plugin management.")

    def _ensure_backtest_plugins_registered(self) -> None:
        """
        确保回测插件已注册到PluginManager

        注册默认的回测插件，如果尚未注册的话
        """
        from .backtest.plugins.commission_models import FixedCommissionModel
        from .backtest.plugins.matching_engines import SimpleMatchingEngine
        from .backtest.plugins.slippage_models import FixedSlippageModel

        # 注册默认回测插件（如果尚未注册）
        plugins_to_register = [
            SimpleMatchingEngine,
            FixedSlippageModel,
            FixedCommissionModel,
        ]

        for plugin_class in plugins_to_register:
            try:
                plugin_name = plugin_class.METADATA.name
                if plugin_name not in self.plugin_manager.get_all_plugins():
                    self.plugin_manager.register_plugin(plugin_class)
                    self.logger.debug(f"Registered backtest plugin: {plugin_name}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to register plugin {plugin_class.__name__}: {e}"
                )

    def run(self):
        """运行回测"""
        self.logger.info(f"Starting backtest for strategy: {self.strategy_file}")

        # 此处应有加载数据和策略的逻辑
        # ...

        with self.engine as _:
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
