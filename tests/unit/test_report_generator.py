#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReportGenerator模块测试
"""

import pytest
import pandas as pd
import sys
import os
import json
import yaml
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from simtradelab.report_generator import ReportGenerator
from simtradelab.context import Portfolio, Position


class TestReportGenerator:
    """ReportGenerator测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_engine(self, temp_dir):
        """创建模拟引擎"""
        engine = Mock()
        engine.strategy_file = os.path.join(temp_dir, "test_strategy.py")
        engine.start_date = pd.Timestamp('2023-01-01')
        engine.end_date = pd.Timestamp('2023-01-05')
        engine.initial_cash = 1000000.0
        engine.frequency = '1d'
        engine.securities = ['000001.SZ', '600519.SH']
        engine.data_path = None
        
        # 创建策略文件
        with open(engine.strategy_file, 'w', encoding='utf-8') as f:
            f.write("""
def initialize(context):
    pass

def handle_data(context, data):
    pass
""")
        
        # 创建模拟上下文
        context = Mock()
        context.portfolio = Mock()
        context.portfolio.cash = 500000.0
        context.portfolio.total_value = 1200000.0
        context.portfolio.positions = {}
        
        # 创建模拟交易记录器
        context.blotter = Mock()
        context.blotter.get_all_trades.return_value = []
        
        engine.context = context
        
        # 创建投资组合历史
        engine.portfolio_history = [
            {
                'datetime': pd.Timestamp('2023-01-01'),
                'total_value': 1000000.0,
                'cash': 1000000.0
            },
            {
                'datetime': pd.Timestamp('2023-01-05'),
                'total_value': 1200000.0,
                'cash': 500000.0
            }
        ]
        
        return engine
    
    @pytest.fixture
    def mock_performance_metrics(self):
        """创建模拟性能指标"""
        return {
            'total_return': 0.20,
            'annualized_return': 0.15,
            'volatility': 0.12,
            'sharpe_ratio': 1.25,
            'max_drawdown': 0.08,
            'win_rate': 0.65,
            'trading_days': 250,
            'total_trades': 50,
            'initial_value': 1000000.0,
            'final_value': 1200000.0
        }
    
    # ==================== 初始化测试 ====================
    
    @pytest.mark.unit
    def test_report_generator_initialization(self, mock_engine, temp_dir):
        """测试报告生成器初始化"""
        output_dir = os.path.join(temp_dir, "reports")
        generator = ReportGenerator(mock_engine, output_dir)
        
        assert generator.engine == mock_engine
        assert generator.strategy_name == "test_strategy"
        assert generator.output_dir == os.path.join(output_dir, "test_strategy")
        assert os.path.exists(generator.output_dir)
        assert isinstance(generator.timestamp, str)
        assert len(generator.timestamp) == 15  # YYYYMMDD_HHMMSS
    
    @pytest.mark.unit
    def test_report_generator_default_output_dir(self, mock_engine):
        """测试默认输出目录"""
        generator = ReportGenerator(mock_engine)
        
        assert generator.output_dir == os.path.join("reports", "test_strategy")
    
    # ==================== 文件名生成测试 ====================
    
    @pytest.mark.unit
    def test_generate_filename_basic(self, mock_engine, temp_dir):
        """测试基本文件名生成"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        filename = generator.generate_filename("txt", include_params=False)
        
        assert filename.startswith("test_strategy")
        assert filename.endswith(".txt")
        assert generator.timestamp in filename
    
    @pytest.mark.unit
    def test_generate_filename_with_params(self, mock_engine, temp_dir):
        """测试包含参数的文件名生成"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        filename = generator.generate_filename("json", include_params=True)
        
        expected_parts = [
            "test_strategy",
            "20230101_20230105",  # 日期范围
            "cash100w",           # 资金（万元）
            "freq1d",             # 频率
            "stocks2",            # 股票数量
            generator.timestamp
        ]
        
        for part in expected_parts:
            assert part in filename
        
        assert filename.endswith(".json")
    
    @pytest.mark.unit
    def test_generate_filename_no_dates(self, mock_engine, temp_dir):
        """测试无日期时的文件名生成"""
        mock_engine.start_date = None
        mock_engine.end_date = None
        
        generator = ReportGenerator(mock_engine, temp_dir)
        filename = generator.generate_filename("csv")
        
        assert "test_strategy" in filename
        assert filename.endswith(".csv")
        # 不应该包含日期部分
        assert "20230101" not in filename
    
    @pytest.mark.unit
    def test_generate_filename_no_securities(self, mock_engine, temp_dir):
        """测试无股票列表时的文件名生成"""
        mock_engine.securities = None
        
        generator = ReportGenerator(mock_engine, temp_dir)
        filename = generator.generate_filename("yaml", include_params=True)
        
        assert "test_strategy" in filename
        # 不应该包含stocks部分
        assert "stocks" not in filename
    
    # ==================== 综合报告测试 ====================
    
    @pytest.mark.unit
    def test_generate_comprehensive_report_success(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试成功生成综合报告"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics
            
            filepath = generator.generate_comprehensive_report()
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith(".txt")
            
            # 验证文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "simtradelab 策略回测综合报告" in content
            assert "test_strategy" in content
            assert "20.00%" in content  # 总收益率
            assert "1.250" in content   # 夏普比率
    
    @pytest.mark.unit
    def test_generate_comprehensive_report_no_metrics(self, mock_engine, temp_dir):
        """测试无性能指标时的综合报告生成"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = None
            
            filepath = generator.generate_comprehensive_report()
            
            assert filepath is None
    
    @pytest.mark.unit
    def test_generate_comprehensive_report_with_options(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试带选项的综合报告生成"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics
            
            filepath = generator.generate_comprehensive_report(
                include_strategy_code=False,
                include_trade_details=False
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            
            # 验证文件内容不包含策略代码和交易明细
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "策略代码" not in content
            assert "交易明细" not in content
    
    @pytest.mark.unit
    def test_generate_comprehensive_report_file_error(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试文件写入错误的处理"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics
            
            # 模拟文件写入错误
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                filepath = generator.generate_comprehensive_report()
                
                assert filepath is None
    
    # ==================== JSON报告测试 ====================
    
    @pytest.mark.unit
    def test_generate_json_report_success(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试成功生成JSON报告"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics
            
            filepath = generator.generate_json_report()
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith(".json")
            
            # 验证JSON内容
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert 'report_info' in data
            assert 'backtest_config' in data
            assert 'performance_metrics' in data
            assert 'portfolio_history' in data
            assert 'final_positions' in data
            assert 'trade_summary' in data
            assert 'strategy_code' in data
            
            # 验证具体内容
            assert data['report_info']['strategy_name'] == 'test_strategy'
            assert data['backtest_config']['initial_cash'] == 1000000.0
            assert data['performance_metrics']['total_return'] == 0.20
    
    @pytest.mark.unit
    def test_generate_json_report_no_strategy_file(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试策略文件不存在时的JSON报告生成"""
        # 删除策略文件
        os.remove(mock_engine.strategy_file)
        
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics
            
            filepath = generator.generate_json_report()
            
            assert filepath is not None
            
            # 验证策略代码为None
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data['strategy_code'] is None
    
    # ==================== YAML报告测试 ====================
    
    @pytest.mark.unit
    def test_generate_yaml_report_success(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试成功生成YAML报告"""
        generator = ReportGenerator(mock_engine, temp_dir)
        
        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics
            
            filepath = generator.generate_yaml_report()
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith(".yaml")
            
            # 验证YAML内容
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            assert 'report_info' in data
            assert 'backtest_config' in data
            assert 'performance_metrics' in data
            assert 'portfolio_summary' in data
            assert 'trade_summary' in data
            
            # 验证数据类型转换
            assert isinstance(data['backtest_config']['initial_cash'], float)
            assert isinstance(data['performance_metrics']['total_return'], float)
    
    @pytest.mark.unit
    def test_generate_yaml_report_no_metrics(self, mock_engine, temp_dir):
        """测试无性能指标时的YAML报告生成"""
        generator = ReportGenerator(mock_engine, temp_dir)

        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = None

            filepath = generator.generate_yaml_report()

            assert filepath is None

    # ==================== CSV报告测试 ====================

    @pytest.mark.unit
    def test_generate_csv_report_success(self, mock_engine, temp_dir):
        """测试成功生成CSV报告"""
        generator = ReportGenerator(mock_engine, temp_dir)

        filepath = generator.generate_csv_report()

        assert filepath is not None
        assert os.path.exists(filepath)
        assert filepath.endswith(".csv")

        # 验证CSV内容
        df = pd.read_csv(filepath)

        assert len(df) == 2
        assert 'total_value' in df.columns
        assert 'cash' in df.columns
        assert 'daily_return' in df.columns
        assert 'cumulative_return' in df.columns

        # 验证计算的列（使用近似比较处理浮点数精度问题）
        assert abs(df['cumulative_return'].iloc[-1] - 0.2) < 1e-10  # (1200000 / 1000000) - 1

    @pytest.mark.unit
    def test_generate_csv_report_no_history(self, mock_engine, temp_dir):
        """测试无投资组合历史时的CSV报告生成"""
        mock_engine.portfolio_history = None

        generator = ReportGenerator(mock_engine, temp_dir)
        filepath = generator.generate_csv_report()

        assert filepath is None

    @pytest.mark.unit
    def test_generate_csv_report_empty_history(self, mock_engine, temp_dir):
        """测试空投资组合历史时的CSV报告生成"""
        mock_engine.portfolio_history = []

        generator = ReportGenerator(mock_engine, temp_dir)
        filepath = generator.generate_csv_report()

        assert filepath is None

    @pytest.mark.unit
    def test_generate_csv_report_file_error(self, mock_engine, temp_dir):
        """测试CSV文件写入错误的处理"""
        generator = ReportGenerator(mock_engine, temp_dir)

        # 模拟文件写入错误
        with patch('pandas.DataFrame.to_csv', side_effect=PermissionError("Permission denied")):
            filepath = generator.generate_csv_report()

            assert filepath is None

    # ==================== 摘要报告测试 ====================

    @pytest.mark.unit
    def test_generate_summary_report_success(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试成功生成摘要报告"""
        generator = ReportGenerator(mock_engine, temp_dir)

        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics

            filepath = generator.generate_summary_report()

            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith(".summary.txt")

            # 验证摘要内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "策略回测摘要报告" in content
            assert "test_strategy" in content
            assert "20.00%" in content  # 总收益率
            assert "综合评级" in content

    @pytest.mark.unit
    def test_generate_summary_report_no_metrics(self, mock_engine, temp_dir):
        """测试无性能指标时的摘要报告生成"""
        generator = ReportGenerator(mock_engine, temp_dir)

        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = None

            filepath = generator.generate_summary_report()

            assert filepath is None

    @pytest.mark.unit
    def test_generate_summary_report_file_error(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试摘要报告文件写入错误的处理"""
        generator = ReportGenerator(mock_engine, temp_dir)

        with patch('simtradelab.report_generator.calculate_performance_metrics') as mock_calc:
            mock_calc.return_value = mock_performance_metrics

            # 模拟文件写入错误
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                filepath = generator.generate_summary_report()

                assert filepath is None

    # ==================== 私有方法测试 ====================

    @pytest.mark.unit
    def test_generate_header(self, mock_engine, temp_dir):
        """测试生成报告头部"""
        generator = ReportGenerator(mock_engine, temp_dir)

        header = generator._generate_header()

        assert "simtradelab 策略回测综合报告" in header
        assert "=" * 100 in header

    @pytest.mark.unit
    def test_generate_basic_info(self, mock_engine, temp_dir):
        """测试生成基本信息"""
        generator = ReportGenerator(mock_engine, temp_dir)

        basic_info = generator._generate_basic_info()

        assert "基本信息" in basic_info
        assert "test_strategy" in basic_info
        assert "2023-01-01 至 2023-01-05" in basic_info
        assert "1d" in basic_info
        assert "1,000,000.00" in basic_info
        assert "000001.SZ, 600519.SH" in basic_info
        assert "2只" in basic_info

    @pytest.mark.unit
    def test_generate_basic_info_with_data_source(self, mock_engine, temp_dir):
        """测试包含数据源的基本信息生成"""
        # 添加数据源
        mock_engine.data_source = Mock()
        mock_engine.data_source.__class__.__name__ = "TushareDataSource"

        generator = ReportGenerator(mock_engine, temp_dir)
        basic_info = generator._generate_basic_info()

        assert "TushareDataSource" in basic_info

    @pytest.mark.unit
    def test_generate_basic_info_with_csv_data(self, mock_engine, temp_dir):
        """测试包含CSV数据源的基本信息生成"""
        mock_engine.data_source = None
        mock_engine.data_path = "/path/to/data.csv"

        generator = ReportGenerator(mock_engine, temp_dir)
        basic_info = generator._generate_basic_info()

        assert "CSV文件 (data.csv)" in basic_info

    @pytest.mark.unit
    def test_generate_performance_section(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试生成性能指标部分"""
        generator = ReportGenerator(mock_engine, temp_dir)

        performance_section = generator._generate_performance_section(mock_performance_metrics)

        assert "收益指标" in performance_section
        assert "风险指标" in performance_section
        assert "交易统计" in performance_section
        assert "20.00%" in performance_section  # 总收益率
        assert "1.250" in performance_section   # 夏普比率
        assert "8.00%" in performance_section   # 最大回撤
        assert "65.00%" in performance_section  # 胜率
        assert "50次" in performance_section    # 总交易次数

    @pytest.mark.unit
    def test_generate_performance_section_with_benchmark(self, mock_engine, temp_dir, mock_performance_metrics):
        """测试包含基准对比的性能指标部分"""
        # 添加基准相关指标
        mock_performance_metrics.update({
            'benchmark_total_return': 0.10,
            'benchmark_annualized_return': 0.08,
            'benchmark_volatility': 0.15,
            'alpha': 0.05,
            'beta': 1.2,
            'information_ratio': 0.8,
            'tracking_error': 0.05
        })

        generator = ReportGenerator(mock_engine, temp_dir)

        # 创建模拟基准收益率
        benchmark_returns = pd.Series([0.01, 0.02, -0.01, 0.015])

        performance_section = generator._generate_performance_section(mock_performance_metrics, benchmark_returns)

        assert "基准对比" in performance_section
        assert "10.00%" in performance_section  # 基准总收益率
        assert "0.050" in performance_section   # Alpha
        assert "1.200" in performance_section   # Beta

    @pytest.mark.unit
    def test_generate_strategy_code_section(self, mock_engine, temp_dir):
        """测试生成策略代码部分"""
        generator = ReportGenerator(mock_engine, temp_dir)

        strategy_section = generator._generate_strategy_code_section()

        assert "策略代码" in strategy_section
        assert "def initialize(context):" in strategy_section
        assert "def handle_data(context, data):" in strategy_section
        # 验证行号
        assert "1:" in strategy_section
        assert "2:" in strategy_section

    @pytest.mark.unit
    def test_generate_strategy_code_section_file_error(self, mock_engine, temp_dir):
        """测试策略代码文件读取错误的处理"""
        # 删除策略文件
        os.remove(mock_engine.strategy_file)

        generator = ReportGenerator(mock_engine, temp_dir)
        strategy_section = generator._generate_strategy_code_section()

        assert "无法读取策略代码" in strategy_section

    @pytest.mark.unit
    def test_generate_trade_details_section_with_trades(self, mock_engine, temp_dir):
        """测试包含交易记录的交易明细部分"""
        # 创建模拟交易记录
        mock_trade1 = Mock()
        mock_trade1.security = '000001.SZ'
        mock_trade1.amount = 1000
        mock_trade1.price = 12.50
        mock_trade1.trade_time = pd.Timestamp('2023-01-02 09:30:00')

        mock_trade2 = Mock()
        mock_trade2.security = '600519.SH'
        mock_trade2.amount = -500
        mock_trade2.price = 180.00
        mock_trade2.trade_time = pd.Timestamp('2023-01-03 14:30:00')

        mock_engine.context.blotter.get_all_trades.return_value = [mock_trade1, mock_trade2]

        generator = ReportGenerator(mock_engine, temp_dir)
        trade_section = generator._generate_trade_details_section()

        assert "交易明细" in trade_section
        assert "总交易记录: 2笔" in trade_section
        assert "000001.SZ" in trade_section
        assert "600519.SH" in trade_section
        assert "买入" in trade_section
        assert "卖出" in trade_section
        assert "12.50" in trade_section
        assert "180.00" in trade_section

    @pytest.mark.unit
    def test_generate_trade_details_section_no_trades(self, mock_engine, temp_dir):
        """测试无交易记录的交易明细部分"""
        mock_engine.context.blotter.get_all_trades.return_value = []

        generator = ReportGenerator(mock_engine, temp_dir)
        trade_section = generator._generate_trade_details_section()

        assert "交易明细" in trade_section
        assert "无交易记录" in trade_section

    @pytest.mark.unit
    def test_generate_trade_details_section_no_blotter(self, mock_engine, temp_dir):
        """测试无交易记录器的交易明细部分"""
        # 删除blotter属性而不是设置为None
        delattr(mock_engine.context, 'blotter')

        generator = ReportGenerator(mock_engine, temp_dir)
        trade_section = generator._generate_trade_details_section()

        assert "交易明细" in trade_section
        assert "无法获取交易记录" in trade_section

    @pytest.mark.unit
    def test_generate_trade_details_section_many_trades(self, mock_engine, temp_dir):
        """测试大量交易记录的处理（只显示最近20笔）"""
        # 创建25笔交易记录
        trades = []
        for i in range(25):
            mock_trade = Mock()
            mock_trade.security = f'00000{i%3}.SZ'
            mock_trade.amount = 1000 + i * 10
            mock_trade.price = 10.0 + i * 0.1
            mock_trade.trade_time = pd.Timestamp(f'2023-01-{(i%28)+1:02d} 09:30:00')
            trades.append(mock_trade)

        mock_engine.context.blotter.get_all_trades.return_value = trades

        generator = ReportGenerator(mock_engine, temp_dir)
        trade_section = generator._generate_trade_details_section()

        assert "总交易记录: 25笔" in trade_section
        assert "省略5笔交易记录" in trade_section

    @pytest.mark.unit
    def test_generate_position_section_with_positions(self, mock_engine, temp_dir):
        """测试包含持仓的持仓信息部分"""
        # 创建模拟持仓
        position1 = Mock()
        position1.amount = 1000
        position1.avg_cost = 12.50
        position1.market_value = 13000.0

        position2 = Mock()
        position2.amount = 500
        position2.avg_cost = 180.00
        position2.market_value = 95000.0

        mock_engine.context.portfolio.positions = {
            '000001.SZ': position1,
            '600519.SH': position2
        }
        mock_engine.context.portfolio.total_value = 608000.0

        generator = ReportGenerator(mock_engine, temp_dir)
        position_section = generator._generate_position_section()

        assert "最终持仓" in position_section
        assert "现金余额" in position_section
        assert "股票持仓" in position_section
        assert "000001.SZ" in position_section
        assert "600519.SH" in position_section
        assert "1000股" in position_section
        assert "500股" in position_section
        assert "12.50" in position_section
        assert "180.00" in position_section
        assert "股票总市值" in position_section
        assert "总资产" in position_section

    @pytest.mark.unit
    def test_generate_position_section_no_positions(self, mock_engine, temp_dir):
        """测试无持仓的持仓信息部分"""
        mock_engine.context.portfolio.positions = {}

        generator = ReportGenerator(mock_engine, temp_dir)
        position_section = generator._generate_position_section()

        assert "最终持仓" in position_section
        assert "现金余额" in position_section
        assert "无股票持仓" in position_section

    @pytest.mark.unit
    def test_generate_position_section_zero_amount_positions(self, mock_engine, temp_dir):
        """测试包含零持仓的持仓信息部分"""
        # 创建包含零持仓的模拟持仓
        position1 = Mock()
        position1.amount = 1000
        position1.avg_cost = 12.50
        position1.market_value = 13000.0

        position2 = Mock()
        position2.amount = 0  # 零持仓
        position2.avg_cost = 180.00
        position2.market_value = 0.0

        mock_engine.context.portfolio.positions = {
            '000001.SZ': position1,
            '600519.SH': position2
        }

        generator = ReportGenerator(mock_engine, temp_dir)
        position_section = generator._generate_position_section()

        assert "000001.SZ" in position_section
        assert "600519.SH" not in position_section  # 零持仓不应该显示

    @pytest.mark.unit
    def test_generate_footer(self, mock_engine, temp_dir):
        """测试生成报告尾部"""
        generator = ReportGenerator(mock_engine, temp_dir)

        footer = generator._generate_footer()

        assert "报告生成完成" in footer
        assert "simtradelab v1.0.0" in footer
        assert "=" * 100 in footer

    # ==================== 数据获取方法测试 ====================

    @pytest.mark.unit
    def test_get_portfolio_history_data(self, mock_engine, temp_dir):
        """测试获取投资组合历史数据"""
        generator = ReportGenerator(mock_engine, temp_dir)

        history_data = generator._get_portfolio_history_data()

        assert isinstance(history_data, list)
        assert len(history_data) == 2

        # 验证第一条记录
        first_record = history_data[0]
        assert 'datetime' in first_record
        assert 'total_value' in first_record
        assert 'cash' in first_record
        assert first_record['total_value'] == 1000000.0
        assert first_record['cash'] == 1000000.0

        # 验证最后一条记录
        last_record = history_data[-1]
        assert last_record['total_value'] == 1200000.0
        assert last_record['cash'] == 500000.0

    @pytest.mark.unit
    def test_get_portfolio_history_data_empty(self, mock_engine, temp_dir):
        """测试获取空投资组合历史数据"""
        mock_engine.portfolio_history = []

        generator = ReportGenerator(mock_engine, temp_dir)
        history_data = generator._get_portfolio_history_data()

        assert isinstance(history_data, list)
        assert len(history_data) == 0

    @pytest.mark.unit
    def test_get_portfolio_history_data_none(self, mock_engine, temp_dir):
        """测试获取None投资组合历史数据"""
        mock_engine.portfolio_history = None

        generator = ReportGenerator(mock_engine, temp_dir)
        history_data = generator._get_portfolio_history_data()

        assert isinstance(history_data, list)
        assert len(history_data) == 0

    @pytest.mark.unit
    def test_get_portfolio_summary_data(self, mock_engine, temp_dir):
        """测试获取投资组合摘要数据"""
        generator = ReportGenerator(mock_engine, temp_dir)

        summary_data = generator._get_portfolio_summary_data()

        assert isinstance(summary_data, dict)
        assert 'start_value' in summary_data
        assert 'end_value' in summary_data
        assert 'start_cash' in summary_data
        assert 'end_cash' in summary_data
        assert 'trading_days' in summary_data

        assert summary_data['start_value'] == 1000000.0
        assert summary_data['end_value'] == 1200000.0
        assert summary_data['start_cash'] == 1000000.0
        assert summary_data['end_cash'] == 500000.0
        assert summary_data['trading_days'] == 2

    @pytest.mark.unit
    def test_get_portfolio_summary_data_empty(self, mock_engine, temp_dir):
        """测试获取空投资组合摘要数据"""
        mock_engine.portfolio_history = []

        generator = ReportGenerator(mock_engine, temp_dir)
        summary_data = generator._get_portfolio_summary_data()

        assert isinstance(summary_data, dict)
        assert len(summary_data) == 0

    @pytest.mark.unit
    def test_get_final_positions_data(self, mock_engine, temp_dir):
        """测试获取最终持仓数据"""
        # 创建模拟持仓
        position1 = Mock()
        position1.amount = 1000
        position1.avg_cost = 12.50
        position1.market_value = 13000.0

        position2 = Mock()
        position2.amount = 0  # 零持仓
        position2.avg_cost = 180.00
        position2.market_value = 0.0

        mock_engine.context.portfolio.positions = {
            '000001.SZ': position1,
            '600519.SH': position2
        }

        generator = ReportGenerator(mock_engine, temp_dir)
        positions_data = generator._get_final_positions_data()

        assert isinstance(positions_data, dict)
        assert '000001.SZ' in positions_data
        assert '600519.SH' not in positions_data  # 零持仓不包含

        # 验证持仓数据结构
        pos_data = positions_data['000001.SZ']
        assert 'amount' in pos_data
        assert 'avg_cost' in pos_data
        assert 'market_value' in pos_data
        assert pos_data['amount'] == 1000.0
        assert pos_data['avg_cost'] == 12.50
        assert pos_data['market_value'] == 13000.0

    @pytest.mark.unit
    def test_get_final_positions_data_no_positions(self, mock_engine, temp_dir):
        """测试获取无持仓的最终持仓数据"""
        mock_engine.context.portfolio.positions = {}

        generator = ReportGenerator(mock_engine, temp_dir)
        positions_data = generator._get_final_positions_data()

        assert isinstance(positions_data, dict)
        assert len(positions_data) == 0

    @pytest.mark.unit
    def test_get_trade_summary_data(self, mock_engine, temp_dir):
        """测试获取交易摘要数据"""
        # 创建模拟交易记录
        mock_trade1 = Mock()
        mock_trade1.amount = 1000
        mock_trade1.price = 12.50

        mock_trade2 = Mock()
        mock_trade2.amount = -500
        mock_trade2.price = 180.00

        mock_trade3 = Mock()
        mock_trade3.amount = 800
        mock_trade3.price = 15.00

        mock_engine.context.blotter.get_all_trades.return_value = [mock_trade1, mock_trade2, mock_trade3]

        generator = ReportGenerator(mock_engine, temp_dir)
        trade_summary = generator._get_trade_summary_data()

        assert isinstance(trade_summary, dict)
        assert 'total_trades' in trade_summary
        assert 'buy_trades' in trade_summary
        assert 'sell_trades' in trade_summary
        assert 'total_volume' in trade_summary
        assert 'total_amount' in trade_summary

        assert trade_summary['total_trades'] == 3
        assert trade_summary['buy_trades'] == 2  # amount > 0
        assert trade_summary['sell_trades'] == 1  # amount < 0
        assert trade_summary['total_volume'] == 2300.0  # 1000 + 500 + 800
        assert trade_summary['total_amount'] == 114500.0  # 1000*12.5 + 500*180 + 800*15

    @pytest.mark.unit
    def test_get_trade_summary_data_no_trades(self, mock_engine, temp_dir):
        """测试获取无交易的交易摘要数据"""
        mock_engine.context.blotter.get_all_trades.return_value = []

        generator = ReportGenerator(mock_engine, temp_dir)
        trade_summary = generator._get_trade_summary_data()

        assert trade_summary['total_trades'] == 0
        assert trade_summary['buy_trades'] == 0
        assert trade_summary['sell_trades'] == 0
        assert trade_summary['total_volume'] == 0.0
        assert trade_summary['total_amount'] == 0.0

    # ==================== 摘要内容生成测试 ====================

    @pytest.mark.unit
    def test_generate_summary_content_excellent_rating(self, mock_engine, temp_dir):
        """测试生成优秀评级的摘要内容"""
        # 创建优秀的性能指标
        excellent_metrics = {
            'total_return': 0.25,      # > 10%
            'annualized_return': 0.20,
            'sharpe_ratio': 2.5,       # > 2.0
            'max_drawdown': 0.03,      # < 5%
            'win_rate': 0.70,          # > 60%
            'trading_days': 250,
            'total_trades': 50,
            'initial_value': 1000000.0,
            'final_value': 1250000.0
        }

        generator = ReportGenerator(mock_engine, temp_dir)
        summary_content = generator._generate_summary_content(excellent_metrics)

        assert "🌟 优秀" in summary_content
        assert "25.00%" in summary_content  # 总收益率
        assert "2.500" in summary_content   # 夏普比率
        assert "3.00%" in summary_content   # 最大回撤
        assert "70.0%" in summary_content   # 胜率

    @pytest.mark.unit
    def test_generate_summary_content_poor_rating(self, mock_engine, temp_dir):
        """测试生成较差评级的摘要内容"""
        # 创建较差的性能指标
        poor_metrics = {
            'total_return': -0.05,     # 负收益
            'annualized_return': -0.03,
            'sharpe_ratio': -0.5,      # 负夏普比率
            'max_drawdown': 0.25,      # > 10%
            'win_rate': 0.30,          # < 60%
            'trading_days': 250,
            'total_trades': 50,
            'initial_value': 1000000.0,
            'final_value': 950000.0
        }

        generator = ReportGenerator(mock_engine, temp_dir)
        summary_content = generator._generate_summary_content(poor_metrics)

        assert "❌ 较差" in summary_content
        assert "-5.00%" in summary_content  # 总收益率
        assert "-0.500" in summary_content  # 夏普比率
        assert "25.00%" in summary_content  # 最大回撤

    @pytest.mark.unit
    def test_generate_summary_content_good_rating(self, mock_engine, temp_dir):
        """测试生成良好评级的摘要内容"""
        # 创建良好的性能指标
        good_metrics = {
            'total_return': 0.08,      # 8%
            'annualized_return': 0.06,
            'sharpe_ratio': 1.5,       # > 1.0
            'max_drawdown': 0.08,      # < 10%
            'win_rate': 0.55,          # 55%
            'trading_days': 250,
            'total_trades': 50,
            'initial_value': 1000000.0,
            'final_value': 1080000.0
        }

        generator = ReportGenerator(mock_engine, temp_dir)
        summary_content = generator._generate_summary_content(good_metrics)

        assert "👍 良好" in summary_content
        assert "8.00%" in summary_content   # 总收益率
        assert "1.500" in summary_content   # 夏普比率


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
