# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
回测核心类和数据结构

包含Portfolio, Position, Order, Context等核心对象
"""


from __future__ import annotations

from collections import OrderedDict
import bisect
import pandas as pd
import numpy as np
from functools import wraps
from joblib import Parallel, delayed
from tqdm import tqdm
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

from ..utils.performance_config import get_performance_config
from .cache_manager import cache_manager
from .config_manager import config
from .lifecycle_controller import LifecyclePhase


# ==================== 多进程worker函数 ====================
def _load_data_chunk(data_dir, data_type, keys_chunk) -> dict[str, Any]:
    """多进程worker：加载一批数据

    Args:
        data_dir: 数据目录路径
        data_type: 数据类型（'stock', 'valuation', 'fundamentals', 'exrights'）
        keys_chunk: 要加载的key列表

    Returns:
        dict: {key: dataframe}
    """
    from . import storage

    load_map = {
        'stock': storage.load_stock,
        'valuation': storage.load_valuation,
        'fundamentals': storage.load_fundamentals,
        'exrights': lambda data_dir, k: storage.load_exrights(data_dir, k).get('exrights_events', pd.DataFrame())
    }

    load_func = load_map[data_type]
    result: dict[str, Any] = {}

    for key in keys_chunk:
        try:
            df = load_func(data_dir, key)
            if not df.empty:
                result[key] = df
        except Exception:
            pass

    return result


def ensure_data_loaded(func):
    """装饰器：确保数据已加载后再访问"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._ensure_data_loaded()
        return func(self, *args, **kwargs)
    return wrapper


class BacktestContext:
    """回测上下文配置（封装共享依赖）"""
    def __init__(self, stock_data_dict=None, get_stock_date_index_func=None,
                 check_limit_func=None, log_obj=None, context_obj=None, data_context=None):
        self.stock_data_dict = stock_data_dict
        self.get_stock_date_index = get_stock_date_index_func
        self.check_limit = check_limit_func
        self.log = log_obj
        self.context = context_obj
        self.data_context = data_context

class LazyDataDict:
    """延迟加载数据字典（可选全量加载，支持多进程加速）"""
    def __init__(self, data_dir, data_type, all_keys_list, max_cache_size=6000, preload=False, use_multiprocessing=True):
        """初始化延迟加载数据字典

        Args:
            data_dir: 数据根目录路径
            data_type: 数据类型（'stock', 'valuation', 'fundamentals', 'exrights'）
            all_keys_list: 所有可用的key列表
            max_cache_size: 最大缓存数量
            preload: 是否预加载所有数据
            use_multiprocessing: 是否使用多进程加载
        """
        from . import storage

        self.data_dir = data_dir
        self.data_type = data_type

        # 数据类型到加载方法的映射
        self._load_map = {
            'stock': storage.load_stock,
            'valuation': storage.load_valuation,
            'fundamentals': storage.load_fundamentals,
            'exrights': lambda data_dir, k: storage.load_exrights(data_dir, k).get('exrights_events', pd.DataFrame())
        }
        self._cache = OrderedDict()  # 使用OrderedDict实现LRU
        self._all_keys = all_keys_list
        self._max_cache_size = max_cache_size  # 最大缓存数量
        self._preload = preload
        self._access_count = 0  # 访问计数器
        self._lru_update_interval = 100  # 每N次访问才重新排序

        # 如果启用预加载，一次性加载所有数据到内存
        if preload:
            config = get_performance_config()

            # 判断是否使用多进程
            enable_mp = (use_multiprocessing and
                        config.enable_multiprocessing and
                        len(all_keys_list) >= config.min_batch_size)

            if enable_mp:
                # 多进程并行加载
                num_workers = config.num_workers
                chunk_size = max(50, len(all_keys_list) // (num_workers * 2))
                chunks = [all_keys_list[i:i+chunk_size]
                         for i in range(0, len(all_keys_list), chunk_size)]

                print(f"  使用{num_workers}进程并行加载 {len(all_keys_list)} 只...")
                import time
                start_time = time.perf_counter()

                # 多进程加载
                results = Parallel(n_jobs=num_workers, backend='loky', verbose=0)(
                    delayed(_load_data_chunk)(self.data_dir, self.data_type, chunk)
                    for chunk in chunks
                )

                # 合并结果
                for chunk_result in results:
                    self._cache.update(chunk_result)

                elapsed = time.perf_counter() - start_time
                print(f"  ✓ 加载完成，耗时 {elapsed:.1f}秒")
            else:
                # 串行加载（带进度条）
                load_func = self._load_map[self.data_type]
                for key in tqdm(all_keys_list, desc='  加载', ncols=80, ascii=True,
                              bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:4d}/{total:4d} [{elapsed}<{remaining}]'):
                    try:
                        self._cache[key] = load_func(self.data_path, key)
                    except KeyError:
                        pass

    def __contains__(self, key):
        return key in self._all_keys

    def __getitem__(self, key):
        if key in self._cache:
            # LRU优化：每N次访问才重新排序（减少move_to_end开销）
            if not self._preload:
                self._access_count += 1
                if self._access_count % self._lru_update_interval == 0:
                    self._cache.move_to_end(key)
            return self._cache[key]

        # 预加载模式下，缓存中没有说明数据不存在
        if self._preload:
            raise KeyError(f"Stock {key} not found")

        # 延迟加载模式：缓存未命中，从存储加载
        try:
            load_func = self._load_map[self.data_type]
            value = load_func(self.data_dir, key)

            # 添加到缓存
            self._cache[key] = value

            # LRU淘汰：如果超过最大缓存，删除最旧的
            if len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)  # 删除最早的项

            return value
        except KeyError:
            raise KeyError(f'Stock {key} not found')

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return self._all_keys

    def items(self):
        for key in self._all_keys:
            yield key, self[key]

    def clear_cache(self):
        """手动清空缓存"""
        self._cache.clear()



class StockData:
    """单个股票的数据对象，支持mavg和vwap方法"""
    def __init__(self, stock, current_date, bt_ctx):
        """
        Args:
            stock: 股票代码
            current_date: 当前日期
            bt_ctx: BacktestContext实例
        """
        self.stock = stock
        self.current_date = current_date
        self._stock_df = None
        self._current_idx = None
        self._bt_ctx = bt_ctx
        self._data: Optional[dict[str, Any]] = None  # 延迟加载标记
        self._cached_phase = None  # 缓存的phase,用于判断是否需要重新加载
        self._cached_idx = None  # 缓存的idx,用于判断是否需要重新加载

        if bt_ctx and bt_ctx.stock_data_dict and stock in bt_ctx.stock_data_dict:
            self._stock_df = bt_ctx.stock_data_dict[stock]

    def _ensure_data_loaded(self):
        """确保数据已加载（延迟加载）"""
        # 优化:只在phase或idx变化时重新加载
        # 因为同一个Data对象在before_trading_start和handle_data之间共享
        # 需要判断当前phase,如果phase变化则重新加载

        # 首次访问时才计算_current_idx（此时phase已正确设置）
        if self._stock_df is not None and isinstance(self._stock_df, pd.DataFrame):
            if self._bt_ctx and self._bt_ctx.get_stock_date_index:
                date_dict, sorted_dates = self._bt_ctx.get_stock_date_index(self.stock)
                current_date_norm = self.current_date.normalize()

                # 通过LifecycleController判断当前阶段
                controller = self._bt_ctx.context._lifecycle_controller if self._bt_ctx.context else None
                current_phase = controller.current_phase if controller else None

                is_before_trading = (current_phase == LifecyclePhase.BEFORE_TRADING_START)

                if is_before_trading:
                    # before_trading_start阶段：返回前一交易日数据
                    pos = bisect.bisect_left(sorted_dates, current_date_norm)
                    if pos > 0:
                        self._current_idx = date_dict[sorted_dates[pos - 1]]
                else:
                    # handle_data阶段：返回当日数据
                    if current_date_norm in date_dict:
                        self._current_idx = date_dict[current_date_norm]

                # 优化:只有phase或idx变化时才重新加载
                if (self._cached_phase != current_phase or
                    self._cached_idx != self._current_idx or
                    self._data is None):
                    self._data = self._load_data()
                    self._cached_phase = current_phase
                    self._cached_idx = self._current_idx

    def _load_data(self):
        """加载股票当日数据并应用前复权"""
        if self._current_idx is None or self._stock_df is None:
            raise ValueError("股票 {} 在 {} 数据加载失败".format(self.stock, self.current_date))

        row = self._stock_df.iloc[self._current_idx]
        data = {
            'close': row['close'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'volume': row['volume']
        }

        return data

    @ensure_data_loaded
    def __getitem__(self, key):
        if key not in self._data:
            raise KeyError(f"股票 {self.stock} 数据中没有字段 {key}")
        return self._data[key]

    @property
    def dt(self):
        """时间"""
        return self.current_date

    @property
    @ensure_data_loaded
    def open(self):
        """开盘价"""
        return self._data.get('open', np.nan)

    @property
    @ensure_data_loaded
    def close(self):
        """收盘价"""
        return self._data.get('close', np.nan)

    @property
    @ensure_data_loaded
    def price(self):
        """结束时价格（同close）"""
        return self._data.get('close', np.nan)

    @property
    @ensure_data_loaded
    def low(self):
        """最低价"""
        return self._data.get('low', np.nan)

    @property
    @ensure_data_loaded
    def high(self):
        """最高价"""
        return self._data.get('high', np.nan)

    @property
    @ensure_data_loaded
    def volume(self):
        """成交量"""
        return self._data.get('volume', 0)

    @property
    @ensure_data_loaded
    def money(self):
        """成交金额"""
        return self._data['close'] * self._data['volume']

    @ensure_data_loaded
    def mavg(self, window):
        """计算移动平均线（带全局缓存）"""
        cache_key = (self.stock, self.current_date, window)

        # 检查全局缓存
        cached_value = cache_manager.get('ma_cache', cache_key)
        if cached_value is not None:
            return cached_value

        if self._current_idx is None or self._stock_df is None:
            raise ValueError(f"股票 {self.stock} 无法计算mavg({window})")

        start_idx = max(0, self._current_idx - window + 1)
        close_prices = self._stock_df.iloc[start_idx:self._current_idx + 1]['close'].values
        result = np.nanmean(close_prices)

        # 更新全局缓存
        cache_manager.put('ma_cache', cache_key, result)

        return result

    @ensure_data_loaded
    def vwap(self, window):
        """计算成交量加权平均价（带全局缓存）"""
        cache_key = (self.stock, self.current_date, window)

        # 检查全局缓存
        cached_value = cache_manager.get('vwap_cache', cache_key)
        if cached_value is not None:
            return cached_value

        if self._current_idx is None or self._stock_df is None:
            raise ValueError(f"股票 {self.stock} 无法计算vwap({window})")

        start_idx = max(0, self._current_idx - window + 1)
        slice_df = self._stock_df.iloc[start_idx:self._current_idx + 1]
        volumes = slice_df['volume'].values
        closes = slice_df['close'].values
        total_volume = np.sum(volumes)

        if total_volume == 0:
            raise ValueError(f"股票 {self.stock} 计算vwap({window})时成交量为0")

        result = np.sum(closes * volumes) / total_volume

        # 更新全局缓存
        cache_manager.put('vwap_cache', cache_key, result)

        return result


class Data(dict):
    """模拟data对象，支持动态获取股票数据（带LRU缓存限制）"""
    MAX_CACHE_SIZE = 200  # 减小最大缓存股票数，降低内存占用

    def __init__(self, current_date, bt_ctx=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_date = current_date
        self._bt_ctx = bt_ctx
        self._access_order = OrderedDict()  # 使用OrderedDict实现O(1) LRU

    def __getitem__(self, stock):
        """动态获取股票数据，返回StockData对象"""
        # 如果已经缓存，直接返回并更新LRU
        if stock in self:
            if stock in self._access_order:
                self._access_order.move_to_end(stock)  # O(1)操作
            return super().__getitem__(stock)

        # 创建StockData对象并缓存
        stock_data = StockData(stock, self.current_date, self._bt_ctx)
        super().__setitem__(stock, stock_data)
        self._access_order[stock] = None

        # LRU淘汰：如果超过上限，删除最旧的
        if len(self) > self.MAX_CACHE_SIZE:
            oldest, _ = self._access_order.popitem(last=False)
            if oldest in self:
                super().__delitem__(oldest)

        return stock_data


# class Context:
#     """模拟context对象"""
#     def __init__(self, current_dt, bt_ctx=None):
#         self.current_dt = current_dt
#         self.previous_date = (current_dt - timedelta(days=1)).date()
#         self.portfolio = Portfolio(bt_ctx, self)
#         self.blotter = Blotter(current_dt, bt_ctx)
#         # 回测配置
#         self.commission_ratio = 0.0003
#         self.min_commission = 5.0
#         self.commission_type = 'STOCK'
#         self.slippage = 0.0
#         self.fixed_slippage = 0.0
#         self.limit_mode = 'LIMITED'
#         self.volume_ratio = 0.25
#         self.benchmark = '000300.SS'

class Blotter:
    """模拟blotter对象"""
    def __init__(self, current_dt, bt_ctx=None):
        self.current_dt = current_dt
        self.open_orders = []
        self._order_id_counter = 0
        self._bt_ctx = bt_ctx

    def create_order(self, stock, amount):
        """创建订单"""
        self._order_id_counter += 1
        order = Order(
            id=self._order_id_counter,
            symbol=stock,
            amount=amount,
            dt=self.current_dt,
            limit=None
        )
        self.open_orders.append(order)
        return order

    def cancel_order(self, order):
        """取消订单"""
        if order in self.open_orders:
            self.open_orders.remove(order)
            order.status = 'cancelled'
            return True
        return False

    def process_orders(self, portfolio, current_dt):
        """处理未成交订单（使用当日收盘价成交）优化版：批量预加载"""
        executed_orders = []

        if not self.open_orders:
            return executed_orders

        # 批量预加载：收集所有需要的股票数据
        stock_data_cache = {}
        for order in self.open_orders:
            if order.symbol not in stock_data_cache and self._bt_ctx and self._bt_ctx.stock_data_dict:
                stock_df = self._bt_ctx.stock_data_dict.get(order.symbol)
                if stock_df is None or not isinstance(stock_df, pd.DataFrame):
                    continue

                if self._bt_ctx.get_stock_date_index:
                    date_dict, _ = self._bt_ctx.get_stock_date_index(order.symbol)
                    idx = date_dict.get(current_dt)
                else:
                    idx = stock_df.index.get_loc(current_dt) if current_dt in stock_df.index else None

                if idx is not None:
                    stock_data_cache[order.symbol] = {
                        'df': stock_df,
                        'idx': idx,
                        'close': stock_df.iloc[idx]['close'],
                        'volume': stock_df.iloc[idx]['volume']
                    }

        # 处理订单
        for order in self.open_orders[:]:
            # 使用缓存获取当日收盘价
            execution_price = None
            if order.symbol in stock_data_cache:
                execution_price = stock_data_cache[order.symbol]['close']

            if execution_price is None or np.isnan(execution_price) or execution_price <= 0:
                continue

            # 检查成交量限制（LIMIT模式）
            actual_amount = order.amount
            if config.trading.limit_mode == 'LIMIT':
                if order.symbol in stock_data_cache:
                    daily_volume = stock_data_cache[order.symbol]['volume']
                    # 应用成交比例限制
                    volume_ratio = config.trading.volume_ratio
                    max_allowed = int(daily_volume * volume_ratio)

                    if abs(order.amount) > max_allowed:
                        if max_allowed > 0:
                            # 部分成交
                            actual_amount = max_allowed if order.amount > 0 else -max_allowed
                            if self._bt_ctx.log:
                                self._bt_ctx.log.warning(
                                    f"【订单部分成交】{order.symbol} | 委托量:{abs(order.amount)}, 成交量:{abs(actual_amount)} (成交比例限制:{volume_ratio})"
                                )
                        else:
                            if self._bt_ctx.log:
                                self._bt_ctx.log.warning(
                                    f"【订单失败】{order.symbol} | 原因: 当日成交量为0或不足"
                                )
                            self.open_orders.remove(order)
                            order.status = 'failed'
                            continue

            # 检查涨跌停限制
            if self._bt_ctx and self._bt_ctx.check_limit:
                limit_status = self._bt_ctx.check_limit(order.symbol, current_dt)[order.symbol]
                if order.amount > 0 and limit_status == 1:
                    if self._bt_ctx.log:
                        self._bt_ctx.log.warning(f"【订单失败】{order.symbol} | 原因: 涨停买不进")
                    self.open_orders.remove(order)
                    order.status = 'failed'
                    continue
                elif order.amount < 0 and limit_status == -1:
                    if self._bt_ctx.log:
                        self._bt_ctx.log.warning(f"【订单失败】{order.symbol} | 原因: 跌停卖不出")
                    self.open_orders.remove(order)
                    order.status = 'failed'
                    continue

            # 执行订单
            if actual_amount > 0:
                # 买入
                cost = actual_amount * execution_price
                if cost <= portfolio._cash:
                    portfolio._cash -= cost
                    portfolio.add_position(order.symbol, actual_amount, execution_price, current_dt)
                    order.status = 'filled'
                    order.filled = actual_amount
                    executed_orders.append(order)
                self.open_orders.remove(order)
            elif actual_amount < 0:
                # 卖出
                if order.symbol in portfolio.positions:
                    position = portfolio.positions[order.symbol]
                    sell_qty = position.amount

                    # 减仓/清仓（含FIFO分红税调整）
                    portfolio.remove_position(order.symbol, sell_qty, current_dt)

                    # 卖出收入到账
                    sell_revenue = sell_qty * execution_price
                    portfolio._cash += sell_revenue

                    # 更新价格（仅在未清仓时）
                    if order.symbol in portfolio.positions:
                        position = portfolio.positions[order.symbol]
                        position.last_sale_price = execution_price
                        position.market_value = position.amount * execution_price

                    order.status = 'filled'
                    order.filled = actual_amount
                    executed_orders.append(order)

                self.open_orders.remove(order)

        return executed_orders

class Order(BaseModel):
    """订单对象"""
    id: int | str = Field(..., description="订单号（支持整数或UUID字符串）")
    dt: Optional[datetime] = Field(None, description="订单产生时间")
    symbol: str = Field(..., description="标的代码")
    amount: int = Field(..., description="下单数量（正数=买入，负数=卖出）")
    limit: Optional[float] = Field(None, description="指定价格")
    filled: int = Field(default=0, description="成交数量")
    entrust_no: str = Field(default='', description="委托编号")
    priceGear: Optional[int] = Field(default=None, description="盘口档位")
    status: str = Field(default='0', description="订单状态：'0'未报, '1'待报, '2'已报")

    model_config = {"arbitrary_types_allowed": True}

    @property
    def created(self) -> Optional[datetime]:
        """订单生成时间（dt的别名，保持API兼容性）"""
        return self.dt


class Portfolio:
    """模拟portfolio对象"""
    def __init__(self, initial_capital=100000.0, bt_ctx=None, context_obj=None):
        self._cash = initial_capital
        self.starting_cash = initial_capital
        self.positions = {}
        self.positions_value = 0.0
        self._bt_ctx = bt_ctx
        self._context = context_obj
        # 日内缓存
        self._cached_portfolio_value = None
        self._cache_date = None
        # 持股批次追踪（用于分红税FIFO计算）
        self._position_lots = {}

    def _invalidate_cache(self):
        """清空缓存（持仓变化时调用）"""
        self._cached_portfolio_value = None
        self._cache_date = None

    def add_position(self, stock, amount, price, date):
        """买入建仓/加仓"""
        if stock not in self.positions:
            self.positions[stock] = Position(stock, amount, price)
            self._position_lots[stock] = [{'date': date, 'amount': amount, 'dividends': [], 'dividends_total': 0.0}]
        else:
            # 可变模式：直接修改现有position
            position = self.positions[stock]
            new_amount = position.amount + amount
            new_cost = (position.amount * position.cost_basis + amount * price) / new_amount
            position.amount = new_amount
            position.cost_basis = new_cost
            position.enable_amount = new_amount
            position.market_value = new_amount * new_cost
            self._position_lots[stock].append({'date': date, 'amount': amount, 'dividends': [], 'dividends_total': 0.0})
        self._invalidate_cache()

    def remove_position(self, stock, amount, sell_date):
        """卖出减仓/清仓（FIFO扣减批次）"""
        if stock not in self.positions:
            return 0.0

        position = self.positions[stock]

        # 边界检查：卖出数量不能超过持仓
        if amount > position.amount:
            raise ValueError(
                '卖出数量 {} 超过持仓 {}: {}'.format(amount, position.amount, stock)
            )

        # FIFO计算税务调整
        tax_adjustment = self._calculate_dividend_tax(stock, amount, sell_date)

        # 更新持仓
        if position.amount == amount:
            del self.positions[stock]
            if stock in self._position_lots:
                del self._position_lots[stock]
        else:
            position.amount -= amount
            position.enable_amount -= amount
            position.market_value = position.amount * position.cost_basis

        self._invalidate_cache()
        return tax_adjustment

    def add_dividend(self, stock, dividend_per_share):
        """记录分红到各批次"""
        if stock in self._position_lots:
            for lot in self._position_lots[stock]:
                lot_div = dividend_per_share * lot['amount']
                lot['dividends'].append(lot_div)
                lot['dividends_total'] = lot.get('dividends_total', 0.0) + lot_div

    def _calculate_dividend_tax(self, stock, amount, sell_date):
        """计算分红税调整（FIFO）"""
        if stock not in self._position_lots:
            return 0.0

        lots = self._position_lots[stock]
        remaining = amount
        tax_adjustment = 0.0
        i = 0

        while i < len(lots) and remaining > 0:
            lot = lots[i]
            holding_days = (sell_date - lot['date']).days

            # 真实税率
            if holding_days <= 30:
                actual_rate = 0.20
            elif holding_days <= 365:
                actual_rate = 0.10
            else:
                actual_rate = 0.0

            # 本批次卖出数量
            sell_qty = min(remaining, lot['amount'])
            ratio = sell_qty / lot['amount']

            # 优先使用缓存总和
            lot_div_total = lot.get('dividends_total', sum(lot['dividends']))
            tax_adjustment += lot_div_total * ratio * (actual_rate - 0.20)

            # 扣减批次
            if lot['amount'] <= remaining:
                remaining -= lot['amount']
                lots.pop(i)
            else:
                lot['amount'] -= remaining
                # 更新剩余部分的分红总额
                lot['dividends_total'] = lot_div_total * (1.0 - ratio)
                remaining = 0
                i += 1

        return tax_adjustment

    @property
    def cash(self):
        """当前可用资金"""
        return self._cash

    @property
    def available_cash(self):
        """当前可用资金（别名）"""
        return self._cash

    @property
    def capital_used(self):
        """已使用的现金"""
        return self.starting_cash - self._cash

    @property
    def returns(self):
        """当前收益比例"""
        if self.starting_cash > 0:
            return (self.portfolio_value - self.starting_cash) / self.starting_cash
        return 0.0

    @property
    def pnl(self):
        """浮动盈亏"""
        return self.portfolio_value - self.starting_cash

    @property
    def start_date(self):
        """开始时间"""
        return self._context.current_dt if self._context else None

    @property
    def portfolio_value(self):
        """计算总资产（现金+持仓市值）带日内缓存"""
        # 检查缓存
        current_date = self._context.current_dt if self._context else None
        if current_date is not None and current_date == self._cache_date and self._cached_portfolio_value is not None:
            return self._cached_portfolio_value

        total = self._cash

        # 持仓市值（使用当天收盘价）
        positions_value = 0.0
        for stock, position in self.positions.items():
            if position.amount > 0:
                current_price = position.cost_basis
                if self._bt_ctx and self._bt_ctx.stock_data_dict and stock in self._bt_ctx.stock_data_dict:
                    stock_df = self._bt_ctx.stock_data_dict[stock]
                    if isinstance(stock_df, pd.DataFrame) and self._context:
                        # 使用哈希索引 O(1) 查找，避免 df.loc O(log n)
                        if self._bt_ctx.get_stock_date_index:
                            date_dict, _ = self._bt_ctx.get_stock_date_index(stock)
                            idx = date_dict.get(self._context.current_dt)
                            if idx is not None:
                                price = stock_df.iloc[idx]['close']
                                if not np.isnan(price) and price > 0:
                                    current_price = price

                position.last_sale_price = current_price
                position.market_value = position.amount * current_price
                positions_value += position.amount * current_price

        self.positions_value = positions_value
        result = total + positions_value

        # 更新缓存
        if current_date is not None:
            self._cache_date = current_date
            self._cached_portfolio_value = result

        return result

    @property
    def total_value(self):
        """总资产（portfolio_value 的别名）"""
        return self.portfolio_value

class Position:
    """模拟持仓对象"""
    def __init__(self, stock: str, amount: float, cost_basis: float):
        self.stock = stock
        self.sid = stock  # 别名，保持兼容
        self.amount = amount
        self.cost_basis = cost_basis
        self.enable_amount = amount
        self.last_sale_price = cost_basis
        self.today_amount = 0
        self.business_type = 'STOCK'
        self.market_value = amount * cost_basis



class Global:
    """模拟全局变量g（策略可用于存储自定义数据）"""
    pass

