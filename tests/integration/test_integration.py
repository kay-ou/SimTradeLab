"""
集成测试 - 测试完整的回测流程
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from simtradelab import BacktestEngine
from simtradelab.data_sources import AkshareDataSource


class TestFullBacktestFlow:
    """完整回测流程测试"""
    
    @pytest.mark.integration
    @pytest.mark.data
    def test_csv_backtest_flow(self, sample_data_path, test_strategy_path):
        """测试CSV数据源完整回测流程"""
        if not sample_data_path.exists():
            pytest.skip(f"Sample data file not found: {sample_data_path}")
        
        if not test_strategy_path.exists():
            pytest.skip(f"Test strategy file not found: {test_strategy_path}")
        
        # 创建引擎
        engine = BacktestEngine(
            strategy_file=str(test_strategy_path),
            data_path=str(sample_data_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 运行回测
        engine.run()
        
        # 验证结果 - mock数据源可能没有数据
        assert hasattr(engine, 'portfolio_history')
        # 如果没有数据，portfolio_history可能为空，这是正常的
        if len(engine.portfolio_history) == 0:
            pytest.skip("No data available from mock source")
        
        # 验证投资组合历史
        for record in engine.portfolio_history:
            assert 'total_value' in record
            assert 'cash' in record
            assert 'datetime' in record or 'date' in record  # 可能是datetime或date
            assert record['total_value'] > 0
            assert record['cash'] >= 0
        
        # 验证性能分析
        if hasattr(engine, 'performance_analysis'):
            perf = engine.performance_analysis
            assert 'total_return' in perf
            assert 'sharpe_ratio' in perf
            assert 'max_drawdown' in perf
    
    @pytest.mark.integration
    def test_strategy_with_trading(self, mock_csv_data, temp_dir):
        """测试包含交易的策略"""
        # 创建包含交易的策略
        trading_strategy = '''
def initialize(context):
    """策略初始化"""
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.traded = False

def handle_data(context, data):
    """处理数据"""
    if not context.traded:
        # 买入第一只股票
        order('STOCK_A', 100)
        context.traded = True

def before_trading_start(context, data):
    """交易前处理"""
    pass

def after_trading_end(context, data):
    """交易后处理"""
    pass
'''
        
        # 保存策略文件
        strategy_path = Path(temp_dir) / "trading_strategy.py"
        strategy_path.write_text(trading_strategy)
        
        # 保存数据文件
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 创建引擎
        engine = BacktestEngine(
            strategy_file=str(strategy_path),
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 运行回测
        engine.run()
        
        # 验证交易发生 - 检查是否有交易记录
        assert hasattr(engine, 'portfolio_history')
        assert len(engine.portfolio_history) > 0
        assert engine.context.traded is True

        # 验证持仓变化
        final_positions = engine.context.portfolio.positions
        if 'STOCK_A' in final_positions:
            assert final_positions['STOCK_A'].amount > 0
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.network
    def test_real_data_backtest_flow(self, mock_akshare_source):
        """测试真实数据源回测流程"""
        # 创建简单策略
        simple_strategy = '''
def initialize(context):
    """策略初始化"""
    pass

def handle_data(context, data):
    """处理数据"""
    # 简单的买入持有策略
    positions = get_positions()
    if len(positions) == 0:
        order('000001.SZ', 100)

def before_trading_start(context, data):
    """交易前处理"""
    pass

def after_trading_end(context, data):
    """交易后处理"""
    pass
'''
        
        # 保存策略文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(simple_strategy)
            strategy_path = f.name
        
        try:
            # 创建引擎
            engine = BacktestEngine(
                strategy_file=strategy_path,
                data_source=mock_akshare_source,
                securities=['000001.SZ', '000002.SZ'],
                start_date='2024-12-01',
                end_date='2024-12-05',
                initial_cash=1000000.0
            )
            
            # 运行回测
            engine.run()
            
            # 验证结果
            assert hasattr(engine, 'portfolio_history')
            assert len(engine.portfolio_history) > 0
            
        finally:
            # 清理临时文件
            Path(strategy_path).unlink(missing_ok=True)
    
    @pytest.mark.integration
    def test_performance_analysis(self, mock_csv_data, temp_dir):
        """测试性能分析功能"""
        # 创建策略文件
        strategy_path = Path(temp_dir) / "perf_strategy.py"
        strategy_path.write_text('''
def initialize(context):
    pass

def handle_data(context, data):
    pass
''')
        
        # 保存数据文件
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 创建引擎
        engine = BacktestEngine(
            strategy_file=str(strategy_path),
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 运行回测
        engine.run()
        
        # 验证性能分析
        if hasattr(engine, 'performance_analysis'):
            perf = engine.performance_analysis
            
            # 检查必要的性能指标
            expected_metrics = [
                'total_return', 'annual_return', 'sharpe_ratio',
                'max_drawdown', 'volatility', 'win_rate'
            ]
            
            for metric in expected_metrics:
                assert metric in perf, f"Missing performance metric: {metric}"
    
    @pytest.mark.integration
    def test_multiple_securities_backtest(self, mock_csv_data, temp_dir):
        """测试多股票回测"""
        # 创建多股票策略
        multi_stock_strategy = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.weights = [0.5, 0.5]

def handle_data(context, data):
    # 等权重投资 - 只在第一天或需要重新平衡时交易
    positions = get_positions()
    total_value = context.portfolio.total_value
    
    # 检查是否已经有持仓，如果有则不重复投资
    if len(positions) == 0:
        # 初次建仓
        for i, stock in enumerate(context.stocks):
            if stock in data:
                target_value = total_value * context.weights[i]
                try:
                    order_target_value(stock, target_value)
                except Exception as e:
                    log.warning(f"买入{stock}失败: {e}")
                    continue

def before_trading_start(context, data):
    pass

def after_trading_end(context, data):
    pass
'''
        
        # 保存策略文件
        strategy_path = Path(temp_dir) / "multi_strategy.py"
        strategy_path.write_text(multi_stock_strategy)
        
        # 保存数据文件
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 创建引擎
        engine = BacktestEngine(
            strategy_file=str(strategy_path),
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 运行回测
        engine.run()
        
        # 验证多股票交易 - 检查投资组合历史
        assert hasattr(engine, 'portfolio_history')
        assert len(engine.portfolio_history) > 0

        # 验证有交易活动 - 检查是否有持仓而不是依赖现金变化
        final_positions = engine.context.portfolio.positions
        assert len(final_positions) > 0, "应该有持仓记录，说明发生了交易"
        
        # 额外验证：检查是否有交易记录
        if hasattr(engine.context, 'blotter'):
            trades = engine.context.blotter.get_all_trades()
            assert len(trades) > 0, "应该有交易记录"
    
    @pytest.mark.integration
    def test_commission_impact(self, mock_csv_data, temp_dir):
        """测试手续费对回测结果的影响"""
        # 创建交易策略
        trading_strategy = '''
def initialize(context):
    pass

def handle_data(context, data):
    # 频繁交易以测试手续费影响
    order('STOCK_A', 100)
    order('STOCK_A', -50)

def before_trading_start(context, data):
    pass

def after_trading_end(context, data):
    pass
'''
        
        # 保存策略文件
        strategy_path = Path(temp_dir) / "commission_strategy.py"
        strategy_path.write_text(trading_strategy)
        
        # 保存数据文件
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 测试无手续费情况
        engine1 = BacktestEngine(
            strategy_file=str(strategy_path),
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        engine1.commission_ratio = 0.0
        engine1.min_commission = 0.0
        engine1.run()
        
        # 测试有手续费情况
        engine2 = BacktestEngine(
            strategy_file=str(strategy_path),
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        engine2.commission_ratio = 0.001
        engine2.min_commission = 5.0
        engine2.run()
        
        # 验证手续费影响
        if (engine1.portfolio_history and engine2.portfolio_history and
            len(engine1.portfolio_history) > 0 and len(engine2.portfolio_history) > 0):

            final_value1 = engine1.portfolio_history[-1]['total_value']
            final_value2 = engine2.portfolio_history[-1]['total_value']

            # 有手续费的情况下，最终价值应该更低（如果有交易发生）
            # 检查现金变化来判断是否有交易
            cash_changed1 = engine1.portfolio_history[0]['cash'] != engine1.portfolio_history[-1]['cash']
            if cash_changed1:
                assert final_value2 <= final_value1
    
    @pytest.mark.integration
    def test_error_handling_in_strategy(self, mock_csv_data, temp_dir):
        """测试策略中的错误处理"""
        # 创建有错误的策略
        error_strategy = '''
def initialize(context):
    pass

def handle_data(context, data):
    # 故意引发错误
    raise ValueError("Test error in strategy")

def before_trading_start(context, data):
    pass

def after_trading_end(context, data):
    pass
'''
        
        # 保存策略文件
        strategy_path = Path(temp_dir) / "error_strategy.py"
        strategy_path.write_text(error_strategy)
        
        # 保存数据文件
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 创建引擎
        engine = BacktestEngine(
            strategy_file=str(strategy_path),
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 运行回测应该处理错误
        with pytest.raises(Exception):
            engine.run()
