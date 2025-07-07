#!/usr/bin/env python3
"""
CLI模块测试 - 测试命令行接口功能
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

from simtradelab.cli import parse_arguments, main, validate_arguments, create_data_source, get_securities_list, get_date_range


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


class TestCLIValidateArguments:
    """CLI参数验证函数测试"""
    
    def test_validate_arguments_valid_csv_args(self, temp_dir):
        """测试有效CSV参数验证"""
        # 创建临时策略文件
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        # 创建临时CSV文件
        csv_file = Path(temp_dir) / "data.csv"
        csv_file.write_text("date,security,open,high,low,close,volume\n")
        
        # 创建模拟参数对象
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = str(csv_file)
        args.data_source = None
        args.securities = None
        args.start_date = None
        args.end_date = None
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) == 0
    
    def test_validate_arguments_missing_strategy_file(self):
        """测试策略文件不存在"""
        args = Mock()
        args.strategy = "/nonexistent/strategy.py"
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001.SZ"
        args.start_date = None
        args.end_date = None
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("策略文件不存在" in error for error in errors)
    
    def test_validate_arguments_missing_csv_file(self, temp_dir):
        """测试CSV文件不存在"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = "/nonexistent/data.csv"
        args.data_source = None
        args.securities = None
        args.start_date = None
        args.end_date = None
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("数据文件不存在" in error for error in errors)
    
    def test_validate_arguments_missing_securities_for_real_data(self, temp_dir):
        """测试真实数据源缺少securities参数"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = None
        args.start_date = None
        args.end_date = None
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("必须指定 --securities 参数" in error for error in errors)
    
    def test_validate_arguments_invalid_security_code_format(self, temp_dir):
        """测试无效股票代码格式"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001,600000.SH,INVALID"
        args.start_date = None
        args.end_date = None
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        # 应该有两个错误：000001和INVALID都不符合格式
        invalid_codes = [e for e in errors if "股票代码格式错误" in e]
        assert len(invalid_codes) == 2
    
    def test_validate_arguments_invalid_start_date_format(self, temp_dir):
        """测试无效开始日期格式"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001.SZ"
        args.start_date = "2024/12/01"
        args.end_date = None
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("开始日期格式错误" in error for error in errors)
    
    def test_validate_arguments_invalid_end_date_format(self, temp_dir):
        """测试无效结束日期格式"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001.SZ"
        args.start_date = None
        args.end_date = "invalid-date"
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("结束日期格式错误" in error for error in errors)
    
    def test_validate_arguments_start_date_after_end_date(self, temp_dir):
        """测试开始日期晚于结束日期"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001.SZ"
        args.start_date = "2024-12-05"
        args.end_date = "2024-12-01"
        args.cash = 1000000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("开始日期必须早于结束日期" in error for error in errors)
    
    def test_validate_arguments_negative_cash(self, temp_dir):
        """测试负数初始资金"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001.SZ"
        args.start_date = None
        args.end_date = None
        args.cash = -1000.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("初始资金必须大于0" in error for error in errors)
    
    def test_validate_arguments_zero_cash(self, temp_dir):
        """测试零初始资金"""
        strategy_file = Path(temp_dir) / "strategy.py"
        strategy_file.write_text("def initialize(context): pass")
        
        args = Mock()
        args.strategy = str(strategy_file)
        args.data = None
        args.data_source = "akshare"
        args.securities = "000001.SZ"
        args.start_date = None
        args.end_date = None
        args.cash = 0.0
        
        errors = validate_arguments(args)
        assert len(errors) > 0
        assert any("初始资金必须大于0" in error for error in errors)


class TestCLICreateDataSource:
    """CLI数据源创建函数测试"""
    
    def test_create_data_source_csv(self):
        """测试创建CSV数据源"""
        args = Mock()
        args.data = "/path/to/data.csv"
        args.data_source = None
        
        result = create_data_source(args)
        assert result == "/path/to/data.csv"
    
    @patch('simtradelab.cli.AkshareDataSource')
    def test_create_data_source_akshare(self, mock_akshare):
        """测试创建AkShare数据源"""
        mock_instance = Mock()
        mock_akshare.return_value = mock_instance
        
        args = Mock()
        args.data = None
        args.data_source = "akshare"
        
        result = create_data_source(args)
        assert result == mock_instance
        mock_akshare.assert_called_once()
    
    @patch('simtradelab.cli.TushareDataSource')
    def test_create_data_source_tushare(self, mock_tushare):
        """测试创建Tushare数据源"""
        mock_instance = Mock()
        mock_tushare.return_value = mock_instance
        
        args = Mock()
        args.data = None
        args.data_source = "tushare"
        
        result = create_data_source(args)
        assert result == mock_instance
        mock_tushare.assert_called_once()
    
    def test_create_data_source_invalid(self):
        """测试创建无效数据源"""
        args = Mock()
        args.data = None
        args.data_source = None
        
        with pytest.raises(ValueError, match="未指定有效的数据源"):
            create_data_source(args)


class TestCLIGetSecuritiesList:
    """CLI股票列表获取函数测试"""
    
    def test_get_securities_list_with_securities(self):
        """测试获取股票列表（有securities参数）"""
        args = Mock()
        args.securities = "000001.SZ,000002.SZ, 600000.SH"
        
        result = get_securities_list(args)
        assert result == ["000001.SZ", "000002.SZ", "600000.SH"]
    
    def test_get_securities_list_with_spaces(self):
        """测试获取股票列表（包含空格）"""
        args = Mock()
        args.securities = " 000001.SZ , 000002.SZ  ,600000.SH "
        
        result = get_securities_list(args)
        assert result == ["000001.SZ", "000002.SZ", "600000.SH"]
    
    def test_get_securities_list_single_security(self):
        """测试获取单个股票"""
        args = Mock()
        args.securities = "000001.SZ"
        
        result = get_securities_list(args)
        assert result == ["000001.SZ"]
    
    def test_get_securities_list_empty_securities(self):
        """测试空securities参数"""
        args = Mock()
        args.securities = None
        
        result = get_securities_list(args)
        assert result is None
    
    def test_get_securities_list_empty_string(self):
        """测试空字符串securities参数"""
        args = Mock()
        args.securities = ""
        
        result = get_securities_list(args)
        # 空字符串会返回None，因为if args.securities检查为 False
        assert result is None


class TestCLIGetDateRange:
    """CLI日期范围获取函数测试"""
    
    def test_get_date_range_with_both_dates(self):
        """测试指定开始和结束日期"""
        args = Mock()
        args.start_date = "2024-12-01"
        args.end_date = "2024-12-05"
        args.data_source = None
        
        start, end = get_date_range(args)
        assert start == "2024-12-01"
        assert end == "2024-12-05"
    
    def test_get_date_range_with_start_date_only(self):
        """测试只指定开始日期"""
        args = Mock()
        args.start_date = "2024-12-01"
        args.end_date = None
        args.data_source = None
        
        start, end = get_date_range(args)
        assert start == "2024-12-01"
        assert end is None
    
    def test_get_date_range_with_end_date_only(self):
        """测试只指定结束日期"""
        args = Mock()
        args.start_date = None
        args.end_date = "2024-12-05"
        args.data_source = None
        
        start, end = get_date_range(args)
        assert start is None
        assert end == "2024-12-05"
    
    @patch('simtradelab.cli.datetime')
    def test_get_date_range_real_data_source_defaults(self, mock_datetime):
        """测试真实数据源的默认日期范围"""
        from datetime import datetime as real_datetime, timedelta as real_timedelta
        
        # 设置mock当前时间为2024-12-05
        mock_now = real_datetime(2024, 12, 5)
        mock_datetime.now.return_value = mock_now
        
        # 设置timedelta
        mock_datetime.timedelta = real_timedelta
        
        args = Mock()
        args.start_date = None
        args.end_date = None
        args.data_source = "akshare"
        
        start, end = get_date_range(args)
        assert end == "2024-12-05"
        assert start == "2024-11-05"
    
    @patch('simtradelab.cli.datetime')
    def test_get_date_range_real_data_source_with_start_date(self, mock_datetime):
        """测试真实数据源指定开始日期"""
        mock_now = Mock()
        mock_now.strftime.return_value = "2024-12-05"
        mock_datetime.now.return_value = mock_now
        
        args = Mock()
        args.start_date = "2024-12-01"
        args.end_date = None
        args.data_source = "akshare"
        
        start, end = get_date_range(args)
        assert start == "2024-12-01"
        assert end == "2024-12-05"
    
    @patch('simtradelab.cli.datetime')
    def test_get_date_range_real_data_source_with_end_date(self, mock_datetime):
        """测试真实数据源指定结束日期"""
        mock_timedelta_result = Mock()
        mock_timedelta_result.strftime.return_value = "2024-11-05"
        mock_datetime.now.return_value.__sub__.return_value = mock_timedelta_result
        
        args = Mock()
        args.start_date = None
        args.end_date = "2024-12-10"
        args.data_source = "akshare"
        
        start, end = get_date_range(args)
        assert start == "2024-11-05"
        assert end == "2024-12-10"
    
    def test_get_date_range_csv_data_source(self):
        """测试CSV数据源不设置默认日期"""
        args = Mock()
        args.start_date = None
        args.end_date = None
        args.data_source = None
        
        start, end = get_date_range(args)
        assert start is None
        assert end is None
    
    @patch('simtradelab.cli.datetime')
    def test_get_date_range_real_data_source_no_end_date_set(self, mock_datetime):
        """测试真实数据源且end_date未设置的情况"""
        from datetime import datetime as real_datetime, timedelta as real_timedelta
        
        # 设置mock当前时间为2024-12-05
        mock_now = real_datetime(2024, 12, 5)
        mock_datetime.now.return_value = mock_now
        
        # 设置timedelta
        mock_datetime.timedelta = real_timedelta
        
        args = Mock()
        args.start_date = None
        args.end_date = None
        args.data_source = "tushare"
        
        start, end = get_date_range(args)
        assert start == "2024-11-05"
        assert end == "2024-12-05"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])