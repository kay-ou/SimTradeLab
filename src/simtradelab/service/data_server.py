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
from typing import Tuple, Dict
from ..ptrade.object import LazyDataDict


def load_data_from_hdf5(data_path: str, required_data=None) -> Tuple[
    pd.HDFStore, pd.HDFStore,
    LazyDataDict, LazyDataDict, LazyDataDict, LazyDataDict,
    Dict, pd.DataFrame, Dict, Dict, object, Dict
]:
    """从HDF5文件加载所有数据（可复用的加载函数）

    Args:
        data_path: 数据目录路径
        required_data: 需要加载的数据集合,可选值:{'price','valuation','fundamentals','exrights'}
                      None表示加载全部

    Returns:
        元组包含: (
            stock_data_store, fundamentals_store,
            stock_data_dict, valuation_dict, fundamentals_dict, exrights_dict,
            benchmark_data, stock_metadata, index_constituents, stock_status_history,
            adj_pre_cache
        )
    """
    # 默认加载全部
    if required_data is None:
        required_data = {'price', 'valuation', 'fundamentals', 'exrights'}

    print("正在打开数据文件...")

    stock_data_store = pd.HDFStore('{}/ptrade_data.h5'.format(data_path), 'r')
    fundamentals_store = pd.HDFStore('{}/ptrade_fundamentals.h5'.format(data_path), 'r')

    # 导入配置(统一在开头)
    from simtradelab.ptrade.config_manager import config

    # 只在需要时读取stock keys（这一步很慢，4-5秒）
    if 'price' in required_data:
        print("正在读取数据索引...")
        all_stock_keys = [k.split('/')[-1] for k in stock_data_store.keys() if k.startswith('/stock_data/')]
    else:
        all_stock_keys = []  # 不需要price数据时跳过读取keys

    # 股票价格数据
    if 'price' in required_data:
        print("\n[1] 股票价格（{}只）...".format(len(all_stock_keys)))
        stock_data_dict = LazyDataDict(stock_data_store, '/stock_data/', all_stock_keys, preload=True)
    else:
        print("\n[1] 股票价格（跳过）")
        stock_data_dict = LazyDataDict(stock_data_store, '/stock_data/', [], preload=False)

    # 估值数据
    if 'valuation' in required_data:
        valuation_keys = [k.split('/')[-1] for k in fundamentals_store.keys() if k.startswith('/valuation/')]
        print("[2] 估值数据（{}只）...".format(len(valuation_keys)))
        valuation_dict = LazyDataDict(fundamentals_store, '/valuation/', valuation_keys, preload=True)
    else:
        print("[2] 估值数据（跳过）")
        valuation_dict = LazyDataDict(fundamentals_store, '/valuation/', [], preload=False)

    # 财务数据
    if 'fundamentals' in required_data:
        fundamentals_keys = [k.split('/')[-1] for k in fundamentals_store.keys() if k.startswith('/fundamentals/')]
        print("[3] 财务数据（{}只，延迟加载）...".format(len(fundamentals_keys)))
        fundamentals_dict = LazyDataDict(fundamentals_store, '/fundamentals/', fundamentals_keys,
                                         max_cache_size=config.cache.fundamentals_cache_size)
    else:
        print("[3] 财务数据（跳过）")
        fundamentals_dict = LazyDataDict(fundamentals_store, '/fundamentals/', [], preload=False)

    # 除权数据
    if 'exrights' in required_data:
        exrights_keys = [k.split('/')[-1] for k in stock_data_store.keys() if k.startswith('/exrights/')]
        print("[4] 除权数据（{}只，延迟加载）...".format(len(exrights_keys)))
        exrights_dict = LazyDataDict(stock_data_store, '/exrights/', exrights_keys,
                                    max_cache_size=config.cache.exrights_cache_size)
    else:
        print("[4] 除权数据（跳过）")
        exrights_dict = LazyDataDict(stock_data_store, '/exrights/', [], preload=False)

    print("\n已加载: {}".format(' | '.join(sorted(required_data))))
    print("")

    # 加载元数据和基准
    stock_metadata = stock_data_store['/stock_metadata']
    benchmark_df = stock_data_store['/benchmark']
    metadata = stock_data_store['/metadata']

    index_constituents = {}
    stock_status_history = {}
    if 'index_constituents' in metadata.index and pd.notna(metadata['index_constituents']): # type: ignore
        index_constituents = json.loads(metadata['index_constituents']) # type: ignore
    if 'stock_status_history' in metadata.index and pd.notna(metadata['stock_status_history']): # type: ignore
        stock_status_history = json.loads(metadata['stock_status_history']) # type: ignore

    # 构建benchmark_data字典，包含常用指数
    benchmark_data = {
        '000300.SS': benchmark_df,  # 沪深300（默认）
    }

    # 从stock_data中添加常见指数作为可选基准
    common_indices = ['000001.SZ', '000905.SZ', '399001.SZ', '399006.SZ']
    for index_code in common_indices:
        if index_code in stock_data_dict:
            benchmark_data[index_code] = stock_data_dict[index_code]

    print(f"可用基准: {', '.join(benchmark_data.keys())}")

    # 只有需要价格或除权数据时才加载复权缓存
    adj_pre_cache = None
    dividend_cache = None

    if 'price' in required_data or 'exrights' in required_data:
        from ..ptrade.adj_pre_cache import load_adj_pre_cache, create_dividend_cache
        from ..ptrade.data_context import DataContext
        temp_context = DataContext(
            stock_data_dict=stock_data_dict,
            valuation_dict=valuation_dict,
            fundamentals_dict=fundamentals_dict,
            exrights_dict=exrights_dict,
            benchmark_data=benchmark_data,
            stock_metadata=stock_metadata,
            stock_data_store=stock_data_store,
            fundamentals_store=fundamentals_store,
            index_constituents=index_constituents,
            stock_status_history=stock_status_history,
            adj_pre_cache=None
        )
        adj_pre_cache = load_adj_pre_cache(temp_context)
        dividend_cache = create_dividend_cache(temp_context)

    print("✓ 数据加载完成\n")

    return (
        stock_data_store, fundamentals_store,
        stock_data_dict, valuation_dict, fundamentals_dict, exrights_dict,
        benchmark_data, stock_metadata, index_constituents, stock_status_history,
        adj_pre_cache, dividend_cache
    )


class DataServer:
    """数据服务器单例"""
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data_path=None, required_data=None):
        # 只初始化一次基础结构
        if DataServer._initialized:
            print("使用已加载的数据（常驻内存）")
            # 如果指定了新的数据需求,动态补充加载
            if required_data is not None:
                self._ensure_data_loaded(required_data)
            return

        # 使用统一路径管理
        if data_path is None:
            from ..paths import DATA_PATH
            data_path = str(DATA_PATH)

        print("=" * 70)
        print("首次加载 - 在jupyter notebook中数据将常驻内存")
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
        self.adj_pre_cache = None

        self.index_constituents = {}
        self.stock_status_history = {}

        # 记录已加载的数据类型
        self._loaded_data_types = set()

        # 加载数据
        self._load_data(required_data)

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

    def _load_data(self, required_data=None):
        """加载HDF5数据文件

        Args:
            required_data: 需要加载的数据集合,None表示全部加载
        """
        # 默认加载全部
        if required_data is None:
            required_data = {'price', 'valuation', 'fundamentals', 'exrights'}

        # 记录需要加载的数据类型
        self._loaded_data_types = required_data

        (
            self.stock_data_store, self.fundamentals_store,
            self.stock_data_dict, self.valuation_dict, self.fundamentals_dict, self.exrights_dict,
            self.benchmark_data, self.stock_metadata, self.index_constituents, self.stock_status_history,
            self.adj_pre_cache, self.dividend_cache
        ) = load_data_from_hdf5(self.data_path, required_data)

    def _ensure_data_loaded(self, required_data):
        """确保所需数据已加载,动态补充缺失的数据

        Args:
            required_data: 需要的数据集合
        """
        if not hasattr(self, '_loaded_data_types'):
            self._loaded_data_types = set()

        # 计算缺失的数据类型
        missing = set(required_data) - self._loaded_data_types
        if not missing:
            return

        print("补充加载缺失数据: {}".format(', '.join(sorted(missing))))

        # 导入配置
        from simtradelab.ptrade.config_manager import config

        # 只加载缺失的数据
        if 'price' in missing:
            all_stock_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/stock_data/')]
            print("  加载股票价格（{}只）...".format(len(all_stock_keys)))
            self.stock_data_dict = LazyDataDict(self.stock_data_store, '/stock_data/', all_stock_keys, preload=True)

        if 'valuation' in missing:
            valuation_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/valuation/')]
            print("  加载估值数据（{}只）...".format(len(valuation_keys)))
            self.valuation_dict = LazyDataDict(self.fundamentals_store, '/valuation/', valuation_keys, preload=True)

        if 'fundamentals' in missing:
            fundamentals_keys = [k.split('/')[-1] for k in self.fundamentals_store.keys() if k.startswith('/fundamentals/')]
            print("  加载财务数据（{}只，延迟加载）...".format(len(fundamentals_keys)))
            self.fundamentals_dict = LazyDataDict(self.fundamentals_store, '/fundamentals/', fundamentals_keys,
                                                 max_cache_size=config.cache.fundamentals_cache_size)

        if 'exrights' in missing:
            exrights_keys = [k.split('/')[-1] for k in self.stock_data_store.keys() if k.startswith('/exrights/')]
            print("  加载除权数据（{}只，延迟加载）...".format(len(exrights_keys)))
            self.exrights_dict = LazyDataDict(self.stock_data_store, '/exrights/', exrights_keys,
                                            max_cache_size=config.cache.exrights_cache_size)

        # 更新已加载记录
        self._loaded_data_types.update(missing)

    def get_benchmark_data(self):
        """获取基准数据"""
        return self.benchmark_data['000300.SS'] # type: ignore

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
