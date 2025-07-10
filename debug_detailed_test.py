#!/usr/bin/env python3

import tempfile
import textwrap
from pathlib import Path

from simtradelab.adapters.ptrade.adapter import PTradeAdapter
from simtradelab.plugins.base import PluginConfig

# 创建适配器
metadata = PTradeAdapter.METADATA
config = PluginConfig(config={
    "initial_cash": 1000000,
    "commission_rate": 0.0003,
    "slippage_rate": 0.001      
})
adapter = PTradeAdapter(metadata, config)
adapter.initialize()

print(f"Initial config - commission: {adapter._commission_rate}, slippage: {adapter._slippage_rate}")
print(f"Router config - commission: {adapter._api_router._commission_rate}, slippage: {adapter._api_router._slippage_rate}")

# 创建测试策略
cost_test_strategy = textwrap.dedent("""
    def initialize(context):
        set_universe(["000001.SZ"])
        context.g.test_completed = False

    def handle_data(context, data):
        if context.g.test_completed:
            return
            
        # 执行测试交易
        stock = "000001.SZ"
        if stock in data:
            price = data[stock]['close']
            print(f"Strategy sees price: {price}")
            shares = 1000  # 买入1000股
            
            # 直接指定价格下单，不依赖当前价格获取
            order_id = order(stock, shares, price)  # 使用limit_price参数
            print(f"Order placed with limit price: {price}")
            context.g.test_completed = True
""")

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
    f.write(cost_test_strategy)
    strategy_path = f.name
    
try:
    adapter.load_strategy(strategy_path)
    context = adapter._ptrade_context
    initial_cash = context.portfolio.cash
    
    print(f"Initial cash: {initial_cash}")
    print(f"After loading strategy - router commission: {adapter._api_router._commission_rate}, slippage: {adapter._api_router._slippage_rate}")
    
    # 执行交易
    test_data = {"000001.SZ": {"close": 15.0}}
    # 手动设置current_data，这样_get_current_price可以找到价格
    context.current_data = test_data
    if hasattr(adapter._strategy_module, 'handle_data'):
        print("Executing handle_data...")
        adapter._strategy_module.handle_data(context, test_data)
    
    # 验证结果
    portfolio = context.portfolio
    print(f"Final cash: {portfolio.cash}")
    print(f"Cash used: {initial_cash - portfolio.cash}")
    
    if "000001.SZ" in portfolio.positions:
        position = portfolio.positions["000001.SZ"]
        print(f"Position amount: {position.amount}")
        print(f"Position cost basis: {position.cost_basis}")
        print(f"Position market value: {position.market_value}")
        
        # 计算理论成本
        expected_cost = 1000 * 15.0  # 15000
        commission = expected_cost * 0.0003  # 4.5
        slippage_cost = expected_cost * 0.001  # 15
        total_expected_cost = expected_cost + commission + slippage_cost  # 15019.5
        
        print(f"Expected cost: {expected_cost}")
        print(f"Expected commission: {commission}")
        print(f"Expected slippage: {slippage_cost}")
        print(f"Total expected cost: {total_expected_cost}")
        
        actual_cash_used = initial_cash - portfolio.cash
        print(f"Actual cash used: {actual_cash_used}")
        print(f"Difference: {actual_cash_used - total_expected_cost}")
        
    else:
        print("No position found!")
        
finally:
    Path(strategy_path).unlink()