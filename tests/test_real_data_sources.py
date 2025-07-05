# -*- coding: utf-8 -*-
"""
真实数据源功能单元测试

测试新的数据源架构和功能
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradesim import (
    BacktestEngine, DataSourceFactory, DataSourceManager, CSVDataSource,
    DataSourceConfig, load_config, TUSHARE_AVAILABLE, AKSHARE_AVAILABLE
)


class TestDataSourceFactory(unittest.TestCase):
    """测试数据源工厂"""

    def test_list_available_sources(self):
        """测试列出可用数据源"""
        sources = DataSourceFactory.list_available()
        self.assertIn('csv', sources)

        if TUSHARE_AVAILABLE:
            self.assertIn('tushare', sources)

        if AKSHARE_AVAILABLE:
            self.assertIn('akshare', sources)

    def test_create_csv_source(self):
        """测试创建CSV数据源"""
        source = DataSourceFactory.create('csv', data_path='data/sample_data.csv')
        self.assertIsInstance(source, CSVDataSource)

    def test_create_invalid_source(self):
        """测试创建无效数据源"""
        with self.assertRaises(ValueError):
            DataSourceFactory.create('invalid_source')


class TestCSVDataSource(unittest.TestCase):
    """测试CSV数据源"""

    def setUp(self):
        """设置测试环境"""
        self.source = CSVDataSource(data_path='data/sample_data.csv')

    def test_get_stock_list(self):
        """测试获取股票列表"""
        stocks = self.source.get_stock_list()
        self.assertIsInstance(stocks, list)
        self.assertGreater(len(stocks), 0)

    def test_get_history(self):
        """测试获取历史数据"""
        stocks = self.source.get_stock_list()
        if stocks:
            history = self.source.get_history(
                securities=stocks[:1],
                start_date='2023-01-01',
                end_date='2023-01-10'
            )
            self.assertIsInstance(history, dict)

    def test_get_current_data(self):
        """测试获取当前数据"""
        stocks = self.source.get_stock_list()
        if stocks:
            current = self.source.get_current_data(stocks[:1])
            self.assertIsInstance(current, dict)


class TestDataSourceManager(unittest.TestCase):
    """测试数据源管理器"""

    def setUp(self):
        """设置测试环境"""
        self.primary_source = CSVDataSource(data_path='data/sample_data.csv')
        self.manager = DataSourceManager(self.primary_source)

    def test_get_history(self):
        """测试通过管理器获取历史数据"""
        stocks = self.primary_source.get_stock_list()
        if stocks:
            history = self.manager.get_history(
                securities=stocks[:1],
                start_date='2023-01-01',
                end_date='2023-01-10'
            )
            self.assertIsInstance(history, dict)

    def test_get_source_status(self):
        """测试获取数据源状态"""
        status = self.manager.get_source_status()
        self.assertIsInstance(status, dict)
        self.assertIn('primary', status)


class TestDataSourceConfig(unittest.TestCase):
    """测试数据源配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = DataSourceConfig()
        self.assertEqual(config.get_default_source(), 'csv')

    def test_csv_config(self):
        """测试CSV配置"""
        config = DataSourceConfig()
        csv_config = config.get_source_config('csv')
        self.assertIsInstance(csv_config, dict)

    def test_config_validation(self):
        """测试配置验证"""
        config = DataSourceConfig()
        is_valid = config.validate()
        self.assertTrue(is_valid)


class TestBacktestEngineWithDataSources(unittest.TestCase):
    """测试回测引擎与数据源集成"""

    def test_csv_data_source_compatibility(self):
        """测试CSV数据源向后兼容性"""
        # 传统方式
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        self.assertIsNotNone(engine.data_source_manager)

    def test_new_api_csv_source(self):
        """测试新API的CSV数据源"""
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_source='csv',
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=1000000.0,
            securities=['STOCK_A']
        )
        self.assertIsNotNone(engine.data_source_manager)

    def test_custom_data_source(self):
        """测试自定义数据源对象"""
        custom_source = CSVDataSource(data_path='data/sample_data.csv')
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_source=custom_source,
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        self.assertIsNotNone(engine.data_source_manager)


if __name__ == '__main__':
    unittest.main(verbosity=2)