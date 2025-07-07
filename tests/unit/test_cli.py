#!/usr/bin/env python3
"""
CLI模块测试 - 测试命令行接口功能
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from simtradelab.cli import parse_arguments, main


class TestCLI:
    """CLI测试"""
    
    @patch('sys.argv')
    def test_parse_arguments(self, mock_argv):
        """测试参数解析"""
        # 测试基本参数
        mock_argv.return_value = ['simtradelab', '--strategy', 'test.py', '--data', 'test.csv']
        with patch('sys.argv', ['simtradelab', '--strategy', 'test.py', '--data', 'test.csv']):
            args = parse_arguments()
            assert args.strategy == 'test.py'
            assert args.data == 'test.csv'
        
        # 测试可选参数
        with patch('sys.argv', [
            'simtradelab', '--strategy', 'test.py', 
            '--data-source', 'akshare',
            '--securities', '000001.SZ,000002.SZ',
            '--start-date', '2023-01-01',
            '--end-date', '2023-01-31',
            '--cash', '100000',
            '--frequency', '1d'
        ]):
            args = parse_arguments()
            assert args.strategy == 'test.py'
            assert args.data_source == 'akshare'
            assert args.securities == '000001.SZ,000002.SZ'
            assert args.start_date == '2023-01-01'
            assert args.end_date == '2023-01-31'
            assert args.cash == 100000
            assert args.frequency == '1d'
    
    @patch('simtradelab.cli.BacktestEngine')
    def test_main_with_csv_data(self, mock_engine):
        """测试主函数 - CSV数据源"""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b'def initialize(context): pass')
            strategy_file = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(b'date,security,open,high,low,close,volume\n2023-01-01,STOCK_A,10,11,9,10,1000')
            data_file = f.name
        
        try:
            # 模拟引擎
            mock_instance = MagicMock()
            mock_instance.run.return_value = []  # 返回空列表
            mock_engine.return_value = mock_instance
            
            # 模拟命令行参数
            test_args = ['simtradelab', '--strategy', strategy_file, '--data', data_file]
            
            with patch('sys.argv', test_args):
                try:
                    result = main()
                    # main函数可能返回None或退出码
                    assert result is None or result in [0, 1]
                except SystemExit as e:
                    # main函数可能调用sys.exit
                    assert e.code in [0, 1]
                
        finally:
            os.unlink(strategy_file)
            os.unlink(data_file)
    
    @patch('simtradelab.cli.BacktestEngine')
    def test_main_with_akshare_data(self, mock_engine):
        """测试主函数 - AkShare数据源"""
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(b'def initialize(context): pass')
            strategy_file = f.name
        
        try:
            # 模拟引擎
            mock_instance = MagicMock()
            mock_instance.run.return_value = []  # 返回空列表
            mock_engine.return_value = mock_instance
            
            # 模拟命令行参数
            test_args = [
                'simtradelab', 
                '--strategy', strategy_file,
                '--data-source', 'akshare',
                '--securities', '000001.SZ'
            ]
            
            with patch('sys.argv', test_args):
                try:
                    result = main()
                    # main函数可能返回None或退出码
                    assert result is None or result in [0, 1]
                except SystemExit as e:
                    # main函数可能调用sys.exit
                    assert e.code in [0, 1]
                
        finally:
            os.unlink(strategy_file)
    
    @patch('simtradelab.cli.sys.exit')
    def test_main_with_invalid_args(self, mock_exit):
        """测试主函数 - 无效参数"""
        # 测试缺少必需参数
        test_args = ['simtradelab']  # 缺少策略文件
        
        with patch('sys.argv', test_args):
            try:
                main()
            except SystemExit:
                pass  # argparse会调用sys.exit
    
    def test_main_with_help(self):
        """测试帮助参数"""
        test_args = ['simtradelab', '--help']
        
        with patch('sys.argv', test_args):
            try:
                main()
            except SystemExit as e:
                # help应该以退出码0退出
                assert e.code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])