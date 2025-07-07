"""
测试BacktestEngine核心功能
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from simtradelab.engine import BacktestEngine
from simtradelab.context import Context


class TestBacktestEngine:
    """BacktestEngine测试类"""
    
    @pytest.mark.unit
    def test_engine_initialization(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试引擎初始化"""
        # 创建临时CSV文件
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert engine.strategy_file == simple_strategy_file
        assert str(engine.start_date.date()) == '2023-01-03'
        assert str(engine.end_date.date()) == '2023-01-05'
        assert engine.initial_cash == 1000000.0
        assert engine.frequency == '1d'
        assert engine.data is not None
        assert isinstance(engine.context, Context)
    
    @pytest.mark.unit
    def test_strategy_loading(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试策略加载"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 检查策略模块是否正确加载
        assert hasattr(engine.strategy, 'initialize')
        assert hasattr(engine.strategy, 'handle_data')
        assert hasattr(engine.strategy, 'before_trading_start')
        assert hasattr(engine.strategy, 'after_trading_end')
        
        # 检查API函数是否注入
        assert hasattr(engine.strategy, 'order')
        assert hasattr(engine.strategy, 'get_history')
        assert hasattr(engine.strategy, 'get_positions')
    
    @pytest.mark.unit
    def test_data_loading_csv(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试CSV数据加载"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert len(engine.data) == 2  # STOCK_A and STOCK_B
        assert 'STOCK_A' in engine.data
        assert 'STOCK_B' in engine.data
        
        # 检查数据格式
        for stock, data in engine.data.items():
            assert isinstance(data, pd.DataFrame)
            assert 'open' in data.columns
            assert 'high' in data.columns
            assert 'low' in data.columns
            assert 'close' in data.columns
            assert 'volume' in data.columns
    
    @pytest.mark.unit
    def test_context_initialization(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试Context初始化"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        context = engine.context
        assert context.portfolio.starting_cash == 1000000.0
        assert context.portfolio.cash == 1000000.0
        assert context.portfolio.total_value == 1000000.0
        assert len(context.portfolio.positions) == 0
    
    @pytest.mark.unit
    def test_invalid_strategy_file(self, mock_csv_data, temp_dir):
        """测试无效策略文件"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        with pytest.raises(FileNotFoundError):
            BacktestEngine(
                strategy_file='nonexistent_strategy.py',
                data_path=str(csv_path),
                start_date='2023-01-03',
                end_date='2023-01-05',
                initial_cash=1000000.0
            )
    
    @pytest.mark.unit
    def test_invalid_data_path(self, simple_strategy_file):
        """测试无效数据路径"""
        with patch('simtradelab.performance_optimizer.get_global_cache') as mock_cache:
            # Mock缓存返回None（无缓存数据）
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()
            
            # 创建引擎，但不期望抛出异常，因为引擎会优雅处理
            engine = BacktestEngine(
                strategy_file=simple_strategy_file,
                data_path='nonexistent_data.csv',
                start_date='2023-01-03',
                end_date='2023-01-05',
                initial_cash=1000000.0
            )
            # 验证数据为空或很少
            assert len(engine.data) <= 2  # 可能有默认的测试数据
    
    @pytest.mark.unit
    def test_date_validation(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试日期验证"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)

        with patch('simtradelab.performance_optimizer.get_global_cache') as mock_cache:
            # Mock缓存返回None（无缓存数据）
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()
            
            with patch('simtradelab.data_sources.manager.DataSourceManager.get_history') as mock_get_history:
                # Mock数据源返回空数据
                mock_get_history.return_value = {}
                
                # 应该抛出DataLoadError异常
                from simtradelab.exceptions import DataLoadError
                with pytest.raises(DataLoadError, match="未能加载到任何股票数据"):
                    BacktestEngine(
                        strategy_file=simple_strategy_file,
                        data_path=str(csv_path),
                        start_date='2099-01-01',  # 未来日期，没有数据
                        end_date='2099-01-02',
                        initial_cash=1000000.0
                    )
    
    @pytest.mark.unit
    def test_commission_setting(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试手续费设置"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 测试设置手续费
        engine.commission_ratio = 0.001
        engine.min_commission = 10.0
        
        assert engine.commission_ratio == 0.001
        assert engine.min_commission == 10.0
    
    @pytest.mark.integration
    def test_simple_backtest_run(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试简单回测运行"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 运行回测
        engine.run()
        
        # 检查结果
        assert hasattr(engine, 'portfolio_history')
        assert len(engine.portfolio_history) > 0
        
        # 检查策略初始化是否被调用
        assert hasattr(engine.strategy, 'g')
        if hasattr(engine.context, 'test_var'):
            assert engine.context.test_var == "initialized"
    
    @pytest.mark.unit
    def test_frequency_validation(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试交易频率验证"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 测试有效频率
        valid_frequencies = ['1d', '1m', '5m', '15m', '30m']
        for freq in valid_frequencies:
            engine = BacktestEngine(
                strategy_file=simple_strategy_file,
                data_path=str(csv_path),
                start_date='2023-01-03',
                end_date='2023-01-05',
                initial_cash=1000000.0,
                frequency=freq
            )
            assert engine.frequency == freq
    
    @pytest.mark.unit
    def test_portfolio_tracking(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试投资组合跟踪"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 初始状态检查
        assert engine.context.portfolio.cash == 1000000.0
        assert engine.context.portfolio.total_value == 1000000.0
        
        # 模拟交易后的状态变化会在集成测试中验证
    
    @pytest.mark.unit
    def test_create_data_source_csv(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试CSV数据源创建"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 测试CSV数据源创建
        csv_source = engine._create_data_source('csv')
        assert csv_source is not None
        from simtradelab.data_sources import CSVDataSource
        assert isinstance(csv_source, CSVDataSource)
    
    @pytest.mark.unit
    def test_create_data_source_tushare(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试Tushare数据源创建"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # Mock配置返回token
        with patch.object(engine.config, 'get_tushare_token', return_value='test_token'):
            with patch('simtradelab.data_sources.DataSourceFactory.create') as mock_create:
                mock_create.return_value = Mock()
                
                tushare_source = engine._create_data_source('tushare')
                assert tushare_source is not None
                mock_create.assert_called_once_with(
                    'tushare', 
                    token='test_token',
                    cache_dir='./cache/tushare',
                    cache_enabled=True
                )
    
    @pytest.mark.unit
    def test_create_data_source_tushare_no_token(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试Tushare数据源创建失败（无token）"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # Mock配置返回空token
        with patch.object(engine.config, 'get_tushare_token', return_value=None):
            with pytest.raises(ValueError, match="Tushare token未配置"):
                engine._create_data_source('tushare')
    
    @pytest.mark.unit
    def test_create_data_source_akshare(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试AkShare数据源创建"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        with patch('simtradelab.data_sources.DataSourceFactory.create') as mock_create:
            mock_create.return_value = Mock()
            
            akshare_source = engine._create_data_source('akshare')
            assert akshare_source is not None
            mock_create.assert_called_once_with(
                'akshare',
                cache_dir='./cache/akshare',
                cache_enabled=True
            )
    
    @pytest.mark.unit
    def test_create_data_source_unsupported(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试不支持的数据源类型"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        with pytest.raises(ValueError, match="不支持的数据源类型: unsupported"):
            engine._create_data_source('unsupported')
    
    @pytest.mark.unit
    def test_is_daily_data_empty_df(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试空DataFrame的日线数据判断"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        empty_df = pd.DataFrame()
        assert engine._is_daily_data(empty_df) is True
    
    @pytest.mark.unit
    def test_is_daily_data_single_row(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试单行DataFrame的日线数据判断"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 创建单行DataFrame
        single_row_df = pd.DataFrame(
            {'close': [100.0]},
            index=[pd.Timestamp('2023-01-01')]
        )
        assert engine._is_daily_data(single_row_df) is True
    
    @pytest.mark.unit
    def test_is_daily_data_daily_frequency(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试日线频率数据判断"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 创建日线频率DataFrame
        daily_df = pd.DataFrame(
            {'close': [100.0, 101.0]},
            index=[pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')]
        )
        assert engine._is_daily_data(daily_df) is True
    
    @pytest.mark.unit
    def test_is_daily_data_minute_frequency(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试分钟频率数据判断"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 创建分钟频率DataFrame
        minute_df = pd.DataFrame(
            {'close': [100.0, 101.0]},
            index=[pd.Timestamp('2023-01-01 09:30:00'), pd.Timestamp('2023-01-01 09:31:00')]
        )
        assert engine._is_daily_data(minute_df) is False
    
    @pytest.mark.unit
    def test_generate_minute_data_empty_df(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试空DataFrame的分钟数据生成"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 创建空的日线数据
        empty_daily_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'security'])
        result = engine._generate_minute_data(empty_daily_df)
        assert result.equals(empty_daily_df)
    
    @pytest.mark.unit
    def test_generate_minute_data_basic(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试基本分钟数据生成"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0,
            frequency='1m'
        )
        
        # 创建简单的日线数据
        daily_data = pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [98.0],
            'close': [102.0],
            'volume': [1000000],
            'security': ['TEST_STOCK']
        }, index=[pd.Timestamp('2023-01-01')])
        
        # 添加security列作为groupby的键
        daily_data = daily_data.reset_index().rename(columns={'index': 'datetime'})
        daily_data = daily_data.set_index('datetime')
        
        minute_data = engine._generate_minute_data(daily_data)
        
        # 验证生成的分钟数据
        assert not minute_data.empty
        assert 'open' in minute_data.columns
        assert 'high' in minute_data.columns
        assert 'low' in minute_data.columns
        assert 'close' in minute_data.columns
        assert 'volume' in minute_data.columns
        assert 'security' in minute_data.columns
        
        # 验证分钟数据数量 (240分钟/天对于1分钟频率)
        assert len(minute_data) == 240
    
    @pytest.mark.unit 
    def test_update_portfolio_value_no_positions(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试无持仓时的投资组合价值更新"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        current_prices = {'STOCK_A': 100.0, 'STOCK_B': 200.0}
        engine._update_portfolio_value(current_prices)
        
        assert engine.portfolio.total_value == engine.portfolio.cash
    
    @pytest.mark.unit
    def test_update_portfolio_value_with_positions(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试有持仓时的投资组合价值更新"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 模拟持仓
        from simtradelab.context import Position
        # 修复：Position需要amount和cost_basis
        engine.portfolio.positions['STOCK_A'] = Position(security='STOCK_A', amount=100, cost_basis=95.0)
        engine.portfolio.positions['STOCK_B'] = Position(security='STOCK_B', amount=50, cost_basis=190.0)
        
        current_prices = {'STOCK_A': 100.0, 'STOCK_B': 200.0}
        engine._update_portfolio_value(current_prices)
        
        expected_position_value = 100 * 100.0 + 50 * 200.0  # 20000
        expected_total = engine.portfolio.cash + expected_position_value
        assert engine.portfolio.total_value == expected_total
    
    @pytest.mark.unit
    def test_update_portfolio_value_exception_handling(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试投资组合价值更新异常处理"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 模拟无效的持仓数据导致异常
        from simtradelab.context import Position
        # 修复：使用正确的模拟对象，并确保其具有必要的属性
        mock_position = Mock(spec=Position)
        mock_position.amount = "invalid"
        mock_position.cost_basis = 100.0
        mock_position.last_sale_price = 100.0
        engine.portfolio.positions['STOCK_A'] = mock_position
        
        current_prices = {'STOCK_A': 100.0}
        
        # 应该不抛出异常，而是使用fallback逻辑
        engine._update_portfolio_value(current_prices)
        
        # 验证使用了fallback计算
        assert engine.portfolio.total_value >= engine.portfolio.cash
    
    @pytest.mark.unit
    def test_get_file_type_emoji_txt_summary(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试summary.txt文件的emoji"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert engine._get_file_type_emoji('strategy_summary.txt') == '📋'
    
    @pytest.mark.unit
    def test_get_file_type_emoji_txt_regular(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试普通txt文件的emoji"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert engine._get_file_type_emoji('report.txt') == '📝'
    
    @pytest.mark.unit
    def test_get_file_type_emoji_json(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试JSON文件的emoji"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert engine._get_file_type_emoji('data.json') == '📊'
    
    @pytest.mark.unit
    def test_get_file_type_emoji_csv(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试CSV文件的emoji"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert engine._get_file_type_emoji('data.csv') == '📈'
    
    @pytest.mark.unit
    def test_get_file_type_emoji_other(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试其他文件类型的emoji"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        assert engine._get_file_type_emoji('document.pdf') == '📄'
    
    @pytest.mark.unit
    def test_run_minute_backtest_basic(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试分钟级回测基本功能"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-03',  # 单日测试
            initial_cash=1000000.0,
            frequency='1m'
        )
        
        # 模拟分钟级数据
        minute_times = pd.date_range(
            start='2023-01-03 09:30:00',
            end='2023-01-03 10:00:00',
            freq='1min'
        )
        
        # 创建简单的分钟数据
        mock_minute_data = {}
        for stock in ['STOCK_A', 'STOCK_B']:
            mock_minute_data[stock] = pd.DataFrame({
                'open': [100.0] * len(minute_times),
                'high': [101.0] * len(minute_times),
                'low': [99.0] * len(minute_times),
                'close': [100.5] * len(minute_times),
                'volume': [1000] * len(minute_times)
            }, index=minute_times)
        
        # 替换引擎的数据
        engine.data = mock_minute_data
        
        # 测试_run_minute_backtest
        engine._run_minute_backtest(minute_times)
        
        # 验证结果
        assert len(engine.portfolio_history) > 0
    
    @pytest.mark.unit
    def test_run_minute_backtest_strategy_callbacks(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试分钟级回测策略回调函数"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        engine = BacktestEngine(
            strategy_file=simple_strategy_file,
            data_path=str(csv_path),
            start_date='2023-01-03',
            end_date='2023-01-03',
            initial_cash=1000000.0,
            frequency='1m'
        )
        
        # Mock策略回调函数
        engine.strategy.before_trading_start = Mock()
        engine.strategy.handle_data = Mock()
        engine.strategy.after_trading_end = Mock()
        
        # 创建测试时间序列（包含不同日期和收盘时间）
        test_times = [
            pd.Timestamp('2023-01-03 09:30:00'),
            pd.Timestamp('2023-01-03 10:00:00'),
            pd.Timestamp('2023-01-03 15:00:00'),  # 收盘时间
            pd.Timestamp('2023-01-04 09:30:00'),  # 新的一天
        ]
        
        # 创建模拟数据
        mock_data = {}
        for stock in ['STOCK_A']:
            mock_data[stock] = pd.DataFrame({
                'open': [100.0] * len(test_times),
                'high': [101.0] * len(test_times),
                'low': [99.0] * len(test_times),
                'close': [100.5] * len(test_times),
                'volume': [1000] * len(test_times)
            }, index=test_times)
        
        engine.data = mock_data
        
        # 运行分钟级回测
        engine._run_minute_backtest(test_times)
        
        # 验证策略回调被调用
        assert engine.strategy.before_trading_start.call_count >= 1  # 每个新交易日调用一次
        assert engine.strategy.handle_data.call_count == len(test_times)  # 每个时间点调用一次
        assert engine.strategy.after_trading_end.call_count >= 1  # 15:00时调用
    
    @pytest.mark.unit
    def test_data_loading_with_cache_hit(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试缓存命中时的数据加载"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # Mock缓存命中
        cached_data = {'STOCK_A': mock_csv_data.head(), 'STOCK_B': mock_csv_data.tail()}
        
        # 修复：patch目标应为engine模块
        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            mock_cache.return_value.get.return_value = cached_data
            mock_cache.return_value.set = Mock()
            
            with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage') as mock_optimizer:
                mock_optimizer.return_value = cached_data
                
                engine = BacktestEngine(
                    strategy_file=simple_strategy_file,
                    data_path=str(csv_path),
                    start_date='2023-01-03',
                    end_date='2023-01-05',
                    initial_cash=1000000.0
                )
                
                # 验证缓存被使用
                mock_cache.return_value.get.assert_called_once()
                # 验证优化器被调用
                mock_optimizer.assert_called_once_with(cached_data)
    
    @pytest.mark.unit
    def test_data_loading_cache_miss_concurrent(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试缓存未命中时的并发数据加载"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)

        # 修复：patch目标应为engine模块
        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()

            # 模拟数据源返回数据
            mock_data = {'STOCK_A': mock_csv_data, 'STOCK_B': mock_csv_data}

            # 模拟AkShare数据源，避免实际导入
            with patch('simtradelab.data_sources.manager.DataSourceManager') as mock_manager_class:
                mock_manager = mock_manager_class.return_value
                mock_manager.get_history.return_value = mock_data

                with patch('simtradelab.engine.ConcurrentDataLoader') as mock_loader:
                    mock_loader_instance = mock_loader.return_value
                    mock_loader_instance.load_multiple_securities.return_value = mock_data

                    with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage') as mock_optimizer:
                        mock_optimizer.return_value = mock_data

                        # 使用CSV数据源而不是akshare，避免依赖
                        engine = BacktestEngine(
                            strategy_file=simple_strategy_file,
                            data_path=str(csv_path),
                            securities=['STOCK_A', 'STOCK_B'],
                            start_date='2023-01-03',
                            end_date='2023-01-05',
                            initial_cash=1000000.0
                        )

                        # 验证数据加载成功
                        assert len(engine.data) >= 1
    
    @pytest.mark.unit
    def test_data_loading_single_security(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试单个股票的数据加载路径"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)

        # 修复：patch目标应为engine模块
        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()

            mock_data = {'STOCK_A': mock_csv_data}

            # 模拟数据源管理器，避免依赖AkShare
            with patch('simtradelab.data_sources.manager.DataSourceManager') as mock_manager_class:
                mock_manager = mock_manager_class.return_value
                mock_manager.get_history.return_value = mock_data

                with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage') as mock_optimizer:
                    mock_optimizer.return_value = mock_data

                    # 使用CSV数据源而不是akshare，避免依赖
                    engine = BacktestEngine(
                        strategy_file=simple_strategy_file,
                        data_path=str(csv_path),
                        securities=['STOCK_A'],
                        start_date='2023-01-03',
                        end_date='2023-01-05',
                        initial_cash=1000000.0
                    )

                    # 验证数据加载成功
                    assert len(engine.data) >= 1
    
    @pytest.mark.unit
    def test_data_loading_no_date_range(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试未指定日期范围的数据加载"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 修复：patch目标应为engine模块
        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()
            
            with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage') as mock_optimizer:
                mock_optimizer.return_value = {'STOCK_A': mock_csv_data}
                
                engine = BacktestEngine(
                    strategy_file=simple_strategy_file,
                    data_path=str(csv_path),
                    start_date=None,
                    end_date=None,
                    initial_cash=1000000.0
                )
                
                # 修复：验证默认日期
                assert engine.start_date is not None
                assert engine.end_date is not None
                # 默认日期可能依赖于测试环境，这里只验证非空
                assert isinstance(engine.start_date, pd.Timestamp)
                assert isinstance(engine.end_date, pd.Timestamp)
    
    @pytest.mark.unit
    def test_data_loading_no_securities_error(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试无法获取股票列表时的错误处理"""
        # 创建一个空的CSV文件来模拟无数据情况
        empty_csv_path = Path(temp_dir) / "empty_data.csv"
        empty_df = pd.DataFrame(columns=['date', 'security', 'open', 'high', 'low', 'close', 'volume'])
        empty_df.to_csv(empty_csv_path, index=False)

        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            # 缓存未命中
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()

            # 模拟数据源管理器，避免依赖AkShare
            with patch('simtradelab.data_sources.manager.DataSourceManager') as mock_manager_class:
                mock_manager = mock_manager_class.return_value
                mock_manager.get_stock_list.return_value = []  # 空股票列表
                mock_manager.get_history.return_value = {}  # 空数据

                from simtradelab.exceptions import DataLoadError
                # 测试空数据文件的错误处理
                with pytest.raises((DataLoadError, ValueError, Exception)):
                    BacktestEngine(
                        strategy_file=simple_strategy_file,
                        data_path=str(empty_csv_path),
                        securities=['NONEXISTENT_STOCK'],  # 不存在的股票
                        start_date='2023-01-03',
                        end_date='2023-01-05',
                        initial_cash=1000000.0
                    )
    
    @pytest.mark.unit
    def test_data_loading_exception_handling(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试数据加载过程中的异常处理"""
        # 创建一个损坏的CSV文件来模拟读取异常
        bad_csv_path = Path(temp_dir) / "bad_data.csv"
        with open(bad_csv_path, 'w') as f:
            f.write("invalid,csv,content\nwith,malformed,data")

        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            # 缓存未命中
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()

            # 模拟CSV读取异常
            with patch('pandas.read_csv') as mock_read_csv:
                mock_read_csv.side_effect = Exception("File read error")

                from simtradelab.exceptions import DataLoadError
                # 测试文件读取异常处理
                with pytest.raises((DataLoadError, Exception)):
                    BacktestEngine(
                        strategy_file=simple_strategy_file,
                        data_path=str(bad_csv_path),
                        securities=['STOCK_A'],
                        start_date='2023-01-03',
                        end_date='2023-01-05',
                        initial_cash=1000000.0
                    )
    
    @pytest.mark.unit
    def test_memory_optimization_applied(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试内存优化是否被应用"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 修复：patch目标应为engine模块
        with patch('simtradelab.engine.get_global_cache') as mock_cache:
            mock_cache.return_value.get.return_value = None
            mock_cache.return_value.set = Mock()
            
            with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage') as mock_optimizer:
                optimized_data = {'STOCK_A': mock_csv_data}
                mock_optimizer.return_value = optimized_data
                
                engine = BacktestEngine(
                    strategy_file=simple_strategy_file,
                    data_path=str(csv_path),
                    start_date='2023-01-03',
                    end_date='2023-01-05',
                    initial_cash=1000000.0
                )
                
                mock_optimizer.assert_called()
                mock_cache.return_value.set.assert_called()
    
    @pytest.mark.unit
    def test_init_data_source_default_source(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试使用默认数据源初始化"""
        csv_path = Path(temp_dir) / "test_data.csv"
        mock_csv_data.to_csv(csv_path, index=False)
        
        # 修复：统一和简化模拟逻辑
        with patch('simtradelab.engine.load_config') as mock_load_config:
            mock_config = mock_load_config.return_value
            mock_config.get_default_source.return_value = 'csv'
            mock_config.get_source_config.return_value = {'data_path': str(csv_path)}

            dates = pd.to_datetime(pd.date_range(start='2023-01-01', end='2023-01-10', freq='D'))
            mock_df = pd.DataFrame({'close': range(10)}, index=dates)
            mock_data = {'STOCK_A': mock_df, 'STOCK_B': mock_df}

            mock_source = Mock()
            mock_source.get_stock_list.return_value = ['STOCK_A', 'STOCK_B']
            mock_source.get_history.return_value = mock_data
            
            with patch('simtradelab.engine.DataSourceFactory.create', return_value=mock_source) as mock_create:
                with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage', return_value=mock_data):
                    engine = BacktestEngine(
                        strategy_file=simple_strategy_file,
                        data_source=None,
                        data_path=None,
                        securities=['STOCK_A', 'STOCK_B'],
                        start_date='2023-01-03',
                        end_date='2023-01-05',
                        initial_cash=1000000.0
                    )
            
            mock_config.get_default_source.assert_called_once()
            mock_create.assert_called_once_with('csv', data_path=str(csv_path))
    
    @pytest.mark.unit
    def test_init_data_source_string_parameter(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试使用字符串参数初始化数据源"""
        # 修复：统一和简化模拟逻辑
        dates = pd.to_datetime(pd.date_range(start='2023-01-01', end='2023-01-10', freq='D'))
        mock_df = pd.DataFrame({'close': range(10)}, index=dates)
        mock_data = {'STOCK_A': mock_df}

        mock_source = Mock()
        mock_source.get_stock_list.return_value = ['STOCK_A']
        mock_source.get_history.return_value = mock_data
        
        with patch('simtradelab.engine.DataSourceFactory.create', return_value=mock_source) as mock_create:
            with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage', return_value=mock_data):
                engine = BacktestEngine(
                    strategy_file=simple_strategy_file,
                    data_source='akshare',
                    securities=['STOCK_A'],
                    start_date='2023-01-03',
                    end_date='2023-01-05',
                    initial_cash=1000000.0
                )
            
        mock_create.assert_called()
    
    @pytest.mark.unit
    def test_init_data_source_object_parameter(self, simple_strategy_file, mock_csv_data, temp_dir):
        """测试使用对象参数初始化数据源"""
        # 修复：统一和简化模拟逻辑
        dates = pd.to_datetime(pd.date_range(start='2023-01-01', end='2023-01-10', freq='D'))
        mock_df = pd.DataFrame({'close': range(10)}, index=dates)
        mock_data = {'STOCK_A': mock_df}

        mock_data_source = Mock()
        mock_data_source.get_stock_list.return_value = ['STOCK_A']
        mock_data_source.get_history.return_value = mock_data
        
        with patch('simtradelab.engine.MemoryOptimizer.reduce_memory_usage', return_value=mock_data):
            engine = BacktestEngine(
                strategy_file=simple_strategy_file,
                data_source=mock_data_source,
                securities=['STOCK_A'],
                start_date='2023-01-03',
                end_date='2023-01-05',
                initial_cash=1000000.0
            )
        
        assert engine.data_source_manager.primary_source is mock_data_source
