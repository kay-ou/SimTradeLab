# -*- coding: utf-8 -*-
"""
SimTradeLab 命令行接口测试 (重构后)
"""

import sys
from unittest.mock import patch, mock_open

import pytest

from simtradelab.cli import main


@pytest.fixture(autouse=True)
def setup_teardown():
    """在每个测试前后保存和恢复sys.argv"""
    original_argv = sys.argv
    yield
    sys.argv = original_argv


@pytest.fixture
def mock_files():
    """模拟策略和配置文件"""
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "builtins.open", mock_open(read_data="backtest: {}")
    ) as mock_file, patch("yaml.safe_load") as mock_yaml_load:
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"backtest": {}}
        yield mock_file, mock_yaml_load


def test_cli_basic_run(mock_files):
    """测试最基本的CLI运行"""
    strategy_file = "dummy_strategy.py"
    config_file = "dummy_config.yaml"

    test_args = ["simtradelab", "--strategy", strategy_file, "--config", config_file]

    with patch("sys.argv", test_args), patch(
        "simtradelab.cli.BacktestRunner"
    ) as mock_runner_class, patch("sys.exit") as mock_exit:
        mock_runner_instance = mock_runner_class.return_value.__enter__.return_value
        mock_runner_instance.run.return_value = {"total_return_pct": 10.5}

        main()

        mock_runner_class.assert_called_once()
        call_kwargs = mock_runner_class.call_args.kwargs
        assert call_kwargs["strategy_file"] == strategy_file
        assert call_kwargs["config"] == {"backtest": {}}

        mock_runner_instance.run.assert_called_once()
        mock_exit.assert_called_once_with(0)


def test_cli_strategy_file_not_found():
    """测试策略文件不存在的情况"""
    strategy_file = "non_existent_strategy.py"
    config_file = "dummy_config.yaml"

    test_args = ["simtradelab", "--strategy", strategy_file, "--config", config_file]

    with patch("sys.argv", test_args), patch(
        "pathlib.Path.exists", side_effect=[False, True]
    ), patch("sys.exit") as mock_exit:
        mock_exit.side_effect = SystemExit  # 模拟 sys.exit 的行为

        with pytest.raises(SystemExit):
            main()

        mock_exit.assert_called_once_with(1)


def test_cli_config_file_not_found():
    """测试配置文件不存在的情况"""
    strategy_file = "dummy_strategy.py"
    config_file = "non_existent_config.yaml"

    test_args = ["simtradelab", "--strategy", strategy_file, "--config", config_file]

    with patch("sys.argv", test_args), patch(
        "pathlib.Path.exists", side_effect=[True, False]
    ), patch("sys.exit") as mock_exit:
        mock_exit.side_effect = SystemExit

        with pytest.raises(SystemExit):
            main()

        mock_exit.assert_called_once_with(1)


def test_cli_quiet_mode(mock_files):
    """测试静默模式"""
    strategy_file = "dummy_strategy.py"
    config_file = "dummy_config.yaml"

    test_args = ["simtradelab", "-s", strategy_file, "-c", config_file, "-q"]

    with patch("sys.argv", test_args), patch(
        "simtradelab.cli.BacktestRunner"
    ) as mock_runner_class, patch("sys.exit") as mock_exit, patch(
        "builtins.print"
    ) as mock_print:
        mock_runner_instance = mock_runner_class.return_value.__enter__.return_value
        mock_runner_instance.run.return_value = {"total_return_pct": 10.5}

        main()

        mock_print.assert_called_once_with("收益率: +10.50%")
        mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__])
