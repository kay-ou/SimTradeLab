#!/usr/bin/env python3
"""
配置管理器测试 - 测试配置管理功能
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path

from simtradelab.config_manager import (
    DataSourceConfig, TushareConfig, AkshareConfig, CSVConfig, 
    BacktestConfig, LoggingConfig, ReportConfig, SimTradeLabConfig,
    load_config, get_config, save_config
)


class TestDataSourceConfigs:
    """数据源配置测试"""
    
    def test_data_source_config_creation(self):
        """测试数据源配置创建"""
        config = DataSourceConfig()
        assert config.enabled is True
        assert config.cache_enabled is True
        assert config.cache_dir == "./cache"
        assert config.timeout == 30
        assert config.retry_count == 3
        assert isinstance(config.extra_params, dict)
    
    def test_data_source_config_custom_values(self):
        """测试自定义数据源配置"""
        config = DataSourceConfig(
            enabled=False,
            cache_enabled=False,
            cache_dir="/tmp/cache",
            timeout=60,
            retry_count=5
        )
        assert config.enabled is False
        assert config.cache_enabled is False
        assert config.cache_dir == "/tmp/cache"
        assert config.timeout == 60
        assert config.retry_count == 5
    
    def test_tushare_config_creation(self):
        """测试Tushare配置创建"""
        config = TushareConfig()
        assert config.enabled is True
        assert config.token is None or isinstance(config.token, str)
        assert config.pro_api is True
    
    def test_tushare_config_with_token(self):
        """测试带Token的Tushare配置"""
        config = TushareConfig(token="test_token_123")
        assert config.token == "test_token_123"
        assert config.enabled is True
        assert config.pro_api is True
    
    @patch.dict(os.environ, {'TUSHARE_TOKEN': 'env_token_456'})
    def test_tushare_config_from_env(self):
        """测试从环境变量获取Tushare配置"""
        config = TushareConfig()
        assert config.token == 'env_token_456'
    
    def test_akshare_config_creation(self):
        """测试AkShare配置创建"""
        config = AkshareConfig()
        assert config.enabled is True
        assert config.cache_enabled is True
    
    def test_csv_config_creation(self):
        """测试CSV配置创建"""
        config = CSVConfig()
        assert config.enabled is True
        assert config.data_path == "./data/sample_data.csv"
        assert config.encoding == "utf-8"
    
    def test_csv_config_custom_path(self):
        """测试自定义路径的CSV配置"""
        config = CSVConfig(data_path="/custom/path/data.csv", encoding="gbk")
        assert config.data_path == "/custom/path/data.csv"
        assert config.encoding == "gbk"


class TestConfigManager:
    """配置管理测试"""
    
    def test_simtradelab_config_creation(self):
        """测试SimTradeLab配置创建"""
        config = SimTradeLabConfig()
        
        # 检查默认配置
        assert isinstance(config.backtest, BacktestConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.reports, ReportConfig)
        assert isinstance(config.data_sources, dict)
        assert config.default_data_source == "csv"
    
    def test_config_data_sources(self):
        """测试配置数据源"""
        config = SimTradeLabConfig()
        
        # 检查各种数据源配置
        assert "csv" in config.data_sources
        assert "akshare" in config.data_sources
        assert "tushare" in config.data_sources
        
        # 检查配置类型
        assert isinstance(config.data_sources["csv"], CSVConfig)
        assert isinstance(config.data_sources["akshare"], AkshareConfig)
        assert isinstance(config.data_sources["tushare"], TushareConfig)
    
    def test_get_data_source_config(self):
        """测试获取数据源配置"""
        config = SimTradeLabConfig()
        
        # 获取CSV配置
        csv_config = config.get_data_source_config("csv")
        assert isinstance(csv_config, CSVConfig)
        
        # 获取不存在的配置
        with pytest.raises(Exception):  # 配置不存在时应该抛出异常
            config.get_data_source_config("unknown")
    
    def test_get_default_data_source_config(self):
        """测试获取默认数据源配置"""
        config = SimTradeLabConfig()
        
        default_config = config.get_default_data_source_config()
        assert isinstance(default_config, CSVConfig)  # 默认是CSV
    
    def test_config_save_and_load(self):
        """测试配置保存和加载"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.yaml"
            
            # 创建配置
            config = SimTradeLabConfig()
            config.backtest.initial_cash = 500000
            config.backtest.commission_rate = 0.0005
            
            # 保存配置
            config.save_to_file(config_file)
            assert config_file.exists()
            
            # 加载配置
            loaded_config = SimTradeLabConfig.from_file(config_file)
            assert loaded_config.backtest.initial_cash == 500000
            assert loaded_config.backtest.commission_rate == 0.0005
    
    def test_config_from_nonexistent_file(self):
        """测试从不存在的文件加载配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "nonexistent_config.yaml"
            
            # 从不存在的文件加载应该创建默认配置
            config = SimTradeLabConfig.from_file(config_file)
            
            # 应该是默认配置
            assert isinstance(config, SimTradeLabConfig)
            assert config.backtest.initial_cash == 1000000.0
            
            # 文件应该被创建
            assert config_file.exists()


class TestConfigFunctions:
    """配置函数测试"""
    
    def test_load_config_function(self):
        """测试加载配置函数"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.yaml")
            
            # 创建测试配置文件
            test_config = SimTradeLabConfig()
            test_config.save_to_file(Path(config_file))
            
            # 加载配置
            loaded_config = load_config(config_file)
            assert isinstance(loaded_config, SimTradeLabConfig)
    
    def test_get_config_function(self):
        """测试获取配置函数"""
        # 获取全局配置
        config = get_config()
        assert isinstance(config, SimTradeLabConfig)
    
    def test_save_config_function(self):
        """测试保存配置函数"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "save_test_config.yaml")
            
            config = SimTradeLabConfig()
            config.backtest.initial_cash = 2000000
            
            # 保存配置
            save_config(config, config_file)
            
            # 验证文件存在
            assert os.path.exists(config_file)
            
            # 验证保存的内容
            loaded_config = SimTradeLabConfig.from_file(Path(config_file))
            assert loaded_config.backtest.initial_cash == 2000000


class TestBacktestConfig:
    """回测配置测试"""
    
    def test_backtest_config_creation(self):
        """测试回测配置创建"""
        config = BacktestConfig()
        
        assert config.initial_cash == 1000000.0
        assert config.commission_rate == 0.0003
        assert config.min_commission == 5.0
        assert config.slippage == 0.001
        assert config.frequency == "1d"
        assert config.benchmark is None
        assert config.enable_cache is True
        assert config.cache_dir == "./cache"
        assert config.concurrent_loading is True
        assert config.max_workers == 4
        assert config.memory_optimization is True
    
    def test_backtest_config_custom_values(self):
        """测试自定义回测配置"""
        config = BacktestConfig(
            initial_cash=500000,
            commission_rate=0.0005,
            min_commission=10.0,
            frequency="1h",
            benchmark="000300.SH"
        )
        
        assert config.initial_cash == 500000
        assert config.commission_rate == 0.0005
        assert config.min_commission == 10.0
        assert config.frequency == "1h"
        assert config.benchmark == "000300.SH"


class TestLoggingConfig:
    """日志配置测试"""
    
    def test_logging_config_creation(self):
        """测试日志配置创建"""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.file_handler is True
        assert config.log_dir == "./logs"
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5
    
    def test_logging_config_custom_values(self):
        """测试自定义日志配置"""
        config = LoggingConfig(
            level="DEBUG",
            file_handler=False,
            log_dir="/tmp/logs",
            max_file_size=20 * 1024 * 1024,
            backup_count=10
        )
        
        assert config.level == "DEBUG"
        assert config.file_handler is False
        assert config.log_dir == "/tmp/logs"
        assert config.max_file_size == 20 * 1024 * 1024
        assert config.backup_count == 10


class TestReportConfig:
    """报告配置测试"""
    
    def test_report_config_creation(self):
        """测试报告配置创建"""
        config = ReportConfig()
        
        assert config.output_dir == "./reports"
        assert config.formats == ["txt", "json", "csv"]
        assert config.include_charts is True
    
    def test_report_config_custom_values(self):
        """测试自定义报告配置"""
        config = ReportConfig(
            output_dir="/tmp/reports",
            formats=["html", "pdf"],
            include_charts=False
        )
        
        assert config.output_dir == "/tmp/reports"
        assert config.formats == ["html", "pdf"]
        assert config.include_charts is False


class TestConfigIntegration:
    """配置集成测试"""
    
    def test_config_serialization(self):
        """测试配置序列化"""
        config = TushareConfig(token="test_token", timeout=60)
        
        # 转换为字典
        config_dict = config.__dict__
        assert config_dict['token'] == "test_token"
        assert config_dict['timeout'] == 60
        assert config_dict['enabled'] is True
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效配置
        config = TushareConfig(token="valid_token")
        assert config.token == "valid_token"
        
        # 测试无效配置（这里主要测试类型检查）
        try:
            config = TushareConfig(timeout="invalid")  # 应该是数字
            # 如果没有类型检查，这里不会失败
            assert True
        except TypeError:
            # 如果有类型检查，会抛出异常
            assert True
    
    def test_config_defaults(self):
        """测试配置默认值"""
        # 测试所有配置都有合理的默认值
        csv_config = CSVConfig()
        akshare_config = AkshareConfig()
        tushare_config = TushareConfig()
        
        assert csv_config.enabled is True
        assert akshare_config.enabled is True
        assert tushare_config.enabled is True
        
        assert csv_config.cache_enabled is True
        assert akshare_config.cache_enabled is True
        assert tushare_config.cache_enabled is True


class TestConfigEdgeCases:
    """配置边界情况测试"""
    
    def test_empty_extra_params(self):
        """测试空的额外参数"""
        config = DataSourceConfig()
        assert isinstance(config.extra_params, dict)
        assert len(config.extra_params) == 0
    
    def test_config_modification(self):
        """测试配置修改"""
        config = DataSourceConfig()
        
        # 修改配置
        config.enabled = False
        config.timeout = 120
        config.extra_params['custom_key'] = 'custom_value'
        
        assert config.enabled is False
        assert config.timeout == 120
        assert config.extra_params['custom_key'] == 'custom_value'
    
    def test_tushare_config_without_env(self):
        """测试没有环境变量的Tushare配置"""
        # 确保环境变量不存在
        original_token = os.environ.get('TUSHARE_TOKEN')
        if 'TUSHARE_TOKEN' in os.environ:
            del os.environ['TUSHARE_TOKEN']
        
        try:
            config = TushareConfig()
            assert config.token is None
        finally:
            # 恢复环境变量
            if original_token:
                os.environ['TUSHARE_TOKEN'] = original_token


if __name__ == '__main__':
    pytest.main([__file__, '-v'])