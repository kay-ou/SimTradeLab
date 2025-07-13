# -*- coding: utf-8 -*-
"""
数据源插件统一配置模型

基于Pydantic的数据源插件配置类，提供类型安全的配置验证。
修复E8: 配置系统缺乏统一验证问题。
"""

from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional, Set

from pydantic import Field, field_validator

from simtradelab.plugins.config.base_config import BasePluginConfig


class DataSourceConfig(BasePluginConfig):
    """数据源插件基础配置模型"""

    cache_timeout: int = Field(default=300, description="数据缓存超时时间（秒）", ge=0, le=3600)

    supported_markets: Set[str] = Field(default={"stock_cn"}, description="支持的市场类型")

    supported_frequencies: Set[str] = Field(default={"1d"}, description="支持的数据频率")

    data_delay: int = Field(default=0, description="数据延迟时间（秒）", ge=0, le=86400)

    @field_validator("cache_timeout")
    @classmethod
    def validate_cache_timeout(cls, v: int) -> int:
        """验证缓存超时时间"""
        if v < 0:
            raise ValueError("缓存超时时间不能为负数")
        return v


class CSVDataPluginConfig(DataSourceConfig):
    """CSV数据插件配置模型"""

    data_dir: Optional[Path] = Field(default=None, description="数据文件存储目录")

    auto_create_missing: bool = Field(default=True, description="是否自动创建缺失的数据文件")

    default_history_days: int = Field(
        default=365, description="默认生成历史数据天数", ge=30, le=3650
    )

    base_volatility: Decimal = Field(
        default=Decimal("0.02"), description="基础日波动率", ge=0, le=1
    )

    cleanup_old_data_days: int = Field(
        default=30, description="清理旧数据文件的保留天数", ge=1, le=365
    )

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, v: Optional[Path]) -> Optional[Path]:
        """验证数据目录"""
        if v is not None:
            if not isinstance(v, Path):
                v = Path(v)
        return v

    class Config:
        title = "CSV数据插件配置"
        description = "CSV格式数据源插件的配置选项"


class MockDataPluginConfig(DataSourceConfig):
    """Mock数据插件配置模型"""

    enabled: bool = Field(default=True, description="是否启用模拟数据插件")

    seed: int = Field(default=42, description="随机数种子，用于生成可重复的模拟数据", ge=0, le=2147483647)

    base_prices: Dict[str, float] = Field(
        default={
            "STOCK_A": 10.0,
            "000001.SZ": 15.0,
            "000002.SZ": 12.0,
            "600000.SH": 8.0,
            "600036.SH": 35.0,
        },
        description="各证券的基础价格配置",
    )

    volatility: Decimal = Field(default=Decimal("0.02"), description="日波动率", ge=0, le=1)

    trend: Decimal = Field(
        default=Decimal("0.0001"), description="趋势系数", ge=-0.01, le=0.01
    )

    daily_volatility_factor: Decimal = Field(
        default=Decimal("0.5"), description="日内波动率因子", ge=0.1, le=2
    )

    volume_range: Dict[str, int] = Field(
        default={"min": 1000, "max": 10000}, description="成交量范围配置"
    )

    @field_validator("base_prices")
    @classmethod
    def validate_base_prices(cls, v: Dict[str, float]) -> Dict[str, float]:
        """验证基础价格配置"""
        for security, price in v.items():
            if price <= 0:
                raise ValueError(f"证券 {security} 的基础价格必须大于0")
        return v

    @field_validator("volume_range")
    @classmethod
    def validate_volume_range(cls, v: Dict[str, int]) -> Dict[str, int]:
        """验证成交量范围"""
        if v.get("min", 0) >= v.get("max", 1):
            raise ValueError("最小成交量必须小于最大成交量")
        if v.get("min", 0) <= 0:
            raise ValueError("最小成交量必须大于0")
        return v

    class Config:
        title = "Mock数据插件配置"
        description = "模拟数据源插件的配置选项"


class ExternalDataSourceConfig(DataSourceConfig):
    """外部数据源配置模型（如数据库、API等）"""

    connection_string: Optional[str] = Field(default=None, description="外部数据源连接字符串")

    api_key: Optional[str] = Field(default=None, description="API密钥")

    api_base_url: Optional[str] = Field(default=None, description="API基础URL")

    timeout: int = Field(default=30, description="请求超时时间（秒）", ge=1, le=300)

    retry_count: int = Field(default=3, description="失败重试次数", ge=0, le=10)

    rate_limit: Optional[int] = Field(
        default=None, description="请求频率限制（每秒请求数）", ge=1, le=1000
    )

    enable_cache: bool = Field(default=True, description="是否启用请求缓存")

    class Config:
        title = "外部数据源配置"
        description = "外部数据源（数据库、API等）的配置选项"


class TDXDataSourceConfig(DataSourceConfig):
    """通达信数据源配置模型"""

    server_ip: str = Field(default="119.147.212.81", description="通达信服务器IP地址")

    server_port: int = Field(default=7709, description="通达信服务器端口", ge=1, le=65535)

    connect_timeout: int = Field(default=10, description="连接超时时间（秒）", ge=1, le=60)

    read_timeout: int = Field(default=30, description="读取超时时间（秒）", ge=1, le=300)

    max_retry: int = Field(default=3, description="最大重试次数", ge=0, le=10)

    enable_heartbeat: bool = Field(default=True, description="是否启用心跳保持连接")

    heartbeat_interval: int = Field(default=60, description="心跳间隔（秒）", ge=10, le=300)

    class Config:
        title = "通达信数据源配置"
        description = "通达信数据源插件的配置选项"


# 配置映射字典，用于插件自动配置模型选择
DATA_SOURCE_PLUGIN_CONFIG_MAPPING = {
    "CSVDataPlugin": CSVDataPluginConfig,
    "csv_data_plugin": CSVDataPluginConfig,
    "MockDataPlugin": MockDataPluginConfig,
    "mock_data_plugin": MockDataPluginConfig,
    "ExternalDataSource": ExternalDataSourceConfig,
    "TDXDataSource": TDXDataSourceConfig,
}


def get_config_model_for_data_plugin(plugin_name: str) -> type:
    """
    根据数据插件名称获取对应的配置模型类

    Args:
        plugin_name: 插件名称

    Returns:
        配置模型类，如果未找到则返回基础配置类
    """
    return DATA_SOURCE_PLUGIN_CONFIG_MAPPING.get(plugin_name, DataSourceConfig)
