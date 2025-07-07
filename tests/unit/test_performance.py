#!/usr/bin/env python3
"""
性能分析模块测试 - 测试性能分析功能
"""

import pytest
import tempfile
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from simtradelab.performance import (
    calculate_portfolio_returns, calculate_performance_metrics,
    print_performance_report, get_performance_summary,
    generate_report_file, _generate_report_content,
    _set_current_engine, get_performance_summary_standalone
)


class TestPerformanceFunctions:
    """性能计算函数测试"""
    
    @pytest.fixture
    def sample_engine(self):
        """创建示例引擎"""
        engine = Mock()
        # 创建投资组合历史数据
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        portfolio_history = []
        
        for i, date in enumerate(dates):
            portfolio_history.append({
                'datetime': date,
                'total_value': 100000 + i * 100 + np.random.normal(0, 50),
                'cash': 50000 - i * 50,
                'market_value': 50000 + i * 150,
                'daily_pnl': np.random.normal(100, 200)
            })
        
        engine.portfolio_history = portfolio_history
        
        # 配置必要的属性
        engine.initial_cash = 100000
        
        # 配置context和portfolio
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.total_value = 110000  # 简单的最终值
        engine.context.blotter = Mock()
        engine.context.blotter.get_all_trades.return_value = []  # 空交易列表
        
        return engine
    
    def test_calculate_portfolio_returns(self, sample_engine):
        """测试计算投资组合收益率"""
        returns = calculate_portfolio_returns(sample_engine)
        
        assert isinstance(returns, pd.Series)
        assert len(returns) == 9  # N-1 returns for N values
        assert not returns.isnull().any()
    
    def test_calculate_portfolio_returns_empty(self):
        """测试空投资组合历史"""
        engine = Mock()
        engine.portfolio_history = []
        
        returns = calculate_portfolio_returns(engine)
        assert isinstance(returns, pd.Series)
        assert len(returns) == 0
    
    def test_calculate_portfolio_returns_insufficient_data(self):
        """测试数据不足的情况"""
        engine = Mock()
        engine.portfolio_history = [{'datetime': '2023-01-01', 'total_value': 100000}]
        
        returns = calculate_portfolio_returns(engine)
        assert isinstance(returns, pd.Series)
        assert len(returns) == 0
    
    def test_calculate_performance_metrics(self, sample_engine):
        """测试计算性能指标"""
        metrics = calculate_performance_metrics(sample_engine)
        
        assert isinstance(metrics, dict)
        # 检查必要的性能指标（使用实际的字段名）
        expected_metrics = [
            'total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown',
            'volatility', 'win_rate'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
    
    def test_calculate_performance_metrics_with_benchmark(self, sample_engine):
        """测试带基准的性能指标计算"""
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.02, 9))
        
        metrics = calculate_performance_metrics(sample_engine, benchmark_returns)
        
        assert isinstance(metrics, dict)
        # 应该包含基准相关指标
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        # 如果有基准数据，可能会有alpha和beta
        if 'alpha' in metrics:
            assert 'beta' in metrics
    
    def test_calculate_performance_metrics_empty_engine(self):
        """测试空引擎的性能指标计算"""
        engine = Mock()
        engine.portfolio_history = []
        
        metrics = calculate_performance_metrics(engine)
        
        assert isinstance(metrics, dict)
        # 应该返回空字典，因为没有足够的数据
        assert len(metrics) == 0
    
    def test_calculate_performance_metrics_constant_values(self):
        """测试常数值的性能指标计算"""
        engine = Mock()
        # 创建常数值的投资组合历史
        dates = pd.date_range('2023-01-01', periods=5, freq='D')
        portfolio_history = []
        
        for date in dates:
            portfolio_history.append({
                'datetime': date,
                'total_value': 100000,  # 常数值
                'cash': 50000,
                'market_value': 50000
            })
        
        engine.portfolio_history = portfolio_history
        engine.initial_cash = 100000
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.total_value = 100000
        engine.context.blotter = Mock()
        engine.context.blotter.get_all_trades.return_value = []
        
        metrics = calculate_performance_metrics(engine)
        
        assert isinstance(metrics, dict)
        assert metrics['total_return'] == 0.0  # 无变化
        assert metrics['volatility'] == 0.0   # 无波动


class TestPerformanceReporting:
    """性能报告功能测试"""
    
    @pytest.fixture
    def sample_engine(self):
        """创建示例引擎"""
        engine = Mock()
        # 创建投资组合历史数据
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        portfolio_history = []
        
        for i, date in enumerate(dates):
            portfolio_history.append({
                'datetime': date,
                'total_value': 100000 + i * 1000,
                'cash': 50000 - i * 100,
                'market_value': 50000 + i * 1100,
            })
        
        engine.portfolio_history = portfolio_history
        engine.initial_cash = 100000
        engine.start_date = dates[0]
        engine.end_date = dates[-1]
        engine.frequency = '1d'
        engine.strategy_file = '/test/strategy.py'
        
        # 配置context和portfolio
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.total_value = 109000
        engine.context.portfolio.cash = 45100
        engine.context.portfolio.positions = {
            'STOCK_A': Mock(amount=100, market_value=30000),
            'STOCK_B': Mock(amount=50, market_value=33900)
        }
        engine.context.blotter = Mock()
        engine.context.blotter.get_all_trades.return_value = [
            Mock(security='STOCK_A', amount=100, price=10.0),
            Mock(security='STOCK_B', amount=50, price=20.0)
        ]
        
        return engine
    
    def test_print_performance_report(self, sample_engine, capsys):
        """测试打印性能报告"""
        print_performance_report(sample_engine)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 检查报告是否包含关键信息
        assert "策略性能分析报告" in output
        assert "收益指标" in output
        assert "风险指标" in output
        assert "交易统计" in output
        assert "总收益率" in output
        assert "年化收益率" in output
        assert "夏普比率" in output
        assert "最大回撤" in output
    
    def test_print_performance_report_with_benchmark(self, sample_engine, capsys):
        """测试带基准的打印性能报告"""
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.02, 9))
        
        print_performance_report(sample_engine, benchmark_returns)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 检查报告是否包含基准信息
        assert "策略性能分析报告" in output
    
    def test_print_performance_report_empty_metrics(self, capsys):
        """测试空指标时的打印报告"""
        engine = Mock()
        engine.portfolio_history = []
        
        print_performance_report(engine)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # 应该没有报告输出
        assert "策略性能分析报告" not in output
    
    def test_get_performance_summary(self, sample_engine):
        """测试获取性能摘要"""
        summary = get_performance_summary(sample_engine)
        
        assert isinstance(summary, dict)
        
        # 检查摘要包含的关键指标
        key_metrics = ['total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        
        for metric in key_metrics:
            assert metric in summary
            assert isinstance(summary[metric], (int, float, np.number))
    
    def test_get_performance_summary_with_benchmark(self, sample_engine):
        """测试带基准的获取性能摘要"""
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.02, 9))
        
        summary = get_performance_summary(sample_engine, benchmark_returns)
        
        assert isinstance(summary, dict)
        
        # 应该包含基本指标
        assert 'total_return' in summary
        assert 'sharpe_ratio' in summary
    
    def test_get_performance_summary_empty_engine(self):
        """测试空引擎的性能摘要"""
        engine = Mock()
        engine.portfolio_history = []
        
        summary = get_performance_summary(engine)
        
        assert isinstance(summary, dict)
        assert all(v == 0 for v in summary.values())  # 应该返回空字典
    
    def test_generate_report_file(self, sample_engine):
        """测试生成报告文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = generate_report_file(sample_engine, output_dir=temp_dir)
            
            assert report_path is not None
            assert Path(report_path).exists()
            assert report_path.endswith('.txt')
            
            # 检查报告文件内容
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "simtradelab 策略回测报告" in content
            assert "基本信息" in content
            assert "收益指标" in content
            assert "风险指标" in content
            assert "交易统计" in content
    
    def test_generate_report_file_with_benchmark(self, sample_engine):
        """测试带基准的生成报告文件"""
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.02, 9))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = generate_report_file(sample_engine, benchmark_returns, output_dir=temp_dir)
            
            assert report_path is not None
            assert Path(report_path).exists()
            
            # 检查报告文件内容
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "simtradelab 策略回测报告" in content
    
    def test_generate_report_file_error_case(self):
        """测试生成报告文件错误情况"""
        engine = Mock()
        engine.portfolio_history = []
        engine.strategy_file = "mock_strategy.py"
        engine.start_date = None
        engine.end_date = None
        engine.portfolio_history = []  # 空数据

        result = generate_report_file(engine)
        assert result is None  # 应该返回 None 表示失败
        
    
    def test_generate_report_content(self, sample_engine):
        """测试生成报告内容"""
        metrics = calculate_performance_metrics(sample_engine)
        content = _generate_report_content(sample_engine, metrics)
        
        assert isinstance(content, str)
        assert len(content) > 0
        
        # 检查内容包含关键部分
        assert "simtradelab 策略回测报告" in content
        assert "基本信息" in content
        assert "收益指标" in content
        assert "风险指标" in content
        assert "交易统计" in content
        assert "最终持仓" in content
    
    def test_generate_report_content_with_benchmark(self, sample_engine):
        """测试带基准的生成报告内容"""
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.02, 9))
        metrics = calculate_performance_metrics(sample_engine, benchmark_returns)
        content = _generate_report_content(sample_engine, metrics, benchmark_returns)
        
        assert isinstance(content, str)
        assert len(content) > 0
        
        # 应该包含基本报告内容
        assert "simtradelab 策略回测报告" in content
    
    def test_set_current_engine_and_standalone_summary(self, sample_engine):
        """测试设置当前引擎和独立摘要"""
        # 设置当前引擎
        _set_current_engine(sample_engine)
        
        # 测试独立摘要函数
        summary = get_performance_summary_standalone()
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        
        # 应该包含关键指标
        key_metrics = ['total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
        for metric in key_metrics:
            assert metric in summary
    
    def test_standalone_summary_no_engine(self):
        """测试无引擎时的独立摘要"""
        # 清空当前引擎
        _set_current_engine(None)
        
        summary = get_performance_summary_standalone()
        
        # 应该返回空字典
        assert isinstance(summary, dict)
        assert len(summary) == 0
    
    def test_standalone_summary_with_benchmark(self, sample_engine):
        """测试带基准的独立摘要"""
        _set_current_engine(sample_engine)
        
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.02, 9))
        summary = get_performance_summary_standalone(benchmark_returns)
        
        assert isinstance(summary, dict)
        assert len(summary) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])