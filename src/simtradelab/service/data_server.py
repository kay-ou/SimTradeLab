# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
数据服务器 - 支持数据常驻内存，多次运行策略无需重新加载

使用方式：
1. 首次运行时自动加载数据并缓存到单例
2. 后续运行直接使用缓存的数据
3. 进程结束时自动释放资源
"""


import pandas as pd
import atexit
from ..ptrade.object import LazyDataDict
from ..utils.config import config as global_config


class DataServer:
    """数据服务器单例"""
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, required_data=None, frequency='1d', data_path: str = None):
        resolved_path = str(data_path) if data_path else global_config.data_path

        # 路径变更时强制重新初始化
        if DataServer._initialized:
            if resolved_path != self.data_path:
                DataServer._initialized = False
            else:
                print("使用已加载的数据（常驻内存）")
                if required_data is not None:
                    self._ensure_data_loaded(required_data, frequency)
                return

        print("=" * 70)
        print("首次加载 - 在jupyter notebook中数据将常驻内存")
        print("=" * 70)

        self.data_path = resolved_path

        print(f"数据路径: {self.data_path}")

        self.stock_data_dict = None
        self.stock_data_dict_1m = None
        self.valuation_dict = None
        self.fundamentals_dict = None
        self.exrights_dict = None
        self.benchmark_data = None
        self.stock_metadata = None
        self.adj_pre_cache = None
        self.adj_post_cache = None
        self.dividend_cache = None

        self.index_constituents = {}
        self.stock_status_history = {}

        # 记录已加载的数据类型
        self._loaded_data_types = set()
        self._frequency = frequency

        # 缓存keys避免重复读取
        self._stock_keys_cache = None
        self._stock_1m_keys_cache = None
        self._valuation_keys_cache = None
        self._fundamentals_keys_cache = None
        self._exrights_keys_cache = None

        # 加载数据
        self._load_data(required_data, frequency)

        # 注册清理函数：进程退出时自动关闭文件
        atexit.register(self._cleanup_on_exit)

        DataServer._initialized = True

    def _clear_all_caches(self):
        """清空所有缓存"""
        for cache in [self.valuation_dict, self.fundamentals_dict,
                      self.stock_data_dict, self.exrights_dict, self.stock_data_dict_1m]:
            if cache is not None:
                cache.clear_cache()

    def _cleanup_on_exit(self):
        """进程退出时清理资源"""
        pass

    def _load_data(self, required_data=None, frequency='1d'):
        """加载数据

        Args:
            required_data: 需要加载的数据集合,None表示全部加载
            frequency: 数据频率 '1d'日线 '1m'分钟线
        """
        # 默认加载全部
        if required_data is None:
            required_data = {'price', 'valuation', 'fundamentals', 'exrights'}

        # 记录需要加载的数据类型
        self._loaded_data_types = required_data
        self._frequency = frequency
        from ..ptrade import storage

        print("正在读取数据...")

        # 获取股票列表
        self._stock_keys_cache = storage.list_stocks(self.data_path)
        self._stock_1m_keys_cache = storage.list_stocks_1m(self.data_path)
        self._valuation_keys_cache = self._stock_keys_cache
        self._fundamentals_keys_cache = self._stock_keys_cache
        self._exrights_keys_cache = self._stock_keys_cache

        print("正在读取元数据...")

        # 加载元数据
        metadata_all = storage.load_metadata(self.data_path, 'metadata')
        if metadata_all:
            self.index_constituents = metadata_all.get('index_constituents', {})
            self.stock_status_history = metadata_all.get('stock_status_history', {})
        else:
            self.index_constituents = {}
            self.stock_status_history = {}

        # 加载交易日历
        trade_days_data = storage.load_metadata(self.data_path, 'trade_days')
        if trade_days_data and 'trade_days' in trade_days_data:
            self.trade_days = pd.DatetimeIndex(pd.to_datetime(trade_days_data['trade_days']))
        else:
            self.trade_days = None

        # 加载股票元数据
        stock_metadata_data = storage.load_metadata(self.data_path, 'stock_metadata')
        if stock_metadata_data and 'data' in stock_metadata_data:
            self.stock_metadata = pd.DataFrame(stock_metadata_data['data'])
            if not self.stock_metadata.empty and 'symbol' in self.stock_metadata.columns:
                self.stock_metadata.set_index('symbol', inplace=True)
        else:
            self.stock_metadata = pd.DataFrame()

        # 加载基准数据
        benchmark_data_raw = storage.load_metadata(self.data_path, 'benchmark')
        if benchmark_data_raw and 'data' in benchmark_data_raw:
            benchmark_df = pd.DataFrame(benchmark_data_raw['data'])
            if not benchmark_df.empty and 'date' in benchmark_df.columns:
                benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
                benchmark_df.set_index('date', inplace=True)
            self.benchmark_data = {'000300.SS': benchmark_df}
        else:
            # 如果benchmark不存在，从stock数据加载默认基准
            self.benchmark_data = {}
            if '000300.SS' in self._stock_keys_cache:
                default_benchmark = storage.load_stock(self.data_path, '000300.SS')
                if default_benchmark is not None:
                    self.benchmark_data['000300.SS'] = default_benchmark

        # 加载指定的数据类型
        self._load_data_by_types(required_data)

    def _load_data_by_types(self, required_data):
        """加载数据类型"""
        from ..ptrade import storage

        # 股票价格（日线）
        if 'price' in required_data:
            print(f"\n[1] 股票价格（{len(self._stock_keys_cache)}只）...")
            self.stock_data_dict = LazyDataDict(
                self.data_path, 'stock', self._stock_keys_cache,
                preload=True
            )

            # 立即填充 benchmark_data（确保 000300.SS 可用）
            if '000300.SS' not in self.benchmark_data:
                if '000300.SS' in self._stock_keys_cache:
                    # 注意：这里不能用 self.stock_data_dict['000300.SS']，因为数据还在加载中
                    # 直接从storage加载，等preload完成后benchmark_data会被更新
                    self.benchmark_data['000300.SS'] = storage.load_stock(self.data_path, '000300.SS')
        else:
            print("\n[1] 股票价格（跳过）")
            self.stock_data_dict = LazyDataDict(self.data_path, 'stock', [], preload=False)

        # 分钟数据（按需加载）
        if 'price_1m' in required_data and self._stock_1m_keys_cache:
            print(f"[1.1] 分钟数据（{len(self._stock_1m_keys_cache)}只）...")
            self.stock_data_dict_1m = LazyDataDict(
                self.data_path, 'stock_1m', self._stock_1m_keys_cache,
                preload=True
            )
        else:
            # 延迟加载模式
            if self._stock_1m_keys_cache:
                self.stock_data_dict_1m = LazyDataDict(
                    self.data_path, 'stock_1m', self._stock_1m_keys_cache,
                    preload=False
                )
            else:
                self.stock_data_dict_1m = None

        # 估值数据
        if 'valuation' in required_data:
            print(f"[2] 估值数据（{len(self._valuation_keys_cache)}只）...")
            self.valuation_dict = LazyDataDict(
                self.data_path, 'valuation', self._valuation_keys_cache,
                preload=True
            )
        else:
            print("[2] 估值数据（跳过）")
            self.valuation_dict = LazyDataDict(self.data_path, 'valuation', [], preload=False)

        # 财务数据
        if 'fundamentals' in required_data:
            print(f"[3] 财务数据（{len(self._fundamentals_keys_cache)}只，延迟加载）...")
            from ..ptrade.config_manager import config
            self.fundamentals_dict = LazyDataDict(
                self.data_path, 'fundamentals', self._fundamentals_keys_cache,
                preload=False,
                max_cache_size=config.cache.fundamentals_cache_size
            )
        else:
            print("[3] 财务数据（跳过）")
            self.fundamentals_dict = LazyDataDict(self.data_path, 'fundamentals', [], preload=False)

        # 除权数据
        if 'exrights' in required_data:
            print(f"[4] 除权数据（{len(self._exrights_keys_cache)}只，延迟加载）...")
            from ..ptrade.config_manager import config
            self.exrights_dict = LazyDataDict(
                self.data_path, 'exrights', self._exrights_keys_cache,
                preload=False,
                max_cache_size=config.cache.exrights_cache_size
            )
        else:
            print("[4] 除权数据（跳过）")
            self.exrights_dict = LazyDataDict(self.data_path, 'exrights', [], preload=False)

        print(f"\n已加载: {' | '.join(sorted(required_data))}")

        # 动态获取所有指数代码
        index_codes = set()
        if self.index_constituents:
            for date_data in self.index_constituents.values():
                index_codes.update(date_data.keys())

        # 将存在的指数添加到 benchmark_data（从 stock_data_dict 获取）
        for code in index_codes:
            if code in self.stock_data_dict:
                self.benchmark_data[code] = self.stock_data_dict[code]

        # 确保 000300.SS 在 benchmark_data 中
        if '000300.SS' not in self.benchmark_data and '000300.SS' in self.stock_data_dict:
            self.benchmark_data['000300.SS'] = self.stock_data_dict['000300.SS']

        keys_list = list(self.benchmark_data.keys())
        print(f"可用基准(共 {len(keys_list)} 个): {', '.join(keys_list[:5])} ...")

        # 加载复权缓存
        if 'price' in required_data or 'exrights' in required_data:
            from ..ptrade.adj_cache import load_adj_pre_cache, load_adj_post_cache, create_dividend_cache
            from ..ptrade.data_context import DataContext
            temp_context = DataContext(
                stock_data_dict=self.stock_data_dict,
                valuation_dict=self.valuation_dict,
                fundamentals_dict=self.fundamentals_dict,
                exrights_dict=self.exrights_dict,
                benchmark_data=self.benchmark_data,
                stock_metadata=self.stock_metadata,
                index_constituents=self.index_constituents,
                stock_status_history=self.stock_status_history,
                adj_pre_cache=None,
                adj_post_cache=None,
                trade_days=self.trade_days
            )
            self.adj_pre_cache = load_adj_pre_cache(temp_context)
            self.adj_post_cache = load_adj_post_cache(temp_context)
            self.dividend_cache = create_dividend_cache(temp_context)

        print("✓ 数据加载完成\n")

    def _ensure_data_loaded(self, required_data, frequency='1d'):
        """确保所需数据已加载,动态补充缺失的数据

        Args:
            required_data: 需要的数据集合
            frequency: 回测频率 '1d'日线 '1m'分钟线
        """
        if not hasattr(self, '_loaded_data_types'):
            self._loaded_data_types = set()

        # 计算缺失的数据类型
        missing = set(required_data) - self._loaded_data_types

        # 分钟回测需要加载分钟数据
        if frequency == '1m' and self.stock_data_dict_1m is None:
            missing.add('price_1m')

        if not missing:
            return

        print(f"补充加载缺失数据: {', '.join(sorted(missing))}")

        # 使用缓存的keys加载缺失数据
        if 'price' in missing and self._stock_keys_cache is not None:
            print(f"  加载股票价格（{len(self._stock_keys_cache)}只）...")
            self.stock_data_dict = LazyDataDict(
                self.data_path, 'stock', self._stock_keys_cache, preload=True
            )

        if 'valuation' in missing and self._valuation_keys_cache is not None:
            print(f"  加载估值数据（{len(self._valuation_keys_cache)}只）...")
            self.valuation_dict = LazyDataDict(
                self.data_path, 'valuation', self._valuation_keys_cache, preload=True
            )

        if 'fundamentals' in missing and self._fundamentals_keys_cache is not None:
            print(f"  加载财务数据（{len(self._fundamentals_keys_cache)}只，延迟加载）...")
            from ..ptrade.config_manager import config
            self.fundamentals_dict = LazyDataDict(
                self.data_path, 'fundamentals', self._fundamentals_keys_cache,
                preload=False,
                max_cache_size=config.cache.fundamentals_cache_size
            )

        if 'exrights' in missing and self._exrights_keys_cache is not None:
            print(f"  加载除权数据（{len(self._exrights_keys_cache)}只，延迟加载）...")
            from ..ptrade.config_manager import config
            self.exrights_dict = LazyDataDict(
                self.data_path, 'exrights', self._exrights_keys_cache,
                preload=False,
                max_cache_size=config.cache.exrights_cache_size
            )

        if 'price_1m' in missing and self._stock_1m_keys_cache is not None:
            print(f"  加载分钟数据（{len(self._stock_1m_keys_cache)}只）...")
            self.stock_data_dict_1m = LazyDataDict(
                self.data_path, 'stock_1m', self._stock_1m_keys_cache,
                preload=True
            )

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

        # 清空其他缓存
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
        """析构时清空缓存"""
        pass
