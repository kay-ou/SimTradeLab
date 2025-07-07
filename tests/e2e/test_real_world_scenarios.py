#!/usr/bin/env python3
"""
端到端测试 - 真实世界场景测试
"""

import pytest
import tempfile
import os
import pandas as pd
from pathlib import Path

from simtradelab.engine import BacktestEngine
from simtradelab.data_sources.akshare_source import AkshareDataSource


class TestRealWorldScenarios:
    """真实世界场景测试"""
    
    @pytest.mark.e2e
    def test_complete_trading_workflow(self, sample_data_file):
        """测试完整的交易工作流程"""
        
        strategy_content = '''
def initialize(context):
    # 策略初始化
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.max_position_size = 0.3  # 最大持仓比例
    context.rebalance_days = 5
    context.day_count = 0
    
    # 设置交易参数
    set_commission(0.0003, 5.0, "STOCK")
    set_limit_mode(True)
    
    # 记录策略开始
    log.info("策略初始化完成")

def before_trading_start(context, data):
    # 交易前准备
    context.day_count += 1
    log.info(f"第{context.day_count}个交易日开始")

def handle_data(context, data):
    # 主要交易逻辑
    if len(data) == 0:
        return
    
    # 获取当前持仓和资金
    positions = get_positions()
    current_cash = context.portfolio.cash
    total_value = context.portfolio.total_value
    
    # 风险管理：检查持仓比例
    for stock in context.stocks:
        if stock in positions:
            position_ratio = positions[stock]['market_value'] / total_value
            if position_ratio > context.max_position_size:
                # 减仓
                reduce_amount = int(positions[stock]['amount'] * 0.1)
                order(stock, -reduce_amount)
                log.info(f"风险控制：减持{stock} {reduce_amount}股")
    
    # 定期重新平衡
    if context.day_count % context.rebalance_days == 0:
        log.info("执行投资组合重新平衡")
        
        target_value_per_stock = total_value * context.max_position_size
        
        for stock in context.stocks:
            if stock not in data:
                continue
                
            current_price = get_price(stock)
            if not current_price:
                continue
            
            # 计算目标持仓
            target_shares = int(target_value_per_stock / current_price)
            current_shares = positions.get(stock, {'amount': 0})['amount']
            
            order_amount = target_shares - current_shares
            if abs(order_amount) > 10:  # 只有变化较大时才交易
                order(stock, order_amount)
                log.info(f"重新平衡：{stock} 目标{target_shares}股，当前{current_shares}股，下单{order_amount}股")

def after_trading_end(context, data):
    # 交易后处理
    positions = get_positions()
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    # 计算持仓市值
    positions_value = sum(position['market_value'] for position in positions.values())

    log.info(f"交易日结束：总资产{total_value:.2f}，现金{cash:.2f}，持仓市值{positions_value:.2f}")

    # 记录持仓信息
    for stock, position in positions.items():
        log.info(f"持仓：{stock} {position['amount']}股，市值{position['market_value']:.2f}")


'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=sample_data_file,
                start_date='2023-01-01',
                end_date='2023-01-10',
                initial_cash=100000
            )
            
            # 运行完整回测
            engine.run()
            
            # 验证完整工作流程
            assert hasattr(engine.context, 'day_count')
            assert engine.context.day_count > 0
            
            # 验证交易记录
            trades = engine.context.blotter.get_all_trades()
            orders = engine.context.blotter.get_all_orders()
            
            # 应该有交易活动
            assert len(orders) > 0
            
            # 验证最终状态
            final_value = engine.context.portfolio.total_value
            assert final_value > 0
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.e2e
    def test_multi_asset_portfolio_management(self, sample_data_file):
        """测试多资产投资组合管理"""
        
        strategy_content = '''
def initialize(context):
    # 多资产投资组合
    context.stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C']
    context.weights = {'STOCK_A': 0.4, 'STOCK_B': 0.3, 'STOCK_C': 0.3}
    context.rebalance_threshold = 0.05  # 5%偏差触发重新平衡
    context.last_rebalance_day = 0
    
    set_commission(0.0003, 5.0, "STOCK")

def handle_data(context, data):
    positions = get_positions()
    total_value = context.portfolio.total_value
    
    # 计算当前权重
    current_weights = {}
    for stock in context.stocks:
        if stock in positions:
            current_weights[stock] = positions[stock]['market_value'] / total_value
        else:
            current_weights[stock] = 0
    
    # 检查是否需要重新平衡
    need_rebalance = False
    for stock in context.stocks:
        target_weight = context.weights[stock]
        current_weight = current_weights[stock]
        
        if abs(current_weight - target_weight) > context.rebalance_threshold:
            need_rebalance = True
            break
    
    # 执行重新平衡
    if need_rebalance:
        log.info("触发投资组合重新平衡")
        
        for stock in context.stocks:
            if stock not in data:
                continue
            
            target_weight = context.weights[stock]
            target_value = total_value * target_weight
            
            # 使用order_target_value来避免现金不足的问题
            try:
                order_target_value(stock, target_value)
                log.info(f"重新平衡{stock}：目标权重{target_weight:.1%}，目标金额{target_value:.0f}")
            except Exception as e:
                log.warning(f"重新平衡{stock}失败: {e}")
                continue

def after_trading_end(context, data):
    # 记录投资组合状态
    positions = get_positions()
    total_value = context.portfolio.total_value
    
    weights_info = []
    for stock in context.stocks:
        if stock in positions:
            weight = positions[stock]['market_value'] / total_value
            weights_info.append(f"{stock}:{weight:.1%}")
        else:
            weights_info.append(f"{stock}:0%")
    
    log.info(f"当前权重分布：{', '.join(weights_info)}")
'''
        
        # 创建多股票数据
        data_rows = []
        for i in range(15):
            for stock in ['STOCK_A', 'STOCK_B', 'STOCK_C']:
                base_price = {'STOCK_A': 10, 'STOCK_B': 20, 'STOCK_C': 5}[stock]
                price = base_price + i * 0.1 + (hash(f"{i}{stock}") % 100) / 100
                
                data_rows.append({
                    'date': f'2023-01-{i+1:02d}',
                    'security': stock,
                    'open': price,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': 1000 + i * 100
                })
        
        df = pd.DataFrame(data_rows)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            multi_asset_data_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_content)
            strategy_file = f.name
        
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path=multi_asset_data_file,
                start_date='2023-01-01',
                end_date='2023-01-15',
                initial_cash=100000
            )
            
            engine.run()
            
            # 验证多资产管理
            positions = engine.context.portfolio.positions
            assert len(positions) > 0
            
            # 验证权重分布合理
            total_value = engine.context.portfolio.total_value
            for stock, position in positions.items():
                weight = position.market_value / total_value
                assert 0 <= weight <= 1  # 权重应该在合理范围内
            
        finally:
            os.unlink(multi_asset_data_file)
            os.unlink(strategy_file)
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_real_data_integration(self):
        """测试真实数据集成（如果可用）"""
        
        try:
            # 尝试使用AkShare获取真实数据
            akshare_source = AkshareDataSource()
            
            # 简单测试是否可以连接
            test_stocks = ['000001.SZ']  # 平安银行
            
            # 这里只测试数据源是否可用，不进行实际的网络请求
            # 在实际环境中可以启用
            pytest.skip("跳过真实数据测试以避免网络依赖")
            
        except ImportError:
            pytest.skip("AkShare不可用，跳过真实数据测试")
    
    @pytest.mark.e2e
    def test_error_recovery_and_robustness(self, sample_data_file):
        """测试错误恢复和系统健壮性"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.error_count = 0
    context.successful_trades = 0

def handle_data(context, data):
    try:
        # 故意引入一些可能的错误情况
        
        # 1. 尝试交易不存在的股票
        try:
            order('NONEXISTENT_STOCK', 100)
        except Exception as e:
            context.error_count += 1
            log.info(f"预期错误被捕获：{str(e)}")
        
        # 2. 尝试获取无效数据
        try:
            invalid_history = get_history(0, '1d', ['close'], ['INVALID'])
        except Exception as e:
            context.error_count += 1
            log.info(f"预期错误被捕获：{str(e)}")
        
        # 3. 正常交易逻辑
        for stock in context.stocks:
            if stock in data:
                try:
                    positions = get_positions()
                    if stock not in positions:
                        order(stock, 50)
                        context.successful_trades += 1
                        log.info(f"成功交易：{stock}")
                except Exception as e:
                    context.error_count += 1
                    log.info(f"交易错误：{str(e)}")
        
        # 4. 测试边界条件
        try:
            # 尝试下超大订单
            order('STOCK_A', 1000000)
        except Exception as e:
            context.error_count += 1
            log.info(f"大订单错误被捕获：{str(e)}")
        
    except Exception as e:
        context.error_count += 1
        log.info(f"策略级错误：{str(e)}")

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
            
            # 系统应该能够处理错误并继续运行
            engine.run()
            
            # 验证错误处理
            assert hasattr(engine.context, 'error_count')
            assert hasattr(engine.context, 'successful_trades')
            
            # 系统应该记录了一些错误但仍然完成了运行
            assert engine.context.error_count > 0  # 应该捕获了一些预期错误
            
        finally:
            os.unlink(strategy_file)
    
    @pytest.mark.e2e
    def test_comprehensive_api_usage(self, sample_data_file):
        """测试API的综合使用"""
        
        strategy_content = '''
def initialize(context):
    context.stocks = ['STOCK_A', 'STOCK_B']
    context.api_test_results = {}
    
    # 测试设置函数
    set_commission(0.0005, 8.0, "STOCK")
    set_limit_mode(False)
    set_benchmark('000001.SH')
    set_universe(context.stocks)

def handle_data(context, data):
    # 测试所有主要API
    api_results = {}
    
    # 交易API
    try:
        positions = get_positions()
        orders = get_orders()
        trades = get_trades()
        api_results['trading_queries'] = True
    except:
        api_results['trading_queries'] = False
    
    # 市场数据API
    try:
        if len(data) > 0:
            stock = list(data.keys())[0]
            history = get_history(5, '1d', ['close'], [stock])
            current = get_current_data([stock])
            price = get_price(stock)
            api_results['market_data'] = True
    except:
        api_results['market_data'] = False
    
    # 技术指标API
    try:
        if len(data) > 0:
            stock = list(data.keys())[0]
            macd = get_MACD(stock)
            rsi = get_RSI(stock)
            api_results['technical_indicators'] = True
    except:
        api_results['technical_indicators'] = False
    
    # 财务数据API
    try:
        fundamentals = get_fundamentals(context.stocks, 'market_cap')
        api_results['fundamentals'] = True
    except:
        api_results['fundamentals'] = False
    
    # 工具函数API
    try:
        all_stocks = get_Ashares()
        stock_status = get_stock_status(context.stocks, 'ST')
        trading_days = get_all_trades_days()
        api_results['utils'] = True
    except:
        api_results['utils'] = False
    
    # 记录API测试结果
    context.api_test_results = api_results
    
    # 执行一些交易
    if len(data) > 0:
        stock = list(data.keys())[0]
        positions = get_positions()
        if stock not in positions:
            order(stock, 100)

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
            
            # 验证API测试结果
            assert hasattr(engine.context, 'api_test_results')
            api_results = engine.context.api_test_results
            
            # 大部分API应该工作正常
            successful_apis = sum(1 for result in api_results.values() if result)
            total_apis = len(api_results)
            
            success_rate = successful_apis / total_apis if total_apis > 0 else 0
            assert success_rate >= 0.6  # 至少60%的API应该工作正常
            
        finally:
            os.unlink(strategy_file)
