# -*- coding: utf-8 -*-
"""
runner.py 测试文件

测试SimTradeLab的用户友好启动器接口
"""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.simtradelab.runner import BacktestEngine, run_strategy


@pytest.mark.unit
class TestBacktestEngine:
    """BacktestEngine单元测试"""

    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file)

            assert engine.strategy_file == Path(strategy_file)
            assert engine.initial_cash == 1000000.0
            assert engine.commission_rate == 0.0003
            assert engine.slippage_rate == 0.001
            assert engine.days == 10
            assert not engine.show_system_logs
            assert not engine._initialized

        finally:
            Path(strategy_file).unlink()

    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(
                strategy_file,
                initial_cash=500000.0,
                commission_rate=0.0005,
                slippage_rate=0.002,
                days=20,
                show_system_logs=True,
            )

            assert engine.initial_cash == 500000.0
            assert engine.commission_rate == 0.0005
            assert engine.slippage_rate == 0.002
            assert engine.days == 20
            assert engine.show_system_logs

        finally:
            Path(strategy_file).unlink()

    @patch("src.simtradelab.runner.PluginManager")
    @patch("src.simtradelab.runner.PTradeAdapter")
    def test_ensure_initialized(
        self, mock_ptrade_adapter_class, mock_plugin_manager_class
    ):
        """测试延迟初始化"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            mock_plugin_manager = MagicMock()
            mock_plugin_manager_class.return_value = mock_plugin_manager

            mock_ptrade_adapter = MagicMock()
            mock_ptrade_adapter_class.return_value = mock_ptrade_adapter

            engine = BacktestEngine(strategy_file, initial_cash=100000)

            # 初始状态未初始化
            assert not engine._initialized

            # 调用_ensure_initialized
            engine._ensure_initialized()

            # 验证初始化
            assert engine._initialized
            mock_plugin_manager_class.assert_called_once()
            mock_ptrade_adapter_class.assert_called_once()
            assert engine._plugin_manager == mock_plugin_manager
            assert engine._ptrade_adapter == mock_ptrade_adapter

            # 再次调用不应该重复初始化
            mock_plugin_manager_class.reset_mock()
            mock_ptrade_adapter_class.reset_mock()
            engine._ensure_initialized()
            mock_plugin_manager_class.assert_not_called()
            mock_ptrade_adapter_class.assert_not_called()

        finally:
            Path(strategy_file).unlink()

    def test_context_manager(self):
        """测试上下文管理器"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            with BacktestEngine(strategy_file) as engine:
                assert isinstance(engine, BacktestEngine)
                engine._ptrade_adapter = MagicMock()

            # 验证stop被调用
            engine._ptrade_adapter._on_shutdown.assert_called_once()

        finally:
            Path(strategy_file).unlink()

    def test_portfolio_property_no_engine(self):
        """测试在没有策略引擎时的portfolio属性"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file)
            assert engine.portfolio is None

        finally:
            Path(strategy_file).unlink()

    def test_portfolio_property_with_engine(self):
        """测试有策略引擎时的portfolio属性"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file)
            mock_ptrade_adapter = MagicMock()
            mock_portfolio = MagicMock()
            mock_ptrade_adapter.get_portfolio.return_value = mock_portfolio
            engine._ptrade_adapter = mock_ptrade_adapter

            assert engine.portfolio == mock_portfolio

        finally:
            Path(strategy_file).unlink()

    def test_stop_with_engine(self):
        """测试stop方法"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file)
            mock_ptrade_adapter = MagicMock()
            engine._ptrade_adapter = mock_ptrade_adapter

            engine.stop()
            mock_ptrade_adapter._on_shutdown.assert_called_once()

        finally:
            Path(strategy_file).unlink()

    def test_stop_without_engine(self):
        """测试没有引擎时的stop方法"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file)
            # 不应该报错
            engine.stop()

        finally:
            Path(strategy_file).unlink()


@pytest.mark.integration
class TestBacktestEngineIntegration:
    """BacktestEngine集成测试"""

    def test_run_simple_strategy(self):
        """测试运行简单策略"""
        # 创建简单策略文件
        strategy_content = """
def initialize(context):
    context.set_universe(['000001.XSHE'])

def handle_data(context, data):
    if context.portfolio.cash > 1000:
        context.order('000001.XSHE', 100)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name

        try:
            with BacktestEngine(strategy_file, initial_cash=10000, days=3) as engine:
                results = engine.run(quiet=True)

                # 验证结果结构
                assert isinstance(results, dict)
                assert "initial_cash" in results
                assert "final_value" in results
                assert "total_return_pct" in results
                assert "strategy_file" in results
                assert "days_simulated" in results

                # 验证基本值
                assert results["initial_cash"] == 10000
                assert results["days_simulated"] == 3
                assert results["strategy_file"] == strategy_file

        finally:
            Path(strategy_file).unlink()

    def test_run_strategy_file_not_found(self):
        """测试策略文件不存在的情况"""
        non_existent_file = "/tmp/non_existent_strategy.py"

        with BacktestEngine(non_existent_file) as engine:
            with pytest.raises(FileNotFoundError, match="策略文件不存在"):
                engine.run()


@pytest.mark.unit
class TestRunStrategyFunction:
    """run_strategy函数测试"""

    def test_run_strategy_function(self):
        """测试run_strategy便捷函数"""
        strategy_content = """
def initialize(context):
    context.set_universe(['000001.XSHE'])

def handle_data(context, data):
    pass
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name

        try:
            results = run_strategy(
                strategy_file=strategy_file, initial_cash=5000, days=2, quiet=True
            )

            assert isinstance(results, dict)
            assert results["initial_cash"] == 5000
            assert results["days_simulated"] == 2

        finally:
            Path(strategy_file).unlink()

    def test_run_strategy_with_custom_params(self):
        """测试带自定义参数的run_strategy"""
        strategy_content = """
def initialize(context):
    context.set_universe(['000001.XSHE'])
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name

        try:
            results = run_strategy(
                strategy_file=strategy_file,
                initial_cash=20000,
                days=5,
                commission_rate=0.001,
                slippage_rate=0.002,
                show_system_logs=False,
                quiet=True,
            )

            assert results["initial_cash"] == 20000
            assert results["days_simulated"] == 5

        finally:
            Path(strategy_file).unlink()


@pytest.mark.unit
class TestRunnerEdgeCases:
    """测试边界情况和错误处理"""

    def test_get_results_before_run(self):
        """测试在运行前获取结果"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file)
            results = engine.get_results()
            assert results == {}

        finally:
            Path(strategy_file).unlink()

    def test_path_object_as_strategy_file(self):
        """测试使用Path对象作为策略文件"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = Path(f.name)

        try:
            engine = BacktestEngine(strategy_file)
            assert engine.strategy_file == strategy_file

        finally:
            strategy_file.unlink()

    def test_zero_days(self):
        """测试days=0的情况"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file, days=0)
            # days=0应该被转换为默认值10
            assert engine.days == 10

        finally:
            Path(strategy_file).unlink()

    def test_none_days(self):
        """测试days=None的情况"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            strategy_file = f.name

        try:
            engine = BacktestEngine(strategy_file, days=None)
            assert engine.days == 10  # 默认值

        finally:
            Path(strategy_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
