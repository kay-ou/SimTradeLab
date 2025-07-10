#!/usr/bin/env python3

from simtradelab.adapters.ptrade.adapter import PTradeAdapter
from simtradelab.plugins.base import PluginConfig

# 创建适配器，使用与测试相同的配置
metadata = PTradeAdapter.METADATA
config = PluginConfig(config={
    "initial_cash": 1000000,  # 100万初始资金
    "commission_rate": 0.0003,  # 万三手续费，使用PTrade标准键名
    "slippage_rate": 0.001      # 千一滑点，使用PTrade标准键名
})

adapter = PTradeAdapter(metadata, config)
adapter.initialize()

print(f"Adapter commission rate: {adapter._commission_rate}")
print(f"Adapter slippage rate: {adapter._slippage_rate}")
print(f"Initial cash: {adapter._initial_cash}")

# 检查API路由器的配置
print(f"API router commission rate: {adapter._api_router._commission_rate}")
print(f"API router slippage rate: {adapter._api_router._slippage_rate}")