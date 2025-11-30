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
from ..ptrade.object import LazyDataDict
from ..utils.paths import DATA_PATH


class DataServer:
    """数据服务器单例"""
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, required_data=None):
        # 只初始化一次基础结构
        if DataServer._initialized:
            print("使用已加载的数据（常驻内存）")
            # 如果指定了新的数据需求,动态补充加载
            if required_data is not None:
                self._ensure_data_loaded(required_data)
            return

        print("=" * 70)
        print("首次加载 - 在jupyter notebook中数据将常驻内存")
        print("=" * 70)

        self.data_path = str(DATA_PATH)
        self.stock_data_store = None
        self.fundamentals_store = None

        self.stock_data_dict = None
        self.valuation_dict = None
        self.fundamentals_dict = None
        self.exrights_dict = None
        self.benchmark_data = None
        self.stock_metadata = None
        self.adj_pre_cache = None
        self.dividend_cache = None

        self.index_constituents = {}
        self.stock_status_history = {}

        # 记录已加载的数据类型
        self._loaded_data_types = set()

        # 缓存keys避免重复读取
        self._stock_keys_cache = None
        self._valuation_keys_cache = None
        self._fundamentals_keys_cache = None
        self._exrights_keys_cache = None

        # 加载数据
        self._load_data(required_data)

        # 注册清理函数：进程退出时自动关闭文件
        atexit.register(self._cleanup_on_exit)

        DataServer._initialized = True

    def _close_stores(self):
        """关闭HDF5文件"""
        if self.stock_data_store is not None:
            self.stock_data_store.close()
        if self.fundamentals_store is not None:
            self.fundamentals_store.close()

    def _clear_all_caches(self):
        """清空所有缓存"""
        for cache in [self.valuation_dict, self.fundamentals_dict,
                      self.stock_data_dict, self.exrights_dict]:
            if cache is not None:
                cache.clear_cache()

    def _create_lazy_dict(self, data_type):
        """创建指定类型的LazyDataDict

        Args:
            data_type: 数据类型 ('price', 'valuation', 'fundamentals', 'exrights')

        Returns:
            LazyDataDict实例
        """
        from simtradelab.ptrade.config_manager import config

        type_configs = {
            'price': {
                'store': self.stock_data_store,
                'prefix': '/stock_data/',
                'keys': self._stock_keys_cache,
                'preload': True,
                'cache_size': None
            },
            'valuation': {
                'store': self.fundamentals_store,
                'prefix': '/valuation/',
                'keys': self._valuation_keys_cache,
                'preload': True,
                'cache_size': None
            },
            'fundamentals': {
                'store': self.fundamentals_store,
                'prefix': '/fundamentals/',
                'keys': self._fundamentals_keys_cache,
                'preload': False,
                'cache_size': config.cache.fundamentals_cache_size
            },
            'exrights': {
                'store': self.stock_data_store,
                'prefix': '/exrights/',
                'keys': self._exrights_keys_cache,
                'preload': False,
                'cache_size': config.cache.exrights_cache_size
            }
        }

        cfg = type_configs[data_type]
        if cfg['preload']:
            return LazyDataDict(cfg['store'], cfg['prefix'], cfg['keys'], preload=True)
        else:
            return LazyDataDict(cfg['store'], cfg['prefix'], cfg['keys'],
                              max_cache_size=cfg['cache_size'])

    def _cleanup_on_exit(self):
        """进程退出时清理资源"""
        self._close_stores()

    def _get_cached_keys(self, store, store_name):
        """获取HDF5文件的keys，优先使用缓存

        Args:
            store: HDFStore对象
            store_name: 存储名称，用于缓存文件命名

        Returns:
            list: keys列表
        """
        import os
        import pickle
        from pathlib import Path

        # 缓存文件路径
        cache_dir = Path(self.data_path) / '.keys_cache'
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f'{store_name}_keys.pkl'

        # H5文件路径和修改时间
        h5_file = Path(store.filename)
        h5_mtime = h5_file.stat().st_mtime if h5_file.exists() else 0

        # 检查缓存是否有效
        if cache_file.exists():
            cache_mtime = cache_file.stat().st_mtime
            if cache_mtime >= h5_mtime:
                # 缓存有效，直接加载
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

        # 缓存无效或不存在，重新读取并缓存
        print(f"  首次读取{store_name}索引（下次将使用缓存）...")
        keys_list = list(store.keys())

        # 保存缓存
        with open(cache_file, 'wb') as f:
            pickle.dump(keys_list, f)

        return keys_list

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

        # 打开HDF5文件
        self.stock_data_store = pd.HDFStore(f'{self.data_path}/ptrade_data.h5', 'r')
        self.fundamentals_store = pd.HDFStore(f'{self.data_path}/ptrade_fundamentals.h5', 'r')

        # 一次性读取所有keys并缓存（避免重复遍历HDF5）
        # 使用缓存keys索引文件，大幅提速
        print("正在读取数据索引...")
        stock_data_keys_all = self._get_cached_keys(self.stock_data_store, 'stock_data')
        fundamentals_keys_all = self._get_cached_keys(self.fundamentals_store, 'fundamentals')

        self._stock_keys_cache = [k.split('/')[-1] for k in stock_data_keys_all if k.startswith('/stock_data/')]
        self._exrights_keys_cache = [k.split('/')[-1] for k in stock_data_keys_all if k.startswith('/exrights/')]
        self._valuation_keys_cache = [k.split('/')[-1] for k in fundamentals_keys_all if k.startswith('/valuation/')]
        self._fundamentals_keys_cache = [k.split('/')[-1] for k in fundamentals_keys_all if k.startswith('/fundamentals/')]

        # 加载元数据
        self.stock_metadata = self.stock_data_store['/stock_metadata']
        benchmark_df = self.stock_data_store['/benchmark']
        metadata = self.stock_data_store['/metadata']

        self.index_constituents = json.loads(metadata['index_constituents']) # type: ignore
        self.stock_status_history = json.loads(metadata['stock_status_history']) # type: ignore

        # 构建benchmark_data
        self.benchmark_data = {'000300.SS': benchmark_df}

        # 加载指定的数据类型
        self._load_data_by_types(required_data)

    def _load_data_by_types(self, required_data):
        """根据数据类型加载对应的LazyDataDict

        Args:
            required_data: 需要加载的数据类型集合
        """
        # 股票价格
        if 'price' in required_data:
            print(f"\n[1] 股票价格（{len(self._stock_keys_cache)}只）...") # type: ignore
            self.stock_data_dict = self._create_lazy_dict('price')
        else:
            print("\n[1] 股票价格（跳过）")
            self.stock_data_dict = LazyDataDict(self.stock_data_store, '/stock_data/', [], preload=False)

        # 估值数据
        if 'valuation' in required_data:
            print(f"[2] 估值数据（{len(self._valuation_keys_cache)}只）...") # type: ignore
            self.valuation_dict = self._create_lazy_dict('valuation')
        else:
            print("[2] 估值数据（跳过）")
            self.valuation_dict = LazyDataDict(self.fundamentals_store, '/valuation/', [], preload=False)

        # 财务数据
        if 'fundamentals' in required_data:
            print(f"[3] 财务数据（{len(self._fundamentals_keys_cache)}只，延迟加载）...") # type: ignore
            self.fundamentals_dict = self._create_lazy_dict('fundamentals')
        else:
            print("[3] 财务数据（跳过）")
            self.fundamentals_dict = LazyDataDict(self.fundamentals_store, '/fundamentals/', [], preload=False)

        # 除权数据
        if 'exrights' in required_data:
            print(f"[4] 除权数据（{len(self._exrights_keys_cache)}只，延迟加载）...") # type: ignore
            self.exrights_dict = self._create_lazy_dict('exrights')
        else:
            print("[4] 除权数据（跳过）")
            self.exrights_dict = LazyDataDict(self.stock_data_store, '/exrights/', [], preload=False)

        print(f"\n已加载: {' | '.join(sorted(required_data))}")

        # 动态获取所有指数代码（从成分股数据中提取）
        #index_codes={'000001.SZ', '000905.SZ', '399001.SZ', '399006.SZ', '000300.SS','399101.SZ'}
        index_codes = set()
        if self.index_constituents:
            for date_data in self.index_constituents.values():
                index_codes.update(date_data.keys())

        # 将存在的指数添加到 benchmark_data (保留已有的000300.SS)
        for code in index_codes:
            if code in self.stock_data_dict:
                self.benchmark_data[code] = self.stock_data_dict[code]

        keys_list = list(self.benchmark_data.keys())
        print(f"可用基准(共 {len(keys_list)} 个): {', '.join(keys_list[:5])} ...")


        # 加载复权缓存
        if 'price' in required_data or 'exrights' in required_data:
            from ..ptrade.adj_pre_cache import load_adj_pre_cache, create_dividend_cache
            from ..ptrade.data_context import DataContext
            temp_context = DataContext(
                stock_data_dict=self.stock_data_dict,
                valuation_dict=self.valuation_dict,
                fundamentals_dict=self.fundamentals_dict,
                exrights_dict=self.exrights_dict,
                benchmark_data=self.benchmark_data,
                stock_metadata=self.stock_metadata,
                stock_data_store=self.stock_data_store,
                fundamentals_store=self.fundamentals_store,
                index_constituents=self.index_constituents,
                stock_status_history=self.stock_status_history,
                adj_pre_cache=None
            )
            self.adj_pre_cache = load_adj_pre_cache(temp_context)
            self.dividend_cache = create_dividend_cache(temp_context)

        print("✓ 数据加载完成\n")

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

        # 使用缓存的keys加载缺失数据
        if 'price' in missing and self._stock_keys_cache is not None:
            print(f"  加载股票价格（{len(self._stock_keys_cache)}只）...")
            self.stock_data_dict = self._create_lazy_dict('price')

        if 'valuation' in missing and self._valuation_keys_cache is not None:
            print(f"  加载估值数据（{len(self._valuation_keys_cache)}只）...")
            self.valuation_dict = self._create_lazy_dict('valuation')

        if 'fundamentals' in missing and self._fundamentals_keys_cache is not None:
            print(f"  加载财务数据（{len(self._fundamentals_keys_cache)}只，延迟加载）...")
            self.fundamentals_dict = self._create_lazy_dict('fundamentals')

        if 'exrights' in missing and self._exrights_keys_cache is not None:
            print(f"  加载除权数据（{len(self._exrights_keys_cache)}只，延迟加载）...")
            self.exrights_dict = self._create_lazy_dict('exrights')

        # 更新已加载记录
        self._loaded_data_types.update(missing)

    def get_benchmark_data(self, benchmark_code='000300.SS') -> pd.DataFrame:
        """获取基准数据,支持动态从stock_data_dict获取

        Args:
            benchmark_code: 基准代码,默认为沪深300('000300.SS')

        Returns:
            基准数据DataFrame

        Raises:
            KeyError: 如果指定的基准代码不存在于benchmark_data和stock_data_dict中
        """
        # 优先从 benchmark_data 获取
        if self.benchmark_data and benchmark_code in self.benchmark_data:
            return self.benchmark_data[benchmark_code] # type: ignore

        # 尝试从 stock_data_dict 动态获取
        if self.stock_data_dict and benchmark_code in self.stock_data_dict:
            # 缓存到 benchmark_data 供后续使用
            benchmark_df = self.stock_data_dict[benchmark_code]
            if self.benchmark_data is None:
                self.benchmark_data = {}
            self.benchmark_data[benchmark_code] = benchmark_df
            return benchmark_df

        # 都找不到,抛出异常
        available_benchmark = list(self.benchmark_data.keys())[:5] if self.benchmark_data else []
        available_stock = list(self.stock_data_dict._all_keys)[:5] if self.stock_data_dict else []
        raise KeyError(
            f"基准 {benchmark_code} 不存在。\n"
            f"可用指数基准: {', '.join(available_benchmark)}...\n"
            f"可用股票数据: {', '.join(available_stock)}..."
        )

    @classmethod
    def shutdown(cls):
        """关闭数据服务器，释放所有资源"""
        if cls._instance is None:
            print("数据服务器未启动")
            return

        print("正在关闭数据服务器...")

        # 关闭HDF5文件并打印确认
        cls._instance._close_stores()
        print("  ✓ 关闭股票数据文件")
        print("  ✓ 关闭基本面数据文件")

        # 清空缓存
        cls._instance._clear_all_caches()

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
        if hasattr(self, 'stock_data_store') or hasattr(self, 'fundamentals_store'):
            self._close_stores()
