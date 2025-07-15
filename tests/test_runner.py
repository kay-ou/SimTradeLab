# -*- coding: utf-8 -*-
"""
runner.py 测试文件 (重构后)

测试SimTradeLab的用户友好启动器接口
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simtradelab.backtest.engine import BacktestEngine
from simtradelab.core.plugin_manager import PluginManager
from simtradelab.runner import BacktestRunner, run_backtest


@pytest.fixture
def mock_config():
    """提供一个默认的配置文件"""
    return {
        "backtest": {
            "matching_engine": "simple",
            "slippage_model": "fixed",
            "commission_model": "fixed",
        }
    }


@pytest.fixture
def strategy_file():
    """创建一个临时的策略文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def initialize(context):\n    pass\n")
        file_path = f.name
    yield file_path
    Path(file_path).unlink()


@patch("simtradelab.runner.PluginManager")
@patch("simtradelab.runner.BacktestEngine")
def test_backtest_runner_initialization(
    mock_engine_class, mock_pm_class, strategy_file
):
    """
    测试 BacktestRunner 的初始化过程

    更新测试以匹配新的统一插件管理架构
    """
    mock_pm_instance = MagicMock(spec=PluginManager)
    mock_pm_class.return_value = mock_pm_instance

    mock_engine_instance = MagicMock(spec=BacktestEngine)
    mock_engine_class.return_value = mock_engine_instance

    # 模拟get_all_plugins返回空字典，触发插件注册
    mock_pm_instance.get_all_plugins.return_value = {}

    config = {
        "backtest": {
            "matching_engine": "SimpleMatchingEngine",
            "slippage_model": "FixedSlippageModel",
            "commission_model": "FixedCommissionModel",
        }
    }

    runner = BacktestRunner(strategy_file=strategy_file, config=config)

    # 验证初始化
    assert runner.strategy_file == strategy_file
    assert runner.config == config
    assert runner.plugin_manager == mock_pm_instance

    # 验证插件注册是否被调用（而不是加载）
    assert mock_pm_instance.register_plugin.call_count >= 3  # 至少注册3个默认插件

    # 验证 BacktestEngine 是否用PluginManager正确实例化
    mock_engine_class.assert_called_once_with(
        plugin_manager=mock_pm_instance,
        config=config["backtest"],
    )


@patch("simtradelab.runner.BacktestRunner")
def test_run_backtest_function(mock_runner_class, strategy_file, mock_config):
    """测试 run_backtest 便捷函数"""
    mock_runner_instance = MagicMock()
    mock_runner_class.return_value.__enter__.return_value = mock_runner_instance

    run_backtest(strategy_file=strategy_file, config=mock_config)

    # 验证 BacktestRunner 是否被正确调用
    mock_runner_class.assert_called_with(
        strategy_file=strategy_file, config=mock_config
    )

    # 验证 run 方法是否被调用
    mock_runner_instance.run.assert_called_once()


def test_runner_integration_run(strategy_file):
    """
    一个更完整的集成测试，验证运行流程
    注意：这个测试依赖于真实的插件和引擎，需要保证它们是可用的
    """
    # 使用一个简单的配置
    config = {
        "backtest": {
            "matching_engine": "simple_matching_engine",
            "slippage_model": "fixed_slippage_model",
            "commission_model": "fixed_commission_model",
        },
        "plugins": {
            "simple_matching_engine": {
                "class": "simtradelab.backtest.plugins.matching_engines.SimpleMatchingEngine",
                "config": {},
            },
            "fixed_slippage_model": {
                "class": "simtradelab.backtest.plugins.slippage_models.FixedSlippageModel",
                "config": {},
            },
            "fixed_commission_model": {
                "class": "simtradelab.backtest.plugins.commission_models.FixedCommissionModel",
                "config": {},
            },
        },
    }

    # 模拟 get_statistics 方法以避免完整的策略运行
    with patch.object(
        BacktestEngine, "get_statistics", return_value={"status": "ok"}
    ) as mock_get_stats:
        runner = BacktestRunner(strategy_file=strategy_file, config=config)
        results = runner.run()

        mock_get_stats.assert_called_once()
        assert results["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__])


class TestBacktestRunnerAdditional:
    """额外的BacktestRunner测试用例，提升覆盖率"""
    
    def test_runner_with_custom_plugin_manager(self, strategy_file, mock_config):
        """测试使用自定义PluginManager初始化"""
        custom_pm = MagicMock(spec=PluginManager)
        custom_pm.get_all_plugins.return_value = {}
        
        with patch("simtradelab.runner.BacktestEngine") as mock_engine:
            runner = BacktestRunner(
                strategy_file=strategy_file, 
                config=mock_config,
                plugin_manager=custom_pm
            )
            
            assert runner.plugin_manager is custom_pm
            # 应该仍然调用插件注册
            assert custom_pm.register_plugin.called
    
    def test_runner_with_plugins_in_config(self, strategy_file):
        """测试配置中包含插件配置"""
        config = {
            "backtest": {"matching_engine": "simple"},
            "plugins": {
                "test_plugin": {
                    "class": "test.Plugin",
                    "config": {"param": "value"}
                }
            }
        }
        
        with patch("simtradelab.runner.BacktestEngine") as mock_engine:
            with patch("simtradelab.runner.PluginManager") as mock_pm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_pm.get_all_plugins.return_value = {}
                
                runner = BacktestRunner(strategy_file=strategy_file, config=config)
                
                # 验证从配置注册插件被调用
                mock_pm.register_plugins_from_config.assert_called_once_with(config["plugins"])
    
    def test_runner_plugin_registration_error(self, strategy_file, mock_config):
        """测试插件注册错误处理"""
        with patch("simtradelab.runner.BacktestEngine") as mock_engine:
            with patch("simtradelab.runner.PluginManager") as mock_pm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                mock_pm.get_all_plugins.return_value = {}
                
                # 模拟注册插件时发生错误
                mock_pm.register_plugin.side_effect = Exception("Plugin registration failed")
                
                # 应该能正常初始化，只是记录警告
                runner = BacktestRunner(strategy_file=strategy_file, config=mock_config)
                assert runner is not None
    
    def test_runner_context_manager(self, strategy_file, mock_config):
        """测试上下文管理器功能"""
        with patch("simtradelab.runner.BacktestEngine") as mock_engine:
            runner = BacktestRunner(strategy_file=strategy_file, config=mock_config)
            
            # 测试__enter__
            assert runner.__enter__() is runner
            
            # 测试__exit__
            runner.__exit__(None, None, None)  # 应该不抛出异常
    
    def test_runner_run_method_logging(self, strategy_file, mock_config):
        """测试run方法的日志记录"""
        with patch("simtradelab.runner.BacktestEngine") as mock_engine_class:
            mock_engine_instance = MagicMock()
            mock_engine_class.return_value = mock_engine_instance
            mock_engine_instance.get_statistics.return_value = {"pnl": 1000}
            
            runner = BacktestRunner(strategy_file=strategy_file, config=mock_config)
            
            with patch.object(runner, 'logger') as mock_logger:
                result = runner.run()
                
                # 验证日志调用
                mock_logger.info.assert_any_call(f"Starting backtest for strategy: {strategy_file}")
                mock_logger.info.assert_any_call(f"Backtest finished. Stats: {{'pnl': 1000}}")
                
                assert result == {"pnl": 1000}
    
    def test_ensure_backtest_plugins_already_registered(self, strategy_file, mock_config):
        """测试当插件已经注册时的行为"""
        with patch("simtradelab.runner.BacktestEngine") as mock_engine:
            with patch("simtradelab.runner.PluginManager") as mock_pm_class:
                mock_pm = MagicMock()
                mock_pm_class.return_value = mock_pm
                
                # 模拟插件已经注册
                mock_pm.get_all_plugins.return_value = {
                    "SimpleMatchingEngine": MagicMock(),
                    "FixedSlippageModel": MagicMock(),
                    "FixedCommissionModel": MagicMock()
                }
                
                runner = BacktestRunner(strategy_file=strategy_file, config=mock_config)
                
                # 验证没有调用register_plugin，因为插件已存在
                mock_pm.register_plugin.assert_not_called()
    
    def test_run_backtest_with_exception_handling(self, strategy_file, mock_config):
        """测试run_backtest函数的异常处理"""
        with patch("simtradelab.runner.BacktestRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner_class.return_value = mock_runner
            mock_runner.__enter__.return_value = mock_runner
            mock_runner.run.side_effect = Exception("Backtest failed")
            
            # 异常应该被传播
            with pytest.raises(Exception, match="Backtest failed"):
                run_backtest(strategy_file=strategy_file, config=mock_config)
