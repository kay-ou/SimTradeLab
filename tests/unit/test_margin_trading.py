#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融资融券交易模块测试
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from simtradelab.margin_trading import (
    # 交易类函数
    margin_trade, margincash_open, margincash_close, margincash_direct_refund,
    marginsec_open, marginsec_close, marginsec_direct_refund,
    
    # 查询类函数
    get_margincash_stocks, get_marginsec_stocks, get_margin_contract,
    get_margin_contractreal, get_margin_assert, get_assure_security_list,
    get_margincash_open_amount, get_margincash_close_amount,
    get_marginsec_open_amount, get_marginsec_close_amount,
    get_margin_entrans_amount, get_enslo_security_info
)


class TestMarginTrading:
    """融资融券交易测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.name = "test_engine"
        return engine
    
    # ==================== 交易类函数测试 ====================
    
    @pytest.mark.unit
    def test_margin_trade_buy(self, mock_engine):
        """测试担保品买入"""
        result = margin_trade(mock_engine, '000001.SZ', 1000, 'buy')
        
        assert result['success'] is True
        assert result['security'] == '000001.SZ'
        assert result['amount'] == 1000
        assert result['operation'] == 'buy'
        assert result['order_type'] == 'margin_trade'
        assert 'order_id' in result
        assert 'timestamp' in result
        assert result['order_id'].startswith('MARGIN_TRADE_')
    
    @pytest.mark.unit
    def test_margin_trade_sell(self, mock_engine):
        """测试担保品卖出"""
        result = margin_trade(mock_engine, '600519.SH', 500, 'sell')
        
        assert result['success'] is True
        assert result['security'] == '600519.SH'
        assert result['amount'] == 500
        assert result['operation'] == 'sell'
        assert result['order_type'] == 'margin_trade'
    
    @pytest.mark.unit
    def test_margincash_open_success(self, mock_engine):
        """测试融资买入成功"""
        with patch('simtradelab.margin_trading.get_margin_assert') as mock_assert:
            mock_assert.return_value = {
                'available_margin_amount': 500000.0
            }
            
            result = margincash_open(mock_engine, '000001.SZ', 1000, 12.50)
            
            assert result['success'] is True
            assert result['security'] == '000001.SZ'
            assert result['amount'] == 1000
            assert result['price'] == 12.50
            assert result['order_type'] == 'margincash_open'
            assert result['estimated_cost'] == 12500.0
            assert 'order_id' in result
    
    @pytest.mark.unit
    def test_margincash_open_insufficient_margin(self, mock_engine):
        """测试融资买入额度不足"""
        with patch('simtradelab.margin_trading.get_margin_assert') as mock_assert:
            mock_assert.return_value = {
                'available_margin_amount': 5000.0  # 额度不足
            }
            
            result = margincash_open(mock_engine, '000001.SZ', 1000, 12.50)
            
            assert result['success'] is False
            assert result['error'] == '可用融资额度不足'
            assert result['order_id'] is None
    
    @pytest.mark.unit
    def test_margincash_close(self, mock_engine):
        """测试卖券还款"""
        result = margincash_close(mock_engine, '000001.SZ', 500, 13.00)
        
        assert result['success'] is True
        assert result['security'] == '000001.SZ'
        assert result['amount'] == 500
        assert result['price'] == 13.00
        assert result['order_type'] == 'margincash_close'
        assert result['order_id'].startswith('MARGIN_CASH_CLOSE_')
    
    @pytest.mark.unit
    def test_margincash_direct_refund(self, mock_engine):
        """测试直接还款"""
        result = margincash_direct_refund(mock_engine, 50000.0)
        
        assert result['success'] is True
        assert result['amount'] == 50000.0
        assert result['transaction_type'] == 'margincash_direct_refund'
        assert result['transaction_id'].startswith('MARGIN_REFUND_')
    
    @pytest.mark.unit
    def test_marginsec_open_success(self, mock_engine):
        """测试融券卖出成功"""
        with patch('simtradelab.margin_trading.get_marginsec_open_amount') as mock_amount:
            mock_amount.return_value = {
                'max_sell_amount': 10000
            }
            
            result = marginsec_open(mock_engine, '000001.SZ', 1000, 12.50)
            
            assert result['success'] is True
            assert result['security'] == '000001.SZ'
            assert result['amount'] == 1000
            assert result['price'] == 12.50
            assert result['order_type'] == 'marginsec_open'
    
    @pytest.mark.unit
    def test_marginsec_open_insufficient_amount(self, mock_engine):
        """测试融券卖出数量不足"""
        with patch('simtradelab.margin_trading.get_marginsec_open_amount') as mock_amount:
            mock_amount.return_value = {
                'max_sell_amount': 500  # 数量不足
            }
            
            result = marginsec_open(mock_engine, '000001.SZ', 1000, 12.50)
            
            assert result['success'] is False
            assert result['error'] == '可融券数量不足'
            assert result['order_id'] is None
    
    @pytest.mark.unit
    def test_marginsec_close(self, mock_engine):
        """测试买券还券"""
        result = marginsec_close(mock_engine, '000001.SZ', 500, 12.00)
        
        assert result['success'] is True
        assert result['security'] == '000001.SZ'
        assert result['amount'] == 500
        assert result['price'] == 12.00
        assert result['order_type'] == 'marginsec_close'
        assert result['order_id'].startswith('MARGIN_SEC_CLOSE_')
    
    @pytest.mark.unit
    def test_marginsec_direct_refund(self, mock_engine):
        """测试直接还券"""
        result = marginsec_direct_refund(mock_engine, '000001.SZ', 1000)
        
        assert result['success'] is True
        assert result['security'] == '000001.SZ'
        assert result['amount'] == 1000
        assert result['transaction_type'] == 'marginsec_direct_refund'
        assert result['transaction_id'].startswith('MARGIN_SEC_REFUND_')
    
    # ==================== 查询类函数测试 ====================
    
    @pytest.mark.unit
    def test_get_margincash_stocks(self, mock_engine):
        """测试获取融资标的"""
        result = get_margincash_stocks(mock_engine)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查第一个标的的结构
        stock = result[0]
        assert 'security' in stock
        assert 'name' in stock
        assert 'margin_ratio' in stock
        assert 'status' in stock
        assert stock['security'] == '000001.SZ'
        assert stock['name'] == '平安银行'
    
    @pytest.mark.unit
    def test_get_marginsec_stocks(self, mock_engine):
        """测试获取融券标的"""
        result = get_marginsec_stocks(mock_engine)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查第一个标的的结构
        stock = result[0]
        assert 'security' in stock
        assert 'name' in stock
        assert 'sec_ratio' in stock
        assert 'available_amount' in stock
        assert 'status' in stock
    
    @pytest.mark.unit
    def test_get_margin_contract(self, mock_engine):
        """测试合约查询"""
        result = get_margin_contract(mock_engine)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查合约结构
        contract = result[0]
        assert 'contract_id' in contract
        assert 'security' in contract
        assert 'contract_type' in contract
        assert 'amount' in contract
        assert 'price' in contract
        assert contract['contract_type'] in ['margin_cash', 'margin_sec']
    
    @pytest.mark.unit
    def test_get_margin_contractreal(self, mock_engine):
        """测试实时合约查询"""
        result = get_margin_contractreal(mock_engine)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查实时合约结构
        contract = result[0]
        assert 'current_value' in contract
        assert 'profit_loss' in contract
        assert 'margin_ratio' in contract
        assert 'risk_level' in contract
    
    @pytest.mark.unit
    def test_get_margin_assert(self, mock_engine):
        """测试信用资产查询"""
        result = get_margin_assert(mock_engine)
        
        assert isinstance(result, dict)
        
        # 检查必要字段
        required_fields = [
            'total_asset', 'total_debt', 'net_asset', 'margin_available',
            'margin_ratio', 'available_margin_amount', 'available_sec_amount',
            'risk_level', 'margin_call_line', 'force_close_line'
        ]
        
        for field in required_fields:
            assert field in result
        
        # 检查数值合理性
        assert result['total_asset'] > 0
        assert result['net_asset'] > 0
        assert result['margin_ratio'] > 0
    
    @pytest.mark.unit
    def test_get_assure_security_list(self, mock_engine):
        """测试担保券查询"""
        result = get_assure_security_list(mock_engine)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查担保券结构
        security = result[0]
        assert 'security' in security
        assert 'name' in security
        assert 'assure_ratio' in security
        assert 'status' in security
        assert 'category' in security
    
    @pytest.mark.unit
    def test_get_margincash_open_amount(self, mock_engine):
        """测试融资最大可买数量查询"""
        with patch('simtradelab.margin_trading.get_margin_assert') as mock_assert:
            mock_assert.return_value = {
                'available_margin_amount': 100000.0
            }
            
            result = get_margincash_open_amount(mock_engine, '000001.SZ')
            
            assert isinstance(result, dict)
            assert 'security' in result
            assert 'max_buy_amount' in result
            assert 'available_margin' in result
            assert 'current_price' in result
            assert 'margin_ratio' in result
            assert result['security'] == '000001.SZ'
            assert result['max_buy_amount'] > 0
    
    @pytest.mark.unit
    def test_get_margincash_close_amount(self, mock_engine):
        """测试卖券还款最大可卖数量查询"""
        result = get_margincash_close_amount(mock_engine, '000001.SZ')
        
        assert isinstance(result, dict)
        assert 'security' in result
        assert 'max_sell_amount' in result
        assert 'position_amount' in result
        assert 'available_amount' in result
        assert result['security'] == '000001.SZ'
    
    @pytest.mark.unit
    def test_get_marginsec_open_amount(self, mock_engine):
        """测试融券最大可卖数量查询"""
        with patch('simtradelab.margin_trading.get_marginsec_stocks') as mock_stocks:
            mock_stocks.return_value = [
                {
                    'security': '000001.SZ',
                    'available_amount': 50000,
                    'sec_ratio': 0.5
                }
            ]
            
            result = get_marginsec_open_amount(mock_engine, '000001.SZ')
            
            assert isinstance(result, dict)
            assert 'security' in result
            assert 'max_sell_amount' in result
            assert 'available_sec_amount' in result
            assert 'sec_ratio' in result
            assert result['security'] == '000001.SZ'
            assert result['max_sell_amount'] == 50000
    
    @pytest.mark.unit
    def test_get_marginsec_close_amount(self, mock_engine):
        """测试买券还券最大可买数量查询"""
        result = get_marginsec_close_amount(mock_engine, '000001.SZ')
        
        assert isinstance(result, dict)
        assert 'security' in result
        assert 'max_buy_amount' in result
        assert 'sec_debt_amount' in result
        assert 'available_cash' in result
        assert result['security'] == '000001.SZ'
    
    @pytest.mark.unit
    def test_get_margin_entrans_amount(self, mock_engine):
        """测试现券还券数量查询"""
        result = get_margin_entrans_amount(mock_engine, '000001.SZ')
        
        assert isinstance(result, dict)
        assert 'security' in result
        assert 'available_return_amount' in result
        assert 'cash_position' in result
        assert 'sec_debt_amount' in result
        assert result['security'] == '000001.SZ'
        
        # 验证逻辑：可还券数量应该是现券持仓和融券负债的较小值
        assert result['available_return_amount'] <= result['cash_position']
        assert result['available_return_amount'] <= result['sec_debt_amount']
    
    @pytest.mark.unit
    def test_get_enslo_security_info(self, mock_engine):
        """测试融券头寸信息查询"""
        result = get_enslo_security_info(mock_engine, '000001.SZ')
        
        assert isinstance(result, dict)
        
        # 检查必要字段
        required_fields = [
            'security', 'total_enslo_amount', 'available_enslo_amount',
            'enslo_rate', 'min_enslo_amount', 'max_enslo_amount', 'enslo_status'
        ]
        
        for field in required_fields:
            assert field in result
        
        assert result['security'] == '000001.SZ'
        assert result['available_enslo_amount'] > 0
        assert result['enslo_rate'] > 0
    
    # ==================== 边界条件和异常测试 ====================
    
    @pytest.mark.unit
    def test_marginsec_open_amount_nonexistent_security(self, mock_engine):
        """测试查询不存在证券的融券数量"""
        with patch('simtradelab.margin_trading.get_marginsec_stocks') as mock_stocks:
            mock_stocks.return_value = []  # 空列表，模拟不存在的证券
            
            result = get_marginsec_open_amount(mock_engine, 'NONEXISTENT.SZ')
            
            assert result['security'] == 'NONEXISTENT.SZ'
            assert result['max_sell_amount'] == 0
            assert result['available_sec_amount'] == 0
    
    @pytest.mark.unit
    def test_margin_trade_with_none_price(self, mock_engine):
        """测试融资买入时价格为None的情况"""
        with patch('simtradelab.margin_trading.get_margin_assert') as mock_assert:
            mock_assert.return_value = {
                'available_margin_amount': 500000.0
            }
            
            result = margincash_open(mock_engine, '000001.SZ', 1000, None)
            
            assert result['success'] is True
            assert result['price'] is None
            assert result['estimated_cost'] == 10000.0  # 1000 * 10.0 (默认价格)
    
    @pytest.mark.unit
    def test_timestamp_format(self, mock_engine):
        """测试时间戳格式"""
        result = margin_trade(mock_engine, '000001.SZ', 1000, 'buy')
        
        # 验证时间戳格式
        timestamp = result['timestamp']
        assert isinstance(timestamp, str)
        # 简单验证ISO格式
        assert 'T' in timestamp or ' ' in timestamp
    
    @pytest.mark.unit
    def test_order_id_format(self, mock_engine):
        """测试订单ID格式"""
        result = margin_trade(mock_engine, '000001.SZ', 1000, 'buy')

        # 验证订单ID格式
        order_id = result['order_id']
        assert isinstance(order_id, str)
        assert order_id.startswith('MARGIN_TRADE_')

        # 验证时间戳部分是数字
        timestamp_part = order_id.replace('MARGIN_TRADE_', '')
        assert timestamp_part.isdigit()
        assert len(timestamp_part) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
