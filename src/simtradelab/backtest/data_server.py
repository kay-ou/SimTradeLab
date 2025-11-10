# -*- coding: utf-8 -*-
"""
数据服务器 - 支持数据常驻内存，多次运行策略无需重新加载

使用方式：
1. 首次运行时自动加载数据并缓存到单例
2. 后续运行直接使用缓存的数据
3. 进程结束时自动释放资源
"""

import pandas as pd
import json
import atexit
from backtest_core import LazyDataDict


class DataServer:
    """数据服务器单例"""
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data_path='/home/kay/dev/ptrade/data'):
        # 只初始化一次
        if DataServer._initialized:
            print("使用已加载的数据（常驻内存）")
            return

        print("=" * 70)
        print("首次加载 - 数据将常驻内存")
        print("=" * 70)

        self.data_path = data_path
        self.stock_data_store = None
        self.fundamentals_store = None

        self.stock_data_dict = None
        self.valuation_dict = None
        self.fundamentals_dict = None
        self.exrights_dict = None
        self.benchmark_data = None
        self.stock_metadata = None

        self.index_constituents = {}
        self.stock_status_history = {}

        # 加载数据
        self._load_data()

        # 注册清理函数：进程退出时自动关闭文件
        atexit.register(self._cleanup_on_exit)

        DataServer._initialized = True

    def _cleanup_on_exit(self):
        """进程退出时清理资源"""
        try:
            if self.stock_data_store is not None:
                self.stock_data_store.close()
            if self.fundamentals_store is not None:
                self.fundamentals_store.close()
        except:
            pass

    def _load_data(self):
        """加载HDF5数据文件"""
        print("正在加载数据文件...")

        self.stock_data_store = pd.HDFStore(f'{self.data_path}/ptrade_data.h5', 'r')
        self.fundamentals_store = pd.HDFStore(f'{self.data_path}/ptrade_fundamentals.h5', 'r')

        # 提取所有表的键名
        all_stock_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/stock_data/')]
        valuation_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/valuation/')]
        fundamentals_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/fundamentals/')]
        exrights_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/exrights/')]

        # 构建数据字典（基本面预加载，价格数据延迟加载）
        print("预加载基本面数据...")
        self.stock_data_dict = LazyDataDict(self.stock_data_store, '/stock_data/', all_stock_keys, max_cache_size=2000)
        self.valuation_dict = LazyDataDict(self.fundamentals_store, '/valuation/', valuation_keys, preload=True)
        self.fundamentals_dict = LazyDataDict(self.fundamentals_store, '/fundamentals/', fundamentals_keys, preload=True)
        self.exrights_dict = LazyDataDict(self.stock_data_store, '/exrights/', exrights_keys, max_cache_size=800)

        print(f"✓ 股票数据: {len(all_stock_keys)} 只")
        print(f"✓ 基本面数据: {len(valuation_keys)} 只")
        print(f"✓ 除权数据: {len(exrights_keys)} 只")

        # 加载元数据和基准
        self.stock_metadata = self.stock_data_store['/stock_metadata']
        benchmark_df = self.stock_data_store['/benchmark']
        metadata = self.stock_data_store['/metadata']

        if 'index_constituents' in metadata.index and pd.notna(metadata['index_constituents']):
            self.index_constituents = json.loads(metadata['index_constituents'])
        if 'stock_status_history' in metadata.index and pd.notna(metadata['stock_status_history']):
            self.stock_status_history = json.loads(metadata['stock_status_history'])

        self.benchmark_data = {'000300.SS': benchmark_df}
        print("✓ 数据加载完成\n")

    def get_benchmark_data(self):
        """获取基准数据"""
        return self.benchmark_data['000300.SS']

    @classmethod
    def shutdown(cls):
        """关闭数据服务器，释放所有资源"""
        if cls._instance is None:
            print("数据服务器未启动")
            return

        print("正在关闭数据服务器...")

        # 关闭HDF5文件
        if cls._instance.stock_data_store is not None:
            try:
                cls._instance.stock_data_store.close()
                print("  ✓ 关闭股票数据文件")
            except:
                pass

        if cls._instance.fundamentals_store is not None:
            try:
                cls._instance.fundamentals_store.close()
                print("  ✓ 关闭基本面数据文件")
            except:
                pass

        # 清空缓存
        if cls._instance.stock_data_dict is not None:
            cls._instance.stock_data_dict.clear_cache()
        if cls._instance.exrights_dict is not None:
            cls._instance.exrights_dict.clear_cache()

        # 重置单例
        cls._instance = None
        cls._initialized = False
        print("✓ 数据服务器已关闭，内存已释放\n")

    @classmethod
    def reset(cls):
        """重置单例（强制重新加载）"""
        cls.shutdown()
        print("下次运行将重新加载数据\n")

    @classmethod
    def status(cls):
        """显示数据服务器状态"""
        if cls._instance is None or not cls._initialized:
            print("数据服务器状态: 未启动")
            return

        print("数据服务器状态: 运行中")
        if cls._instance.stock_data_dict is not None:
            print(f"  - 股票数据: {len(cls._instance.stock_data_dict._all_keys)} 只")
            print(f"  - 缓存数据: {len(cls._instance.stock_data_dict._cache)} 只")
        if cls._instance.exrights_dict is not None:
            print(f"  - 除权数据缓存: {len(cls._instance.exrights_dict._cache)} 只")
        if cls._instance.valuation_dict is not None:
            print(f"  - 内存模式: {'预加载' if cls._instance.valuation_dict._preload else '延迟加载'}")

    def __del__(self):
        """析构时关闭文件句柄"""
        try:
            if self.stock_data_store is not None:
                self.stock_data_store.close()
            if self.fundamentals_store is not None:
                self.fundamentals_store.close()
        except:
            pass
