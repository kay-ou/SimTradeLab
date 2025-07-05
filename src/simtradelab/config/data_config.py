# -*- coding: utf-8 -*-
"""
数据源配置管理

提供数据源配置的加载、保存和管理功能
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from ..logger import log


class DataSourceConfig:
    """数据源配置类"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化配置
        
        Args:
            config_dict: 配置字典
        """
        self.config = config_dict or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'data_sources': {
                'default': 'csv',
                'csv': {
                    'data_path': './data/sample_data.csv'
                },
                'tushare': {
                    'token': '',
                    'cache_dir': './cache/tushare',
                    'cache_enabled': True
                },
                'akshare': {
                    'cache_dir': './cache/akshare', 
                    'cache_enabled': True
                }
            },
            'cache': {
                'enabled': True,
                'ttl': 3600,  # 缓存1小时
                'max_size': 1000  # 最大缓存条目数
            },
            'network': {
                'timeout': 30,  # 网络超时时间（秒）
                'retry_times': 3,  # 重试次数
                'retry_delay': 1  # 重试延迟（秒）
            }
        }
    
    def get_default_source(self) -> str:
        """获取默认数据源"""
        return self.config.get('data_sources', {}).get('default', 'csv')
    
    def set_default_source(self, source_name: str):
        """设置默认数据源"""
        if 'data_sources' not in self.config:
            self.config['data_sources'] = {}
        self.config['data_sources']['default'] = source_name
    
    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """获取指定数据源的配置"""
        return self.config.get('data_sources', {}).get(source_name, {})
    
    def set_source_config(self, source_name: str, config: Dict[str, Any]):
        """设置指定数据源的配置"""
        if 'data_sources' not in self.config:
            self.config['data_sources'] = {}
        self.config['data_sources'][source_name] = config
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.config.get('cache', {})
    
    def set_cache_config(self, config: Dict[str, Any]):
        """设置缓存配置"""
        self.config['cache'] = config
    
    def get_network_config(self) -> Dict[str, Any]:
        """获取网络配置"""
        return self.config.get('network', {})
    
    def set_network_config(self, config: Dict[str, Any]):
        """设置网络配置"""
        self.config['network'] = config
    
    def is_cache_enabled(self) -> bool:
        """检查是否启用缓存"""
        return self.config.get('cache', {}).get('enabled', True)
    
    def get_cache_ttl(self) -> int:
        """获取缓存TTL"""
        return self.config.get('cache', {}).get('ttl', 3600)
    
    def get_tushare_token(self) -> str:
        """获取Tushare token"""
        # 优先从环境变量获取
        token = os.getenv('TUSHARE_TOKEN')
        if token:
            return token
        
        # 从配置文件获取
        return self.get_source_config('tushare').get('token', '')
    
    def set_tushare_token(self, token: str):
        """设置Tushare token"""
        tushare_config = self.get_source_config('tushare')
        tushare_config['token'] = token
        self.set_source_config('tushare', tushare_config)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        try:
            # 检查必要的配置项
            if 'data_sources' not in self.config:
                log.warning("配置中缺少 data_sources 部分")
                return False
            
            default_source = self.get_default_source()
            if default_source not in self.config['data_sources']:
                log.warning(f"默认数据源 {default_source} 未在配置中定义")
                return False
            
            # 验证Tushare配置
            if 'tushare' in self.config['data_sources']:
                tushare_config = self.get_source_config('tushare')
                if not tushare_config.get('token') and not os.getenv('TUSHARE_TOKEN'):
                    log.warning("Tushare配置中缺少token，且环境变量TUSHARE_TOKEN未设置")
            
            return True
            
        except Exception as e:
            log.warning(f"配置验证失败: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.config.copy()
    
    def update(self, other_config: Dict[str, Any]):
        """更新配置"""
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, other_config)


def load_config(config_path: Optional[str] = None) -> DataSourceConfig:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认路径
        
    Returns:
        DataSourceConfig: 配置对象
    """
    if config_path is None:
        # 尝试多个默认路径
        possible_paths = [
            './simtradelab_config.yaml',
            './simtradelab_config.yml',
            './simtradelab_config.json',
            './config/simtradelab_config.yaml',
            './config/simtradelab_config.yml',
            './config/simtradelab_config.json'
        ]
        
        config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
    
    if config_path is None or not os.path.exists(config_path):
        log.info("未找到配置文件，使用默认配置")
        return DataSourceConfig()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                config_dict = json.load(f)
            else:  # yaml
                config_dict = yaml.safe_load(f)
        
        log.info(f"成功加载配置文件: {config_path}")
        return DataSourceConfig(config_dict)
        
    except Exception as e:
        log.warning(f"加载配置文件失败: {e}，使用默认配置")
        return DataSourceConfig()


def save_config(config: DataSourceConfig, config_path: str = './simtradelab_config.yaml'):
    """
    保存配置文件
    
    Args:
        config: 配置对象
        config_path: 配置文件路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            else:  # yaml
                yaml.dump(config.to_dict(), f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        
        log.info(f"配置文件保存成功: {config_path}")
        
    except Exception as e:
        log.warning(f"保存配置文件失败: {e}")


def create_sample_config(config_path: str = './simtradelab_config.yaml'):
    """
    创建示例配置文件
    
    Args:
        config_path: 配置文件路径
    """
    config = DataSourceConfig()
    
    # 添加一些示例配置
    config.set_tushare_token('your_tushare_token_here')
    
    # 添加注释信息（通过特殊键）
    config.config['_comments'] = {
        'data_sources': '数据源配置',
        'tushare_token': '请在 https://tushare.pro 注册并获取token',
        'cache': '缓存配置，可以提高数据获取速度',
        'network': '网络配置，用于控制API调用的超时和重试'
    }
    
    save_config(config, config_path)
    log.info(f"示例配置文件已创建: {config_path}")


# 尝试导入yaml，如果没有则使用json
try:
    import yaml
except ImportError:
    yaml = None
    log.warning("PyYAML未安装，配置文件将使用JSON格式。建议安装: pip install PyYAML")
