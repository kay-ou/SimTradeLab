#!/usr/bin/env python3
"""
策略执行集成测试 - 测试完整的策略运行流程
"""

import pytest
import tempfile
import os
from pathlib import Path

from simtradelab.engine import BacktestEngine


class TestStrategyExecution:
    """策略执行集成测试"""
    
    @pytest.mark.integration
    def test_basic_strategy_execution(self, sample_data_file):
        """测试基本策略执行"""
        
        # 创建简单策略
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.counter = 0

def handle_data(context, data):
    context.counter += 1
    if context.counter == 1:
        # 第一天买入
        order('STOCK_A', 100)
    elif context.counter == 3:
        # 第三天卖出
        order('STOCK_A', -50)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-05',
                initial_cash=100000
            )
            
            # 运行策略
            engine.run()
            
            # 验证策略执行结果
            assert hasattr(engine.context, 'counter')
            assert engine.context.counter > 0
            
            # 验证有交易记录
            trades = engine.context.blotter.get_all_trades()
            assert len(trades) > 0
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.integration
    def test_multi_frequency_strategy(self, sample_data_file):
        """测试多频率策略执行"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A']
    context.trade_count = 0

def handle_data(context, data):
    if len(data) > 0:
        stock = list(data.keys())[0]
        context.trade_count += 1
        
        # 每次都进行小额交易
        order(stock, 10)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            # 测试日线频率
            engine_daily = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-03',
                initial_cash=100000,
                frequency='1d'
            )
            engine_daily.run()
            
            # 测试分钟频率
            engine_minute = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-02',
                initial_cash=100000,
                frequency='1m'
            )
            engine_minute.run()
            
            # 验证不同频率的执行结果
            assert engine_daily.context.trade_count > 0
            assert engine_minute.context.trade_count > 0
            
            # 分钟级应该有更多交易次数
            assert engine_minute.context.trade_count >= engine_daily.context.trade_count
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.integration
    def test_strategy_with_all_apis(self, sample_data_file):
        """测试使用所有API的策略"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    set_commission(0.001, 5.0, "STOCK")
    set_limit_mode(True)

def handle_data(context, data):
    if len(data) > 0:
        stock = list(data.keys())[0]
        
        # 使用各种API
        positions = get_positions()
        orders = get_orders()
        trades = get_trades()
        
        # 获取历史数据
        history = get_history(5, '1d', ['close'], [stock])
        current = get_current_data([stock])
        price = get_price(stock)
        
        # 技术指标
        try:
            macd = get_MACD(stock)
            rsi = get_RSI(stock)
        except:
            pass
        
        # 财务数据
        try:
            fundamentals = get_fundamentals([stock], 'market_cap')
        except:
            pass
        
        # 交易
        if len(positions) == 0:
            order(stock, 100)
        elif len(positions) > 0:
            order_target(stock, 50)

def before_trading_start(context, data):
    context.daily_start = True

def after_trading_end(context, data):
    context.daily_end = True
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-05',
                initial_cash=100000
            )
            
            engine.run()
            
            # 验证策略执行成功
            assert hasattr(engine.context, 'daily_start')
            assert hasattr(engine.context, 'daily_end')
            
            # 验证佣金设置生效
            assert engine.commission_ratio == 0.001
            assert engine.min_commission == 5.0
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.integration
    def test_error_handling_in_strategy(self, sample_data_file):
        """测试策略中的错误处理"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A']
    context.error_count = 0

def handle_data(context, data):
    try:
        # 故意引发错误
        invalid_stock = 'INVALID_STOCK'
        order(invalid_stock, 100)
    except Exception as e:
        context.error_count += 1
    
    # 正常交易
    if len(data) > 0:
        stock = list(data.keys())[0]
        order(stock, 10)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-03',
                initial_cash=100000
            )
            
            engine.run()
            
            # 验证错误被正确处理
            assert hasattr(engine.context, 'error_count')
            # 策略应该继续运行，不会因为错误而停止
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.integration
    def test_strategy_performance_tracking(self, sample_data_file):
        """测试策略性能跟踪"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.trade_dates = []

def handle_data(context, data):
    import datetime
    context.trade_dates.append(datetime.datetime.now())
    
    if len(data) > 0:
        stock = list(data.keys())[0]
        
        # 获取当前持仓
        positions = get_positions()
        
        if len(positions) == 0:
            # 没有持仓时买入
            order(stock, 100)
        else:
            # 有持仓时根据价格变化调整
            current_price = get_price(stock)
            if current_price:
                # 简单的动量策略
                history = get_history(2, '1d', ['close'], [stock])
                if len(history) >= 2:
                    if history.iloc[-1]['close'] > history.iloc[-2]['close']:
                        order(stock, 50)  # 价格上涨，加仓
                    else:
                        order(stock, -25)  # 价格下跌，减仓

def after_trading_end(context, data):
    # 记录每日性能
    positions = get_positions()
    total_value = sum(pos.market_value for pos in positions.values()) if positions else 0
    context.daily_values = getattr(context, 'daily_values', [])
    context.daily_values.append(total_value)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-05',
                initial_cash=100000
            )
            
            engine.run()
            
            # 验证性能跟踪
            assert hasattr(engine.context, 'trade_dates')
            assert hasattr(engine.context, 'daily_values')
            assert len(engine.context.trade_dates) > 0
            
            # 验证有交易活动
            trades = engine.context.blotter.get_all_trades()
            assert len(trades) > 0
            
        finally:
            os.unlink(strategy_file)


class TestAdvancedStrategies:
    """高级策略测试"""
    
    @pytest.mark.integration
    def test_grid_trading_strategy(self, sample_data_file):
        """测试网格交易策略"""
        
        strategy_content = '''
def initialize(context):
    context.stock = 'STOCK_A'
    context.grid_levels = [9.5, 10.0, 10.5, 11.0, 11.5]
    context.position_size = 100
    context.grid_positions = {}

def handle_data(context, data):
    if context.stock not in data:
        return
    
    current_price = get_price(context.stock)
    if not current_price:
        return
    
    # 网格交易逻辑
    for level in context.grid_levels:
        if abs(current_price - level) < 0.1:  # 接近网格线
            if level not in context.grid_positions:
                # 在网格线买入
                order(context.stock, context.position_size)
                context.grid_positions[level] = True
            elif current_price > level * 1.05:  # 价格上涨5%
                # 卖出获利
                order(context.stock, -context.position_size)
                del context.grid_positions[level]
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-05',
                initial_cash=100000
            )
            
            engine.run()
            
            # 验证网格策略执行
            assert hasattr(engine.context, 'grid_positions')
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.integration
    def test_momentum_strategy(self, sample_data_file):
        """测试动量策略"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.lookback = 5
    context.momentum_threshold = 0.02

def handle_data(context, data):
    for stock in context.stocks:
        if stock not in data:
            continue
        
        # 计算动量
        history = get_history(context.lookback, '1d', ['close'], [stock])
        if len(history) < context.lookback:
            continue
        
        returns = history['close'].pct_change().dropna()
        momentum = returns.mean()
        
        current_positions = get_positions()
        
        if momentum > context.momentum_threshold:
            # 正动量，买入
            if stock not in current_positions:
                order(stock, 100)
        elif momentum < -context.momentum_threshold:
            # 负动量，卖出
            if stock in current_positions:
                order(stock, -current_positions[stock].amount)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-05',
                initial_cash=100000
            )
            
            engine.run()
            
            # 验证动量策略执行
            trades = engine.context.blotter.get_all_trades()
            # 动量策略应该产生一些交易
            
        finally:
            os.unlink(strategy_file)
