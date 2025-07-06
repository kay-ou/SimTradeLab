# -*- coding: utf-8 -*-
"""
SimTradeLab 配置管理系统

提供现代化的配置管理功能，支持数据源配置、回测参数配置等。
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import json
import yaml
from .exceptions import ConfigurationError
from .logger import log


@dataclass
class DataSourceConfig:
    """数据源配置"""
    enabled: bool = True
    cache_enabled: bool = True
    cache_dir: str = "./cache"
    timeout: int = 30
    retry_count: int = 3
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TushareConfig(DataSourceConfig):
    """Tushare数据源配置"""
    token: Optional[str] = None
    pro_api: bool = True
    
    def __post_init__(self):
        if self.enabled and not self.token:
            # 尝试从环境变量获取
            self.token = os.getenv('TUSHARE_TOKEN')


@dataclass
class AkshareConfig(DataSourceConfig):
    """AkShare数据源配置"""
    pass


@dataclass
class CSVConfig(DataSourceConfig):
    """CSV数据源配置"""
    data_path: str = "./data/sample_data.csv"
    encoding: str = "utf-8"
    date_column: str = "date"
    

@dataclass
class BacktestConfig:
    """回测配置"""
    initial_cash: float = 1000000.0
    commission_rate: float = 0.0003
    min_commission: float = 5.0
    slippage: float = 0.001
    frequency: str = "1d"
    benchmark: Optional[str] = None
    
    # 性能优化相关
    enable_cache: bool = True
    cache_dir: str = "./cache"
    concurrent_loading: bool = True
    max_workers: int = 4
    memory_optimization: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_handler: bool = True
    log_dir: str = "./logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class ReportConfig:
    """报告配置"""
    output_dir: str = "./reports"
    formats: List[str] = field(default_factory=lambda: ["txt", "json", "csv"])
    include_charts: bool = True


@dataclass
class SimTradeLabConfig:
    """SimTradeLab主配置"""
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    reports: ReportConfig = field(default_factory=ReportConfig)
    
    # 数据源配置
    data_sources: Dict[str, DataSourceConfig] = field(default_factory=lambda: {
        "csv": CSVConfig(),
        "tushare": TushareConfig(enabled=False),
        "akshare": AkshareConfig(enabled=True),
    })
    
    default_data_source: str = "csv"
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'SimTradeLabConfig':
        """从配置文件加载配置"""
        try:
            if not config_path.exists():
                # 创建默认配置文件
                default_config = cls()
                default_config.save_to_file(config_path)
                return default_config
                
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                return cls()
                
            # 解析配置数据
            config = cls()
            
            # 回测配置
            if 'backtest' in data:
                backtest_data = data['backtest']
                config.backtest = BacktestConfig(**backtest_data)
            
            # 日志配置
            if 'logging' in data:
                logging_data = data['logging']
                config.logging = LoggingConfig(**logging_data)
            
            # 报告配置
            if 'reports' in data:
                reports_data = data['reports']
                config.reports = ReportConfig(**reports_data)
            
            # 数据源配置
            if 'data_sources' in data:
                data_sources_data = data['data_sources']
                config.data_sources = {}
                
                for source_name, source_config in data_sources_data.items():
                    if source_name == "tushare":
                        config.data_sources[source_name] = TushareConfig(**source_config)
                    elif source_name == "akshare":
                        config.data_sources[source_name] = AkshareConfig(**source_config)
                    elif source_name == "csv":
                        config.data_sources[source_name] = CSVConfig(**source_config)
                    else:
                        config.data_sources[source_name] = DataSourceConfig(**source_config)
            
            # 默认数据源
            if 'default_data_source' in data:
                config.default_data_source = data['default_data_source']
                
            return config
            
        except Exception as e:
            raise ConfigurationError(f"加载配置文件失败: {str(e)}") from e
    
    def save_to_file(self, config_path: Path) -> None:
        """保存配置到文件"""
        try:
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为字典
            config_dict = {
                'backtest': {
                    'initial_cash': self.backtest.initial_cash,
                    'commission_rate': self.backtest.commission_rate,
                    'min_commission': self.backtest.min_commission,
                    'slippage': self.backtest.slippage,
                    'frequency': self.backtest.frequency,
                    'benchmark': self.backtest.benchmark,
                    'enable_cache': self.backtest.enable_cache,
                    'cache_dir': self.backtest.cache_dir,
                    'concurrent_loading': self.backtest.concurrent_loading,
                    'max_workers': self.backtest.max_workers,
                    'memory_optimization': self.backtest.memory_optimization,
                },
                'logging': {
                    'level': self.logging.level,
                    'format': self.logging.format,
                    'file_handler': self.logging.file_handler,
                    'log_dir': self.logging.log_dir,
                    'max_file_size': self.logging.max_file_size,
                    'backup_count': self.logging.backup_count,
                },
                'reports': {
                    'output_dir': self.reports.output_dir,
                    'formats': self.reports.formats,
                    'include_charts': self.reports.include_charts,
                },
                'data_sources': {},
                'default_data_source': self.default_data_source,
            }
            
            # 转换数据源配置
            for name, source_config in self.data_sources.items():
                if isinstance(source_config, TushareConfig):
                    config_dict['data_sources'][name] = {
                        'enabled': source_config.enabled,
                        'token': source_config.token,
                        'pro_api': source_config.pro_api,
                        'cache_enabled': source_config.cache_enabled,
                        'cache_dir': source_config.cache_dir,
                        'timeout': source_config.timeout,
                        'retry_count': source_config.retry_count,
                        'extra_params': source_config.extra_params,
                    }
                elif isinstance(source_config, CSVConfig):
                    config_dict['data_sources'][name] = {
                        'enabled': source_config.enabled,
                        'data_path': source_config.data_path,
                        'encoding': source_config.encoding,
                        'date_column': source_config.date_column,
                        'cache_enabled': source_config.cache_enabled,
                        'cache_dir': source_config.cache_dir,
                        'timeout': source_config.timeout,
                        'retry_count': source_config.retry_count,
                        'extra_params': source_config.extra_params,
                    }
                else:
                    config_dict['data_sources'][name] = {
                        'enabled': source_config.enabled,
                        'cache_enabled': source_config.cache_enabled,
                        'cache_dir': source_config.cache_dir,
                        'timeout': source_config.timeout,
                        'retry_count': source_config.retry_count,
                        'extra_params': source_config.extra_params,
                    }
            
            # 保存到文件
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            raise ConfigurationError(f"保存配置文件失败: {str(e)}") from e
    
    def get_data_source_config(self, source_name: str) -> DataSourceConfig:
        """获取数据源配置"""
        if source_name not in self.data_sources:
            raise ConfigurationError(f"未找到数据源配置: {source_name}")
        return self.data_sources[source_name]
    
    def get_default_data_source_config(self) -> DataSourceConfig:
        """获取默认数据源配置"""
        return self.get_data_source_config(self.default_data_source)


# 全局配置实例
_global_config: Optional[SimTradeLabConfig] = None


def load_config(config_path: Optional[str] = None) -> SimTradeLabConfig:
    """加载全局配置"""
    global _global_config
    
    if config_path is None:
        config_path = os.getenv('SIMTRADELAB_CONFIG', './simtradelab_config.yaml')
    
    config_file = Path(config_path)
    _global_config = SimTradeLabConfig.from_file(config_file)
    return _global_config


def get_config() -> SimTradeLabConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def save_config(config: SimTradeLabConfig, config_path: Optional[str] = None) -> None:
    """保存配置"""
    if config_path is None:
        config_path = os.getenv('SIMTRADELAB_CONFIG', './simtradelab_config.yaml')
    
    config_file = Path(config_path)
    config.save_to_file(config_file)