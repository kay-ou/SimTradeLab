# -*- coding: utf-8 -*-
"""
runner.py 测试文件 (重构后)

测试SimTradeLab的用户友好启动器接口
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simtradelab.runner import BacktestRunner, run_backtest
from simtradelab.core.plugin_manager import PluginManager
from simtradelab.backtest.engine import BacktestEngine
from simtradelab.backtest.plugins.base import (
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
)

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
def test_backtest_runner_initialization(mock_engine_class, mock_pm_class, strategy_file):
    """测试 BacktestRunner 的初始化过程"""
    mock_pm_instance = MagicMock(spec=PluginManager)
    mock_pm_class.return_value = mock_pm_instance
    
    mock_engine_instance = MagicMock(spec=BacktestEngine)
    mock_engine_class.return_value = mock_engine_instance

    # 模拟插件加载，确保返回正确的类型
    mock_matching_engine = MagicMock(spec=BaseMatchingEngine)
    mock_slippage_model = MagicMock(spec=BaseSlippageModel)
    mock_commission_model = MagicMock(spec=BaseCommissionModel)
    
    mock_pm_instance.load_plugin.side_effect = [
        mock_matching_engine,
        mock_slippage_model,
        mock_commission_model,
    ]
    
    config = {
        "backtest": {
            "matching_engine": "simple",
            "slippage_model": "fixed",
            "commission_model": "fixed",
        }
    }

    runner = BacktestRunner(strategy_file=strategy_file, config=config)

    # 验证初始化
    assert runner.strategy_file == strategy_file
    assert runner.config == config
    assert runner.plugin_manager == mock_pm_instance
    
    # 验证插件加载是否被调用
    assert mock_pm_instance.load_plugin.call_count == 3
    
    # 验证 BacktestEngine 是否用加载的插件正确实例化
    mock_engine_class.assert_called_once_with(
        matching_engine=mock_matching_engine,
        slippage_model=mock_slippage_model,
        commission_model=mock_commission_model,
    )

@patch("simtradelab.runner.BacktestRunner")
def test_run_backtest_function(mock_runner_class, strategy_file, mock_config):
    """测试 run_backtest 便捷函数"""
    mock_runner_instance = MagicMock()
    mock_runner_class.return_value.__enter__.return_value = mock_runner_instance

    run_backtest(strategy_file=strategy_file, config=mock_config)

    # 验证 BacktestRunner 是否被正确调用
    mock_runner_class.assert_called_with(strategy_file=strategy_file, config=mock_config)
    
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
                "config": {}
            },
            "fixed_slippage_model": {
                "class": "simtradelab.backtest.plugins.slippage_models.FixedSlippageModel",
                "config": {}
            },
            "fixed_commission_model": {
                "class": "simtradelab.backtest.plugins.commission_models.FixedCommissionModel",
                "config": {}
            }
        }
    }

    # 模拟 get_statistics 方法以避免完整的策略运行
    with patch.object(BacktestEngine, 'get_statistics', return_value={"status": "ok"}) as mock_get_stats:
        runner = BacktestRunner(strategy_file=strategy_file, config=config)
        results = runner.run()
        
        mock_get_stats.assert_called_once()
        assert results["status"] == "ok"

if __name__ == "__main__":
    pytest.main([__file__])
