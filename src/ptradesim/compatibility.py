# -*- coding: utf-8 -*-
"""
ptrade API版本兼容性处理模块
处理不同版本ptrade API之间的差异，特别是委托状态字段类型差异
"""
from enum import Enum
from .logger import log


class PtradeVersion(Enum):
    """ptrade版本枚举"""
    V005 = "V005"
    V016 = "V016" 
    V041 = "V041"


class OrderStatusCompat:
    """委托状态兼容性处理类"""
    
    # 不同版本的状态映射
    STATUS_MAPPING = {
        # V005版本 - 使用整数状态码
        PtradeVersion.V005: {
            'new': 0,
            'open': 1,
            'filled': 2,
            'cancelled': 3,
            'rejected': 4,
            # 反向映射
            0: 'new',
            1: 'open', 
            2: 'filled',
            3: 'cancelled',
            4: 'rejected'
        },
        
        # V016版本 - 使用字符串状态
        PtradeVersion.V016: {
            'new': 'new',
            'open': 'open',
            'filled': 'filled', 
            'cancelled': 'cancelled',
            'rejected': 'rejected'
        },
        
        # V041版本 - 使用字符串状态（与V016相同）
        PtradeVersion.V041: {
            'new': 'new',
            'open': 'open',
            'filled': 'filled',
            'cancelled': 'cancelled', 
            'rejected': 'rejected'
        }
    }
    
    def __init__(self, version=PtradeVersion.V041):
        """
        初始化兼容性处理器
        
        Args:
            version: ptrade版本，默认V041
        """
        self.version = version
        self.mapping = self.STATUS_MAPPING[version]
        log.info(f"初始化ptrade兼容性处理器，版本: {version.value}")
    
    def to_external_status(self, internal_status):
        """
        将内部状态转换为外部API格式
        
        Args:
            internal_status: 内部状态（字符串）
            
        Returns:
            外部API格式的状态（int或str，取决于版本）
        """
        if isinstance(internal_status, str):
            return self.mapping.get(internal_status, internal_status)
        return internal_status
    
    def from_external_status(self, external_status):
        """
        将外部API状态转换为内部格式
        
        Args:
            external_status: 外部状态（int或str）
            
        Returns:
            内部状态（字符串）
        """
        if self.version == PtradeVersion.V005:
            # V005版本使用整数，需要转换为字符串
            if isinstance(external_status, int):
                return self.mapping.get(external_status, 'unknown')
            elif isinstance(external_status, str):
                # 如果传入的是字符串，先转换为整数再转回字符串
                for k, v in self.mapping.items():
                    if isinstance(k, str) and k == external_status:
                        return external_status
                return 'unknown'
        else:
            # V016和V041版本直接使用字符串
            return external_status if isinstance(external_status, str) else 'unknown'
    
    def get_status_list(self, status_type='all'):
        """
        获取状态列表
        
        Args:
            status_type: 状态类型 ('all', 'open', 'closed')
            
        Returns:
            list: 状态列表
        """
        if status_type == 'open':
            # 未完成状态
            return [self.to_external_status('new'), self.to_external_status('open')]
        elif status_type == 'closed':
            # 已完成状态
            return [self.to_external_status('filled'), 
                   self.to_external_status('cancelled'), 
                   self.to_external_status('rejected')]
        else:
            # 所有状态
            return [self.to_external_status(status) for status in 
                   ['new', 'open', 'filled', 'cancelled', 'rejected']]
    
    def is_open_status(self, status):
        """
        判断是否为未完成状态
        
        Args:
            status: 状态值（int或str）
            
        Returns:
            bool: 是否为未完成状态
        """
        internal_status = self.from_external_status(status)
        return internal_status in ['new', 'open']
    
    def is_filled_status(self, status):
        """
        判断是否为已成交状态
        
        Args:
            status: 状态值（int或str）
            
        Returns:
            bool: 是否为已成交状态
        """
        internal_status = self.from_external_status(status)
        return internal_status == 'filled'
    
    def is_cancelled_status(self, status):
        """
        判断是否为已撤销状态
        
        Args:
            status: 状态值（int或str）
            
        Returns:
            bool: 是否为已撤销状态
        """
        internal_status = self.from_external_status(status)
        return internal_status == 'cancelled'


# 全局兼容性处理器实例
_compat_handler = None


def set_ptrade_version(version):
    """
    设置ptrade版本
    
    Args:
        version: ptrade版本（PtradeVersion枚举或字符串）
    """
    global _compat_handler
    
    if isinstance(version, str):
        try:
            version = PtradeVersion(version.upper())
        except ValueError:
            log.warning(f"不支持的ptrade版本: {version}，使用默认版本V041")
            version = PtradeVersion.V041
    
    _compat_handler = OrderStatusCompat(version)
    log.info(f"设置ptrade版本为: {version.value}")


def get_compat_handler():
    """
    获取兼容性处理器
    
    Returns:
        OrderStatusCompat: 兼容性处理器实例
    """
    global _compat_handler
    if _compat_handler is None:
        _compat_handler = OrderStatusCompat()  # 默认V041版本
    return _compat_handler


def convert_order_status(status, to_external=True):
    """
    转换订单状态格式
    
    Args:
        status: 状态值
        to_external: True表示转换为外部格式，False表示转换为内部格式
        
    Returns:
        转换后的状态值
    """
    handler = get_compat_handler()
    if to_external:
        return handler.to_external_status(status)
    else:
        return handler.from_external_status(status)


def get_version_info():
    """
    获取当前版本信息
    
    Returns:
        dict: 版本信息字典
    """
    handler = get_compat_handler()
    return {
        'version': handler.version.value,
        'status_type': 'integer' if handler.version == PtradeVersion.V005 else 'string',
        'supported_statuses': handler.get_status_list(),
        'open_statuses': handler.get_status_list('open'),
        'closed_statuses': handler.get_status_list('closed')
    }


def validate_order_status(status):
    """
    验证订单状态是否有效
    
    Args:
        status: 状态值
        
    Returns:
        bool: 是否为有效状态
    """
    handler = get_compat_handler()
    internal_status = handler.from_external_status(status)
    return internal_status in ['new', 'open', 'filled', 'cancelled', 'rejected']
