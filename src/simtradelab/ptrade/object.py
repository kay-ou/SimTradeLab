# -*- coding: utf-8 -*-
"""
回测核心类和数据结构

包含Portfolio, Position, Order, Context等核心对象
"""

from collections import OrderedDict
import bisect
import pandas as pd
import numpy as np


# 全局缓存：用于StockData的mavg和vwap计算
_GLOBAL_MA_CACHE = OrderedDict()
_GLOBAL_VWAP_CACHE = OrderedDict()
_MAX_GLOBAL_CACHE_SIZE = 5000  # 减小最大缓存条目数
_CACHE_CURRENT_DATE = None  # 跟踪当前日期，用于每日清理


def clear_daily_cache():
    """清理全局缓存（每日调用）"""
    global _GLOBAL_MA_CACHE, _GLOBAL_VWAP_CACHE, _CACHE_CURRENT_DATE
    _GLOBAL_MA_CACHE.clear()
    _GLOBAL_VWAP_CACHE.clear()
    _CACHE_CURRENT_DATE = None


class BacktestContext:
    """回测上下文配置（封装共享依赖）"""
    def __init__(self, stock_data_dict=None, get_stock_date_index_func=None,
                 check_limit_func=None, log_obj=None, context_obj=None):
        self.stock_data_dict = stock_data_dict
        self.get_stock_date_index = get_stock_date_index_func
        self.check_limit = check_limit_func
        self.log = log_obj
        self.context = context_obj

class LazyDataDict:
    """延迟加载数据字典（可选全量加载）"""
    def __init__(self, store, prefix, all_keys_list, max_cache_size=6000, preload=False):
        self.store = store
        self.prefix = prefix
        self._cache = OrderedDict()  # 使用OrderedDict实现LRU
        self._all_keys = all_keys_list
        self._max_cache_size = max_cache_size  # 最大缓存数量
        self._preload = preload
        self._access_count = 0  # 访问计数器
        self._lru_update_interval = 100  # 每N次访问才重新排序

        # 如果启用预加载，一次性加载所有数据到内存
        if preload:
            from tqdm import tqdm

            for key in tqdm(all_keys_list, desc='  加载', ncols=80, ascii=True,
                          bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:4d}/{total:4d} [{elapsed}<{remaining}]'):
                try:
                    self._cache[key] = self.store[f'{self.prefix}{key}']
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

        # 延迟加载模式：缓存未命中，从HDF5加载
        try:
            value = self.store[f'{self.prefix}{key}']

            # 添加到缓存
            self._cache[key] = value

            # LRU淘汰：如果超过最大缓存，删除最旧的
            if len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)  # 删除最早的项

            return value
        except KeyError:
            raise KeyError(f"Stock {key} not found")

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

        if bt_ctx and bt_ctx.stock_data_dict and stock in bt_ctx.stock_data_dict:
            self._stock_df = bt_ctx.stock_data_dict[stock]
            if isinstance(self._stock_df, pd.DataFrame):
                # 使用预计算的日期索引，避免每次过滤整个index
                if bt_ctx.get_stock_date_index:
                    date_dict, sorted_dates = bt_ctx.get_stock_date_index(stock)
                    # 直接查找当前日期或最近的历史日期
                    if current_date in date_dict:
                        self._current_idx = date_dict[current_date]
                    elif sorted_dates:
                        # 二分查找最近的历史日期
                        pos = bisect.bisect_left(sorted_dates, current_date)
                        if pos > 0:
                            self._current_idx = date_dict[sorted_dates[pos - 1]]
                else:
                    # 回退到原始方法
                    try:
                        self._current_idx = self._stock_df.index.get_loc(current_date)
                    except KeyError:
                        valid_dates = self._stock_df.index[self._stock_df.index < current_date]
                        if len(valid_dates) > 0:
                            self._current_idx = self._stock_df.index.get_loc(valid_dates[-1])

        self._data = self._load_data()

    def _load_data(self):
        """加载股票当日数据"""
        if self._current_idx is not None and self._stock_df is not None:
            try:
                row = self._stock_df.iloc[self._current_idx]
                return {
                    'close': row['close'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'volume': row['volume']
                }
            except:
                pass
        return {'close': np.nan, 'open': np.nan, 'high': np.nan, 'low': np.nan, 'volume': 0}

    def __getitem__(self, key):
        return self._data.get(key, np.nan)

    @property
    def dt(self):
        """时间"""
        return self.current_date

    @property
    def open(self):
        """开盘价"""
        return self._data.get('open', np.nan)

    @property
    def close(self):
        """收盘价"""
        return self._data.get('close', np.nan)

    @property
    def price(self):
        """结束时价格（同close）"""
        return self._data.get('close', np.nan)

    @property
    def low(self):
        """最低价"""
        return self._data.get('low', np.nan)

    @property
    def high(self):
        """最高价"""
        return self._data.get('high', np.nan)

    @property
    def volume(self):
        """成交量"""
        return self._data.get('volume', 0)

    @property
    def money(self):
        """成交金额"""
        return self._data.get('close', np.nan) * self._data.get('volume', 0)

    def mavg(self, window):
        """计算移动平均线（带全局缓存）"""
        global _GLOBAL_MA_CACHE

        cache_key = (self.stock, self.current_date, window)

        # 检查全局缓存
        if cache_key in _GLOBAL_MA_CACHE:
            _GLOBAL_MA_CACHE.move_to_end(cache_key)  # LRU更新
            return _GLOBAL_MA_CACHE[cache_key]

        if self._current_idx is None or self._stock_df is None:
            return np.nan

        try:
            start_idx = max(0, self._current_idx - window + 1)
            close_prices = self._stock_df.iloc[start_idx:self._current_idx + 1]['close'].values
            # 使用 numpy 的 nanmean 直接处理 NaN
            result = np.nanmean(close_prices) if len(close_prices) > 0 else np.nan

            # 更新全局缓存
            _GLOBAL_MA_CACHE[cache_key] = result
            if len(_GLOBAL_MA_CACHE) > _MAX_GLOBAL_CACHE_SIZE:
                _GLOBAL_MA_CACHE.popitem(last=False)  # LRU淘汰

            return result
        except:
            return np.nan

    def vwap(self, window):
        """计算成交量加权平均价（带全局缓存）"""
        global _GLOBAL_VWAP_CACHE

        cache_key = (self.stock, self.current_date, window)

        # 检查全局缓存
        if cache_key in _GLOBAL_VWAP_CACHE:
            _GLOBAL_VWAP_CACHE.move_to_end(cache_key)  # LRU更新
            return _GLOBAL_VWAP_CACHE[cache_key]

        if self._current_idx is None or self._stock_df is None:
            return np.nan

        try:
            start_idx = max(0, self._current_idx - window + 1)
            slice_df = self._stock_df.iloc[start_idx:self._current_idx + 1]
            volumes = slice_df['volume'].values
            closes = slice_df['close'].values
            total_volume = np.sum(volumes)

            if total_volume > 0:
                result = np.sum(closes * volumes) / total_volume
            else:
                result = closes[-1] if len(closes) > 0 else np.nan

            # 更新全局缓存
            _GLOBAL_VWAP_CACHE[cache_key] = result
            if len(_GLOBAL_VWAP_CACHE) > _MAX_GLOBAL_CACHE_SIZE:
                _GLOBAL_VWAP_CACHE.popitem(last=False)  # LRU淘汰

            return result
        except:
            return np.nan


class Data(dict):
    """模拟data对象，支持动态获取股票数据（带LRU缓存限制）"""
    MAX_CACHE_SIZE = 200  # 减小最大缓存股票数，降低内存占用

    def __init__(self, current_date, bt_ctx=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_date = current_date
        self._bt_ctx = bt_ctx
        self._access_order = []  # LRU跟踪

    def __getitem__(self, stock):
        """动态获取股票数据，返回StockData对象"""
        # 如果已经缓存，直接返回并更新LRU
        if stock in self:
            if stock in self._access_order:
                self._access_order.remove(stock)
            self._access_order.append(stock)
            return super().__getitem__(stock)

        # 创建StockData对象并缓存
        stock_data = StockData(stock, self.current_date, self._bt_ctx)
        super().__setitem__(stock, stock_data)
        self._access_order.append(stock)

        # LRU淘汰：如果超过上限，删除最旧的
        if len(self) > self.MAX_CACHE_SIZE:
            oldest = self._access_order.pop(0)
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
            order_id=self._order_id_counter,
            stock=stock,
            amount=amount,
            created_dt=self.current_dt
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
            if order.stock not in stock_data_cache and self._bt_ctx and self._bt_ctx.stock_data_dict:
                if order.stock in self._bt_ctx.stock_data_dict:
                    stock_df = self._bt_ctx.stock_data_dict[order.stock]
                    if isinstance(stock_df, pd.DataFrame):
                        try:
                            if self._bt_ctx.get_stock_date_index:
                                date_dict, _ = self._bt_ctx.get_stock_date_index(order.stock)
                                idx = date_dict.get(current_dt)
                            else:
                                idx = stock_df.index.get_loc(current_dt)

                            if idx is not None:
                                stock_data_cache[order.stock] = {
                                    'df': stock_df,
                                    'idx': idx,
                                    'close': stock_df.iloc[idx]['close'],
                                    'volume': stock_df.iloc[idx]['volume']
                                }
                        except:
                            pass

        # 处理订单
        for order in self.open_orders[:]:
            # 使用缓存获取当日收盘价
            execution_price = None
            if order.stock in stock_data_cache:
                execution_price = stock_data_cache[order.stock]['close']

            if execution_price is None or np.isnan(execution_price) or execution_price <= 0:
                continue

            # 检查成交量限制（LIMIT模式）
            actual_amount = order.amount
            if self._bt_ctx and self._bt_ctx.context and self._bt_ctx.context.limit_mode == 'LIMIT':
                if order.stock in stock_data_cache:
                    daily_volume = stock_data_cache[order.stock]['volume']
                    # 应用成交比例限制
                    volume_ratio = getattr(self._bt_ctx.context, 'volume_ratio', 0.25)
                    max_allowed = int(daily_volume * volume_ratio)

                    if abs(order.amount) > max_allowed:
                        if max_allowed > 0:
                            # 部分成交
                            actual_amount = max_allowed if order.amount > 0 else -max_allowed
                            if self._bt_ctx.log:
                                self._bt_ctx.log.warning(
                                    f"【订单部分成交】{order.stock} | 委托量:{abs(order.amount)}, 成交量:{abs(actual_amount)} (成交比例限制:{volume_ratio})"
                                )
                        else:
                            if self._bt_ctx.log:
                                self._bt_ctx.log.warning(
                                    f"【订单失败】{order.stock} | 原因: 当日成交量为0或不足"
                                )
                            self.open_orders.remove(order)
                            order.status = 'failed'
                            continue

            # 检查涨跌停限制
            if self._bt_ctx and self._bt_ctx.check_limit:
                limit_status = self._bt_ctx.check_limit(order.stock, current_dt)[order.stock]
                if order.amount > 0 and limit_status == 1:
                    if self._bt_ctx.log:
                        self._bt_ctx.log.warning(f"【订单失败】{order.stock} | 原因: 涨停买不进")
                    self.open_orders.remove(order)
                    order.status = 'failed'
                    continue
                elif order.amount < 0 and limit_status == -1:
                    if self._bt_ctx.log:
                        self._bt_ctx.log.warning(f"【订单失败】{order.stock} | 原因: 跌停卖不出")
                    self.open_orders.remove(order)
                    order.status = 'failed'
                    continue

            # 执行订单
            if actual_amount > 0:
                # 买入
                cost = actual_amount * execution_price
                if cost <= portfolio._cash:
                    portfolio._cash -= cost
                    portfolio.add_position(order.stock, actual_amount, execution_price, current_dt)
                    order.status = 'filled'
                    order.filled = actual_amount
                    executed_orders.append(order)
                self.open_orders.remove(order)
            elif actual_amount < 0:
                # 卖出
                if order.stock in portfolio.positions:
                    position = portfolio.positions[order.stock]
                    sell_qty = position.amount

                    # 减仓/清仓（含FIFO分红税调整）
                    portfolio.remove_position(order.stock, sell_qty, current_dt)

                    # 卖出收入到账
                    sell_revenue = sell_qty * execution_price
                    portfolio._cash += sell_revenue

                    # 更新价格
                    position.last_sale_price = execution_price
                    if position.amount > 0:
                        position.market_value = position.amount * execution_price

                    order.status = 'filled'
                    order.filled = actual_amount
                    executed_orders.append(order)

                self.open_orders.remove(order)

        return executed_orders

class Order:
    """订单对象"""
    def __init__(self, order_id, stock, amount, created_dt=None, price=None):
        self.id = order_id  # 订单号
        self.dt = created_dt  # 订单产生时间，datetime.datetime类型
        self.limit = price  # 指定价格（API字段）
        self.symbol = stock  #  标的代码(备注：标的代码尾缀为四位，上证为XSHG，深圳为XSHE，如需对应到代码请做代码尾缀兼容)
        self.amount = amount  # 下单数量（正数=买入，负数=卖出）
        self.created = created_dt  # 订单生成时间，datetime.datetime类型
        self.filled = 0  # 成交数量，买入时为正数，卖出时为负数
        self.entrust_no = ''  # 委托编号
        self.priceGear = None # 盘口档位
        self.status = '0'  # 订单状态：'0'未报, '1'待报, '2'已报

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
            old_pos = self.positions[stock]
            new_amount = old_pos.amount + amount
            new_cost = (old_pos.amount * old_pos.cost_basis + amount * price) / new_amount
            self.positions[stock] = Position(stock, new_amount, new_cost)
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
                '卖出数量({})超过持仓({}): {}'.format(amount, position.amount, stock)
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

        # 持仓市值（使用昨天收盘价，避免未来函数）
        positions_value = 0.0
        for stock, position in self.positions.items():
            if position.amount > 0:
                current_price = position.cost_basis
                if self._bt_ctx and self._bt_ctx.stock_data_dict and stock in self._bt_ctx.stock_data_dict:
                    stock_df = self._bt_ctx.stock_data_dict[stock]
                    if isinstance(stock_df, pd.DataFrame) and self._context:
                        try:
                            # 使用预构建索引快速查找
                            if self._bt_ctx.get_stock_date_index:
                                date_dict, sorted_dates = self._bt_ctx.get_stock_date_index(stock)
                                # 二分查找最近的历史日期
                                import bisect
                                pos = bisect.bisect_left(sorted_dates, self._context.current_dt)
                                if pos > 0:
                                    last_date = sorted_dates[pos - 1]
                                    idx = date_dict[last_date]
                                    current_price = stock_df.iloc[idx]['close']
                                    if np.isnan(current_price) or current_price <= 0:
                                        current_price = position.cost_basis
                            else:
                                # 回退到原始方法
                                valid_dates = stock_df.index[stock_df.index < self._context.current_dt]
                                if len(valid_dates) > 0:
                                    last_date = valid_dates[-1]
                                    idx = stock_df.index.get_loc(last_date)
                                    current_price = stock_df.iloc[idx]['close']
                                    if np.isnan(current_price) or current_price <= 0:
                                        current_price = position.cost_basis
                        except:
                            pass

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

class Position:
    """模拟持仓对象"""
    def __init__(self, stock, amount, cost_basis):
        self.sid = stock
        self.stock = stock
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

