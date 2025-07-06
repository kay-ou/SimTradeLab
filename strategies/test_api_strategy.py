# -*- coding: utf-8 -*-
"""
测试API策略
"""

def initialize(context):
    context.stock = "000001.SZ"
    
def handle_data(context, data):
    order_target_percent(context.stock, 0.5)
