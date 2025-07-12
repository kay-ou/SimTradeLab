# -*- coding: utf-8 -*-
"""
SimTradeLab 启动器

提供简洁的API接口，内部使用完整的插件化架构。
保持用户体验简单，同时利用强大的底层系统。

"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .adapters.ptrade import PTradeAdapter
from .adapters.base import AdapterConfig
from .core.plugin_manager import PluginManager


class BacktestEngine:
    """
    优雅的回测引擎接口

    基于插件化架构，提供简洁易用的API。
    """

    def __init__(
        self,
        strategy_file: Union[str, Path],
        data_path: Optional[Union[str, Path]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001,
        days: Optional[int] = None,
        show_system_logs: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        初始化回测引擎

        Args:
            strategy_file: 策略文件路径
            data_path: 数据文件路径（可选）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            initial_cash: 初始资金
            commission_rate: 佣金费率
            slippage_rate: 滑点率
            days: 运行天数（如果未指定日期范围）
            show_system_logs: 是否显示系统日志
            **kwargs: 其他配置参数
        """
        self.strategy_file = Path(strategy_file)
        self.data_path = Path(data_path) if data_path else None
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.days = days or 10
        self.show_system_logs = show_system_logs

        # PTrade适配器和插件管理器
        self._plugin_manager: Optional[PluginManager] = None
        self._ptrade_adapter: Optional[PTradeAdapter] = None
        self._results: Dict[str, Any] = {}

        # 延迟初始化，只在需要时创建
        self._initialized = False

        # 配置系统日志
        if not self.show_system_logs:
            logging.getLogger("simtradelab").setLevel(logging.CRITICAL)

    def _ensure_initialized(self) -> None:
        """确保系统已初始化"""
        if self._initialized:
            return

        # 初始化插件管理器（自动发现和注册内置插件）
        from .core.event_bus import EventBus
        event_bus = EventBus()
        self._plugin_manager = PluginManager(event_bus)

        # 创建适配器配置
        adapter_config = AdapterConfig(
            config={
                "initial_cash": self.initial_cash,
                "commission_rate": self.commission_rate,
                "slippage_rate": self.slippage_rate,
                "use_mock_data": True,
                "mock_data_enabled": True,
            }
        )

        # 创建适配器实例
        self._ptrade_adapter = PTradeAdapter(adapter_config)
        self._ptrade_adapter.set_event_bus(event_bus)
        self._ptrade_adapter.set_plugin_manager(self._plugin_manager)

        # 初始化适配器（会自动确保数据源可用）
        try:
            self._ptrade_adapter._on_initialize()

            if not self.show_system_logs:
                print("PTrade适配器初始化成功")
        except Exception as e:
            print(f"PTrade适配器初始化失败: {e}")
            import traceback

            traceback.print_exc()
            raise

        self._initialized = True

    def run(self, quiet: bool = False) -> Dict[str, Any]:
        """
        运行回测

        Args:
            quiet: 是否静默运行（不显示进度）

        Returns:
            回测结果字典
        """
        self._ensure_initialized()

        if not self.strategy_file.exists():
            raise FileNotFoundError(f"策略文件不存在: {self.strategy_file}")

        if not quiet:
            print("SimTradeLab 回测引擎")
            print(f"策略: {self.strategy_file.name}")
            print(f"资金: ¥{self.initial_cash:,.0f}")

        # 加载并运行用户策略文件
        try:
            assert self._ptrade_adapter is not None

            # 加载用户策略文件
            if not quiet:
                print("正在加载策略文件...")

            success = self._ptrade_adapter.load_strategy(str(self.strategy_file))
            if not success:
                raise RuntimeError("策略文件加载失败")

            if not quiet:
                print("策略加载成功")

                print(f"开始回测 ({self.days}天)...")

            # 运行策略多天
            for day in range(1, self.days + 1):
                if not quiet and day == 1:
                    # 第一天显示调试信息
                    context = self._ptrade_adapter.get_ptrade_context()

                # 运行策略（适配器会自动生成模拟数据）
                self._ptrade_adapter.run_strategy()

                # 显示进度
                if not quiet and (day % 5 == 0 or day == self.days):
                    portfolio = self._ptrade_adapter.get_portfolio()
                    context = self._ptrade_adapter.get_ptrade_context()
                    if portfolio:
                        print(
                            f"Day {day:2d} | 总值: "
                            f"¥{portfolio.portfolio_value:>10,.0f} | "
                            f"现金: ¥{portfolio.cash:>10,.0f} | "
                            f"仓位: {len(portfolio.positions):>2d}"
                        )
                        if context and context.blotter:
                            print(f"        | 订单数: {len(context.blotter.orders)}")

        except Exception as e:
            import traceback

            if not quiet:
                print(f"策略执行失败: {e}")
                print("详细错误信息:")
                traceback.print_exc()
            raise RuntimeError(f"策略执行失败: {e}")

        # 获取最终结果
        assert self._ptrade_adapter is not None

        # 获取策略执行结果
        portfolio = self._ptrade_adapter.get_portfolio()
        context = self._ptrade_adapter.get_ptrade_context()

        if portfolio is None:
            raise RuntimeError("无法获取投资组合信息")

        # 计算关键指标
        final_value = portfolio.portfolio_value
        total_return = (final_value - self.initial_cash) / self.initial_cash * 100

        results = {
            "initial_cash": self.initial_cash,
            "final_value": final_value,
            "cash": portfolio.cash,
            "positions_value": portfolio.positions_value,
            "total_return_pct": total_return,
            "total_trades": len(context.blotter.orders)
            if context and context.blotter
            else 0,
            "winning_trades": 0,  # 简化实现
            "positions_count": len(portfolio.positions),
            "strategy_file": str(self.strategy_file),
            "days_simulated": self.days,
        }

        if not quiet:
            print("\n回测完成:")
            print(f"   总收益率: {total_return:+.2f}%")
            print(f"   最终价值: ¥{final_value:,.0f}")
            print(f"   仓位数量: {len(portfolio.positions)}")

        self._results = results
        return results

    def get_results(self) -> Dict[str, Any]:
        """获取回测结果"""
        return self._results

    @property
    def portfolio(self) -> Optional[Any]:
        """获取Portfolio对象"""
        if self._ptrade_adapter:
            return self._ptrade_adapter.get_portfolio()
        return None

    def stop(self) -> None:
        """停止引擎并清理资源"""
        if self._ptrade_adapter:
            self._ptrade_adapter._on_shutdown()

    def __enter__(self) -> "BacktestEngine":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口"""
        del exc_type, exc_val, exc_tb  # 避免未使用参数警告
        self.stop()


def run_strategy(
    strategy_file: Union[str, Path],
    initial_cash: float = 1000000.0,
    days: int = 10,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.001,
    show_system_logs: bool = False,
    quiet: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    快速运行策略的函数接口

    Args:
        strategy_file: 策略文件路径
        initial_cash: 初始资金
        days: 运行天数
        commission_rate: 佣金费率
        slippage_rate: 滑点率
        show_system_logs: 是否显示系统日志
        quiet: 是否静默运行
        **kwargs: 其他参数

    Returns:
        回测结果字典
    """
    with BacktestEngine(
        strategy_file=strategy_file,
        initial_cash=initial_cash,
        days=days,
        commission_rate=commission_rate,
        slippage_rate=slippage_rate,
        show_system_logs=show_system_logs,
        **kwargs,
    ) as engine:
        return engine.run(quiet=quiet)
