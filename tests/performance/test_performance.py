#!/usr/bin/env python3
"""
性能测试 - 测试系统在各种负载下的性能
"""

import pytest
import time
import tempfile
import os
import pandas as pd
from pathlib import Path

from ptradesim.engine import BacktestEngine


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.performance
    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        
        # 创建大数据集
        start_time = time.time()
        
        # 生成1年的分钟级数据
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='1min')
        stocks = [f'STOCK_{i:03d}' for i in range(10)]  # 10只股票
        
        data_rows = []
        for date in dates[:1000]:  # 限制数据量以避免测试过慢
            for stock in stocks:
                data_rows.append({
                    'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'security': stock,
                    'open': 10.0 + (hash(f"{date}{stock}") % 100) / 100,
                    'high': 10.5 + (hash(f"{date}{stock}") % 100) / 100,
                    'low': 9.5 + (hash(f"{date}{stock}") % 100) / 100,
                    'close': 10.0 + (hash(f"{date}{stock}") % 100) / 100,
                    'volume': 1000 + (hash(f"{date}{stock}") % 10000)
                })
        
        df = pd.DataFrame(data_rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            data_file = f.name
        
        data_creation_time = time.time() - start_time
        print(f"数据创建时间: {data_creation_time:.2f}秒")
        
        # 创建简单策略
        strategy_content = '''
def initialize(context):
    context.stocks = [f'STOCK_{i:03d}' for i in range(10)]
    context.trade_count = 0

def handle_data(context, data):
    context.trade_count += 1
    if context.trade_count % 100 == 0:  # 每100次数据更新交易一次
        if len(data) > 0:
            stock = list(data.keys())[0]
            order(stock, 10)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            # 测试引擎性能
            engine_start_time = time.time()
            
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=data_file,
                start_date='2023-01-01',
                end_date='2023-01-02',
                initial_cash=1000000,
                frequency='1m'
            )
            
            initialization_time = time.time() - engine_start_time
            print(f"引擎初始化时间: {initialization_time:.2f}秒")
            
            # 运行回测
            run_start_time = time.time()
            engine.run()
            run_time = time.time() - run_start_time
            
            print(f"回测运行时间: {run_time:.2f}秒")
            print(f"处理的数据点数: {engine.context.trade_count}")
            print(f"每秒处理数据点: {engine.context.trade_count / run_time:.0f}")
            
            # 性能断言
            assert run_time < 30  # 应该在30秒内完成
            assert engine.context.trade_count > 0
            
        finally:
            os.unlink(data_file)
            os.unlink(strategy_file)
    
    @pytest.mark.performance
    def test_high_frequency_trading_performance(self):
        """测试高频交易性能"""
        
        # 创建高频策略
        strategy_content = '''
def initialize(context):
    context.stock = 'STOCK_A'
    context.trade_count = 0
    context.order_count = 0

def handle_data(context, data):
    context.trade_count += 1
    
    if context.stock in data:
        # 高频交易 - 每次都下单
        context.order_count += 1
        order(context.stock, 1)  # 小额交易
        
        # 获取各种数据
        positions = get_positions()
        orders = get_orders()
        current_data = get_current_data([context.stock])
        price = get_price(context.stock)
'''
        
        # 创建测试数据
        data_rows = []
        for i in range(1000):  # 1000个数据点
            data_rows.append({
                'date': f'2023-01-01 09:{i//60:02d}:{i%60:02d}',
                'security': 'STOCK_A',
                'open': 10.0 + i * 0.001,
                'high': 10.1 + i * 0.001,
                'low': 9.9 + i * 0.001,
                'close': 10.0 + i * 0.001,
                'volume': 1000
            })
        
        df = pd.DataFrame(data_rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            data_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            start_time = time.time()
            
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=data_file,
                start_date='2023-01-01',
                end_date='2023-01-01',
                initial_cash=1000000,
                frequency='1m'
            )
            
            engine.run()
            
            total_time = time.time() - start_time
            
            print(f"高频交易测试时间: {total_time:.2f}秒")
            print(f"订单数量: {engine.context.order_count}")
            print(f"每秒订单数: {engine.context.order_count / total_time:.0f}")
            
            # 性能断言
            assert total_time < 10  # 应该在10秒内完成
            assert engine.context.order_count > 0
            
        finally:
            os.unlink(data_file)
            os.unlink(strategy_file)
    
    @pytest.mark.performance
    def test_memory_usage_performance(self):
        """测试内存使用性能"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量数据的策略
        strategy_content = '''
def initialize(context):
    context.stocks = [f'STOCK_{i:03d}' for i in range(50)]
    context.data_cache = {}

def handle_data(context, data):
    # 缓存大量数据
    for stock in context.stocks:
        if stock in data:
            history = get_history(20, '1d', ['close', 'volume'], [stock])
            context.data_cache[stock] = history
            
            # 进行一些计算
            if len(history) > 10:
                mean_price = history['close'].mean()
                if mean_price > 10:
                    order(stock, 10)
'''
        
        # 创建多股票数据
        data_rows = []
        for i in range(100):  # 100天
            for j in range(50):  # 50只股票
                stock = f'STOCK_{j:03d}'
                data_rows.append({
                    'date': f'2023-{(i//30)+1:02d}-{(i%30)+1:02d}',
                    'security': stock,
                    'open': 10.0 + j * 0.1,
                    'high': 10.5 + j * 0.1,
                    'low': 9.5 + j * 0.1,
                    'close': 10.0 + j * 0.1 + i * 0.01,
                    'volume': 1000 + j * 100
                })
        
        df = pd.DataFrame(data_rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            data_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=data_file,
                start_date='2023-01-01',
                end_date='2023-01-10',
                initial_cash=1000000
            )
            
            engine.run()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"初始内存: {initial_memory:.1f} MB")
            print(f"最终内存: {final_memory:.1f} MB")
            print(f"内存增长: {memory_increase:.1f} MB")
            
            # 内存使用应该合理
            assert memory_increase < 500  # 不应该增长超过500MB
            
        finally:
            os.unlink(data_file)
            os.unlink(strategy_file)
    
    @pytest.mark.performance
    def test_concurrent_strategies_performance(self):
        """测试并发策略性能（模拟）"""
        
        # 创建多个策略并依次运行（模拟并发）
        strategy_templates = [
            '''
def initialize(context):
    context.stock = 'STOCK_A'
    context.strategy_id = {strategy_id}

def handle_data(context, data):
    if context.stock in data:
        order(context.stock, 10 + context.strategy_id)
''',
            '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.strategy_id = {strategy_id}

def handle_data(context, data):
    for stock in context.stocks:
        if stock in data:
            order(stock, 5 + context.strategy_id)
''',
            '''
def initialize(context):
    context.stock = 'STOCK_B'
    context.strategy_id = {strategy_id}

def handle_data(context, data):
    if context.stock in data:
        positions = get_positions()
        if len(positions) == 0:
            order(context.stock, 20 + context.strategy_id)
'''
        ]
        
        # 创建测试数据
        data_rows = []
        for i in range(10):
            for stock in ['STOCK_A', 'STOCK_B']:
                data_rows.append({
                    'date': f'2023-01-{i+1:02d}',
                    'security': stock,
                    'open': 10.0,
                    'high': 11.0,
                    'low': 9.0,
                    'close': 10.0 + i * 0.1,
                    'volume': 1000
                })
        
        df = pd.DataFrame(data_rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            data_file = f.name
        
        try:
            start_time = time.time()
            
            # 运行多个策略
            for i, template in enumerate(strategy_templates):
                strategy_content = template.format(strategy_id=i)
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(strategy_content)
                    strategy_file = f.name
                
                try:
                    engine = BacktestEngine(
                        strategy_file=strategy_file,
                        data_path=data_file,
                        start_date='2023-01-01',
                        end_date='2023-01-05',
                        initial_cash=100000
                    )
                    
                    engine.run()
                    
                finally:
                    os.unlink(strategy_file)
            
            total_time = time.time() - start_time
            
            print(f"多策略运行时间: {total_time:.2f}秒")
            print(f"平均每策略时间: {total_time / len(strategy_templates):.2f}秒")
            
            # 性能断言
            assert total_time < 30  # 所有策略应该在30秒内完成
            
        finally:
            os.unlink(data_file)


class TestStressTest:
    """压力测试"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_long_period_backtest(self):
        """测试长期回测"""
        
        # 创建一年的数据
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='1d')
        data_rows = []
        
        for date in dates:
            for stock in ['STOCK_A', 'STOCK_B', 'STOCK_C']:
                price = 10.0 + (hash(f"{date}{stock}") % 1000) / 100
                data_rows.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'security': stock,
                    'open': price,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': 1000 + (hash(f"{date}{stock}") % 10000)
                })
        
        df = pd.DataFrame(data_rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            data_file = f.name
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C']
    context.rebalance_freq = 30  # 每30天重新平衡

def handle_data(context, data):
    # 简单的买入持有策略，定期重新平衡
    if hasattr(context, 'day_count'):
        context.day_count += 1
    else:
        context.day_count = 1
    
    if context.day_count % context.rebalance_freq == 0:
        # 重新平衡
        positions = get_positions()
        target_value = 100000 / len(context.stocks)
        
        for stock in context.stocks:
            if stock in data:
                current_value = positions.get(stock, type('obj', (object,), {'market_value': 0})).market_value
                price = get_price(stock)
                if price:
                    target_shares = int(target_value / price)
                    current_shares = positions.get(stock, type('obj', (object,), {'amount': 0})).amount
                    order(stock, target_shares - current_shares)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            start_time = time.time()
            
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=data_file,
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_cash=100000
            )
            
            engine.run()
            
            total_time = time.time() - start_time
            
            print(f"一年回测时间: {total_time:.2f}秒")
            print(f"处理天数: {len(dates)}")
            print(f"每天处理时间: {total_time / len(dates) * 1000:.2f}毫秒")
            
            # 验证回测完成
            assert hasattr(engine.context, 'day_count')
            assert engine.context.day_count > 0
            
            # 性能要求
            assert total_time < 60  # 一年回测应该在1分钟内完成
            
        finally:
            os.unlink(data_file)
            os.unlink(strategy_file)
