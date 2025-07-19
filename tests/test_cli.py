# -*- coding: utf-8 -*-
"""
SimTradeLab 命令行接口测试 (重构后)
"""

import sys
from unittest.mock import patch

import pytest

from simtradelab.cli import main
from simtradelab.runner import BacktestRunner


@pytest.fixture(autouse=True)
def setup_teardown():
    """在每个测试前后保存和恢复sys.argv"""
    original_argv = sys.argv
    yield
    sys.argv = original_argv


@pytest.fixture
def mock_path_exists():
    """模拟路径存在检查"""
    with patch("pathlib.Path.exists", return_value=True) as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_run_result():
    """提供一个完整的回测结果mock字典"""
    return {
        "final_portfolio_value": 110500.0,
        "total_return_pct": 0.105,
        "annualized_return_pct": 0.12,
        "sharpe_ratio": 1.2,
        "max_drawdown_pct": -0.05,
        "annualized_volatility_pct": 0.15,
        "calmar_ratio": 2.4,
        "total_orders": 10,
        "total_trades": 8,
        "trade_rate": 0.8,
    }


def test_cli_basic_run(mock_path_exists, mock_run_result):
    """测试最基本的CLI运行"""
    strategy_file = "dummy_strategy.py"
    config_file = "dummy_config.yaml"

    test_args = ["simtradelab", "--strategy", strategy_file, "--config", config_file]

    with patch("sys.argv", test_args), patch(
        "simtradelab.cli.BacktestRunner"
    ) as mock_runner_class, patch("sys.exit") as mock_exit:
        mock_runner_instance = mock_runner_class.return_value
        mock_runner_instance.run.return_value = mock_run_result

        main()

        mock_runner_class.assert_called_once()
        call_kwargs = mock_runner_class.call_args.kwargs
        assert call_kwargs["strategy_file"] == strategy_file
        assert call_kwargs["config_file"] == config_file

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


def test_cli_quiet_mode(mock_path_exists, mock_run_result):
    """测试静默模式"""
    strategy_file = "dummy_strategy.py"
    config_file = "dummy_config.yaml"

    test_args = ["simtradelab", "-s", strategy_file, "-c", config_file, "-q"]

    with patch("sys.argv", test_args), patch(
        "simtradelab.cli.BacktestRunner"
    ) as mock_runner_class, patch("sys.exit") as mock_exit, patch(
        "builtins.print"
    ) as mock_print:
        mock_runner_instance = mock_runner_class.return_value
        mock_runner_instance.run.return_value = mock_run_result

        main()

        mock_print.assert_called_once_with("累计收益率: +10.50%")
        mock_exit.assert_called_once_with(0)


@pytest.mark.integration
def test_cli_run_buy_and_hold_strategy_e2e():
    """
    测试: 通过CLI成功运行一个完整的'buy_and_hold'策略回测。

    这个测试会:
    1. 使用一个真实的、简单的策略文件。
    2. 使用一个最小化的、真实的配置文件。
    3. 调用 `main()` 函数来启动整个流程。
    4. 捕获标准输出，并验证最终的回测结果摘要是否被正确打印。
    5. 验证程序是否以状态码 0 正常退出。
    """
    # 定义真实的策略和配置文件路径
    # 注意：这里的路径是相对于项目根目录的
    strategy_file = "strategies/buy_and_hold_strategy.py"
    config_file = "simtradelab_config.yaml"  # 使用项目根目录的默认配置

    # 构造命令行参数
    test_args = [
        "simtradelab",
        "--strategy",
        strategy_file,
        "--config",
        config_file,
    ]

    # 使用 patch 来捕获 sys.exit 和 print 的调用
    with patch("sys.argv", test_args), patch("sys.exit") as mock_exit, patch(
        "builtins.print"
    ) as mock_print:
        # 执行主程序
        main()

        # 断言程序正常退出
        mock_exit.assert_called_once_with(0)

        # 断言回测结果的摘要被打印出来
        # 我们在这里寻找任何包含 "Final Portfolio Value" 的输出
        # 这是一个很强的信号，表明回测运行到了最后
        printed_output = "\n".join(
            [str(call.args[0]) for call in mock_print.call_args_list]
        )
        # 断言本地化的回测结果摘要被打印出来
        # 检查关键的中文指标
        assert "最终投资组合价值" in printed_output
        assert "总回报率" in printed_output
        assert "夏普比率" in printed_output


if __name__ == "__main__":
    pytest.main([__file__])
