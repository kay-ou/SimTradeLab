# -*- coding: utf-8 -*-
"""
SimTradeLab 命令行接口测试
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from simtradelab.cli import main


@pytest.fixture(autouse=True)
def setup_teardown():
    """在每个测试前后保存和恢复sys.argv"""
    original_argv = sys.argv
    yield
    sys.argv = original_argv


def test_cli_basic_strategy_run():
    """测试最基本的策略运行命令"""
    strategy_file = "tests/assets/dummy_strategy.py"
    
    # 模拟命令行参数
    test_args = ["simtradelab", "--strategy", strategy_file]
    
    with patch("sys.argv", test_args), \
         patch("simtradelab.cli.run_strategy") as mock_run_strategy, \
         patch("sys.exit") as mock_exit:
        
        main()
        
        # 验证 run_strategy 是否被调用
        mock_run_strategy.assert_called_once()
        
        # 验证调用时的关键字参数
        call_kwargs = mock_run_strategy.call_args.kwargs
        assert call_kwargs["strategy_file"] == Path(strategy_file)
        assert call_kwargs["initial_cash"] == 1000000.0
        assert call_kwargs["days"] == 10
        
        # 验证程序正常退出
        mock_exit.assert_called_once_with(0)


def test_cli_with_all_arguments():
    """测试所有命令行参数都能被正确解析和传递"""
    strategy_file = "tests/assets/dummy_strategy.py"
    output_file = "tests/assets/results.json"
    
    test_args = [
        "simtradelab",
        "--strategy", strategy_file,
        "--days", "50",
        "--cash", "500000",
        "--commission", "0.00025",
        "--slippage", "0.0015",
        "--output", output_file,
        "--quiet"
    ]
    
    with patch("sys.argv", test_args), \
         patch("simtradelab.cli.run_strategy") as mock_run_strategy, \
         patch("builtins.open"), \
         patch("json.dump"), \
         patch("sys.exit") as mock_exit:
        
        # 模拟 run_strategy 返回一个字典以测试输出功能
        mock_run_strategy.return_value = {"total_return_pct": 5.5}
        
        main()
        
        mock_run_strategy.assert_called_once()
        
        call_kwargs = mock_run_strategy.call_args.kwargs
        assert call_kwargs["strategy_file"] == Path(strategy_file)
        assert call_kwargs["initial_cash"] == 500000.0
        assert call_kwargs["days"] == 50
        assert call_kwargs["commission_rate"] == 0.00025
        assert call_kwargs["slippage_rate"] == 0.0015
        assert call_kwargs["quiet"] is True
        
        mock_exit.assert_called_once_with(0)


def test_cli_strategy_file_not_found():
    """测试当策略文件不存在时，程序会以错误码退出"""
    strategy_file = "tests/assets/non_existent_strategy.py"
    
    test_args = ["simtradelab", "--strategy", strategy_file]
    
    with patch("sys.argv", test_args), \
         patch("simtradelab.cli.run_strategy") as mock_run_strategy, \
         patch("sys.exit") as mock_exit:
        
        mock_exit.side_effect = lambda code: (_ for _ in ()).throw(SystemExit(code))
        
        with pytest.raises(SystemExit):
            main()
        
        # 验证 run_strategy 没有被调用
        mock_run_strategy.assert_not_called()
        
        # 验证程序以错误码 1 退出
        mock_exit.assert_called_once_with(1)


def test_cli_data_file_not_found():
    """测试当数据文件不存在时，程序会以错误码退出"""
    strategy_file = "tests/assets/dummy_strategy.py"
    data_file = "tests/assets/non_existent_data.csv"
    
    test_args = ["simtradelab", "--strategy", strategy_file, "--data", data_file]
    
    with patch("sys.argv", test_args), \
         patch("simtradelab.cli.run_strategy") as mock_run_strategy, \
         patch("sys.exit") as mock_exit:
        
        mock_exit.side_effect = lambda code: (_ for _ in ()).throw(SystemExit(code))
        
        with pytest.raises(SystemExit):
            main()
        
        # 验证 run_strategy 没有被调用
        mock_run_strategy.assert_not_called()
        
        # 验证程序以错误码 1 退出
        mock_exit.assert_called_once_with(1)
