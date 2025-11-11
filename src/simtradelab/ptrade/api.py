# -*- coding: utf-8 -*-
"""
ptrade API 模拟层

模拟ptrade平台的所有API函数，用于本地回测
"""

import numpy as np
import pandas as pd
import json
import bisect
import time
from functools import wraps


def format_elapsed_time(elapsed: float) -> str:
    """格式化耗时显示

    Args:
        elapsed: 耗时（秒）

    Returns:
        格式化后的字符串（如：3分32秒 或 45.23秒）
    """
    minutes = int(elapsed / 60)
    seconds = int(elapsed % 60)
    if minutes > 0:
        return f"{minutes}分{seconds}秒"
    else:
        return f"{elapsed:.2f}秒"


def get_current_elapsed_time(instance, func_name: str) -> str:
    """获取正在执行的函数的当前耗时

    Args:
        instance: 实例对象
        func_name: 函数名

    Returns:
        格式化后的耗时字符串
    """
    if hasattr(instance, '_timing_start'):
        start_time = instance._timing_start.get(func_name, 0)
        if start_time > 0:
            elapsed = time.time() - start_time
            return format_elapsed_time(elapsed)
    return '0秒'


def timing(func):
    """性能计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()

        # 保存开始时间（供函数内部访问当前耗时）
        if args and hasattr(args[0], '__class__'):
            instance = args[0]
            if not hasattr(instance, '_timing_start'):
                instance._timing_start = {}
            instance._timing_start[func.__name__] = start

        result = func(*args, **kwargs)
        elapsed = time.time() - start

        if elapsed > 0.1:  # 只记录耗时超过100ms的调用
            func_name = func.__name__
            # 尝试获取第一个参数的类型信息
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                if class_name == 'PtradeAPI':
                    # 如果是批量操作，显示批次大小
                    if len(args) > 1 and isinstance(args[1], (list, tuple)):
                        print(f"  [PERF] {func_name}(批量{len(args[1])}只) 耗时: {elapsed:.2f}s", flush=True)
                    else:
                        print(f"  [PERF] {func_name} 耗时: {elapsed:.2f}s", flush=True)
                elif class_name in ['BacktestRunner', 'StrategyExecutionEngine']:
                    # 回测相关类显示耗时
                    print(f"✓ {func_name} 完成，耗时: {format_elapsed_time(elapsed)}", flush=True)
        return result
    return wrapper


def validate_lifecycle(func):
    """生命周期验证装饰器

    自动检查API是否可以在当前生命周期阶段调用
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 如果context有lifecycle_controller，进行验证
        if hasattr(self, 'context') and self.context and hasattr(self.context, '_lifecycle_controller'):
            controller = self.context._lifecycle_controller
            if controller:
                from .lifecycle_controller import PTradeLifecycleError
                api_name = func.__name__
                validation_result = controller.validate_api_call(api_name)
                if not validation_result.is_valid:
                    raise PTradeLifecycleError(validation_result.error_message)
                # 记录API调用
                controller.record_api_call(api_name, success=True)

        # 执行原函数
        return func(self, *args, **kwargs)
    return wrapper


class PtradeAPI:
    """ptrade API模拟器（面向对象封装）"""

    def __init__(self, data_context, context, log):
        """初始化API模拟器

        Args:
            data_context: DataContext数据上下文对象
            context: Context上下文对象
            log: 日志对象
        """
        self.data_context = data_context
        self.context = context
        self.log = log

        # 股票池管理
        self.active_universe = set()

        # 缓存
        self._stock_status_cache = {}
        self._stock_date_index = {}  # {stock: (date_dict, sorted_dates)}
        self._prebuilt_index = False  # 标记是否已预构建索引
        self._sorted_status_dates = None  # 缓存排序后的状态历史日期
        self._history_cache = {}  # 缓存get_history结果 {(tuple(stocks), count, field, fq, current_dt): result}

    def prebuild_date_index(self, stocks=None):
        """预构建股票日期索引（显著提升性能）"""
        if self._prebuilt_index:
            return

        target_stocks = stocks if stocks else list(self.data_context.stock_data_dict.keys())
        print(f"预构建 {len(target_stocks)} 只股票的日期索引...")

        for i, stock in enumerate(target_stocks):
            if (i + 1) % 1000 == 0:
                print(f"  已构建 {i + 1}/{len(target_stocks)}")
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                if isinstance(stock_df, pd.DataFrame) and isinstance(stock_df.index, pd.DatetimeIndex):
                    date_dict = {date: idx for idx, date in enumerate(stock_df.index)}
                    sorted_dates = list(stock_df.index)
                    self._stock_date_index[stock] = (date_dict, sorted_dates)
            except:
                pass

        self._prebuilt_index = True
        print(f"  完成！已构建 {len(self._stock_date_index)} 只股票的索引")

    def get_stock_date_index(self, stock):
        """获取股票日期索引，返回 (date_dict, sorted_dates) 元组"""
        if stock not in self._stock_date_index:
            # 延迟构建单只股票索引
            stock_df = self.data_context.stock_data_dict[stock]
            if isinstance(stock_df, pd.DataFrame) and isinstance(stock_df.index, pd.DatetimeIndex):
                date_dict = {date: idx for idx, date in enumerate(stock_df.index)}
                sorted_dates = list(stock_df.index)
                self._stock_date_index[stock] = (date_dict, sorted_dates)
            else:
                self._stock_date_index[stock] = ({}, [])
        return self._stock_date_index.get(stock, ({}, []))

    def get_adjusted_price(self, stock, date, price_type='close', fq='none'):
        """获取复权后的价格

        Args:
            stock: 股票代码
            date: 日期
            price_type: 价格类型 (close/open/high/low)
            fq: 复权类型 ('none'-不复权, 'pre'-前复权, 'post'-后复权)
            stock_data_dict: 股票数据字典
            exrights_dict: 除权数据字典

        Returns:
            复权后价格
        """
        if fq == 'none' or stock not in self.data_context.stock_data_dict:
            # 不复权，直接返回原始价格
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                return stock_df.loc[date, price_type]
            except:
                return np.nan

        if fq == 'pre' and stock in self.data_context.exrights_dict:
            # 前复权
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                exrights_df = self.data_context.exrights_dict[stock]

                original_price = stock_df.loc[date, price_type]

                # 找到该日期对应的复权因子
                date_ts = pd.Timestamp(date)
                date_str = date_ts.strftime('%Y%m%d')

                # exrights的index是字符串格式YYYYMMDD
                if date_str in exrights_df.index:
                    exer_a = exrights_df.loc[date_str, 'exer_backward_a']
                    exer_b = exrights_df.loc[date_str, 'exer_backward_b']
                    # 前复权公式: 复权价 = (原始价 - b) / a
                    return (original_price - exer_b) / exer_a if exer_a != 0 else original_price
                else:
                    # 该日期没有除权，返回原始价
                    return original_price
            except:
                return np.nan

        # 其他情况返回原始价
        try:
            stock_df = self.data_context.stock_data_dict[stock]
            return stock_df.loc[date, price_type]
        except:
            return np.nan
        
    # ==================== 基础API ====================

    def get_research_path(self):
        """返回研究目录路径"""
        return '../../../research/'

    def get_Ashares(self, date=None):
        """返回A股代码列表，支持历史查询"""
        if date is None:
            date = self.context.current_dt

        target_date = pd.Timestamp(date)

        if self.data_context.stock_metadata.empty:
            return list(self.data_context.stock_data_dict.keys())

        listed = pd.to_datetime(self.data_context.stock_metadata['listed_date'], format='mixed') <= target_date
        not_delisted = (
            (self.data_context.stock_metadata['de_listed_date'] == '2900-01-01') |
            (pd.to_datetime(self.data_context.stock_metadata['de_listed_date'], errors='coerce', format='mixed') > target_date)
        )

        return self.data_context.stock_metadata[listed & not_delisted].index.tolist()

    def get_trade_days(self, start_date=None, end_date=None, count=None):
        """获取指定范围交易日列表

        Args:
            start_date: 开始日期（与count二选一）
            end_date: 结束日期（默认当前回测日期）
            count: 往前count个交易日（与start_date二选一）
        """
        trade_days_df = self.data_context.stock_data_store['/trade_days']
        all_trade_days = trade_days_df.index

        if end_date is None:
            end_dt = self.context.current_dt
        else:
            end_dt = pd.Timestamp(str(end_date))

        if count is not None:
            if start_date is not None:
                raise ValueError("start_date和count不能同时使用")
            # 找到end_date的位置
            valid_days = all_trade_days[all_trade_days <= end_dt]
            if len(valid_days) == 0:
                return []
            # 往前取count个交易日（包含end_date）
            trade_days = valid_days[-count:]
        else:
            # 使用start_date和end_date范围
            trade_days = all_trade_days[all_trade_days <= end_dt]
            if start_date is not None:
                start_dt = pd.Timestamp(str(start_date))
                trade_days = trade_days[trade_days >= start_dt]

        return [d.strftime('%Y-%m-%d') for d in trade_days]

    def get_all_trades_days(self, date=None):
        """获取某日期之前的所有交易日列表

        Args:
            date: 截止日期（默认当前回测日期）
        """
        return self.get_trade_days(end_date=date)

    def get_trading_day(self, day=0):
        """获取当前时间数天前或数天后的交易日期

        Args:
            day: 偏移天数（正数向后，负数向前，0表示当天或上一交易日，默认0）

        Returns:
            交易日期字符串，如 '2024-01-15'
        """
        base_date = self.context.current_dt

        trade_days_df = self.data_context.stock_data_store['/trade_days']
        all_trade_days = trade_days_df.index

        if base_date in all_trade_days:
            base_idx = all_trade_days.get_loc(base_date)
        else:
            valid_days = all_trade_days[all_trade_days <= base_date]
            if len(valid_days) == 0:
                base_idx = 0
            else:
                base_idx = all_trade_days.get_loc(valid_days[-1])

        target_idx = base_idx + day

        if target_idx < 0 or target_idx >= len(all_trade_days):
            return None

        return all_trade_days[target_idx].strftime('%Y-%m-%d')

    # ==================== 基本面API ====================

    # 定义字段所属表的映射
    FUNDAMENTAL_TABLES = {
        'valuation': ['pe_ttm', 'pb', 'ps_ttm', 'pcf', 'total_value', 'float_value'],
        'profit_ability': ['roe', 'roa', 'gross_income_ratio', 'net_profit_ratio',
                           'roe_ttm', 'roa_ttm', 'gross_income_ratio_ttm', 'net_profit_ratio_ttm'],
        'growth_ability': ['operating_revenue_grow_rate', 'net_profit_grow_rate',
                           'total_asset_grow_rate', 'basic_eps_yoy', 'np_parent_company_yoy'],
        'operating_ability': ['total_asset_turnover_rate', 'current_assets_turnover_rate',
                              'accounts_receivables_turnover_rate', 'inventory_turnover_rate', 'turnover_rate'],
        'debt_paying_ability': ['current_ratio', 'quick_ratio', 'debt_equity_ratio',
                                'interest_cover', 'roic', 'roa_ebit_ttm'],
    }

    @timing
    def get_fundamentals(self, stocks, table, fields, date):
        """获取基本面数据"""
        if table == 'valuation':
            data_dict = self.data_context.valuation_dict
        else:
            if table not in self.FUNDAMENTAL_TABLES:
                raise ValueError(f"Invalid table: {table}. Valid tables: {list(self.FUNDAMENTAL_TABLES.keys())}")

            valid_fields = self.FUNDAMENTAL_TABLES[table]
            for field in fields:
                if field not in valid_fields:
                    raise ValueError(f"Field '{field}' does not belong to table '{table}'. Valid fields: {valid_fields}")

            data_dict = self.data_context.fundamentals_dict

        query_ts = pd.Timestamp(date)
        result_data = {}

        for stock in stocks:
            if stock not in data_dict:
                continue

            try:
                df = data_dict[stock]

                if df is None or len(df) == 0:
                    continue

                idx = df.index.searchsorted(query_ts, side='right')

                if idx > 0:
                    nearest_date = df.index[idx - 1]
                elif len(df.index) > 0:
                    nearest_date = df.index[0]
                else:
                    continue

                row = df.loc[nearest_date]

                stock_data = {}
                for field in fields:
                    stock_data[field] = row[field] if field in row else None

                if stock_data:
                    result_data[stock] = stock_data

            except Exception as e:
                print(f"读取{table}数据失败: stock={stock}, fields={fields}, error={e}")
                import traceback
                traceback.print_exc()
                raise

        return pd.DataFrame.from_dict(result_data, orient='index') if result_data else pd.DataFrame()

    # ==================== 行情API ====================

    class PanelLike(dict):
        """模拟pandas.Panel"""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._stock_list = None

        def __getitem__(self, key):
            if key in self:
                return super().__getitem__(key)

            if self._stock_list is None and self:
                first_df = next(iter(self.values()))
                self._stock_list = list(first_df.columns)

            if self._stock_list and key in self._stock_list:
                stock_data = {}
                for field, df in self.items():
                    if key in df.columns:
                        stock_data[field] = df[key]
                return pd.DataFrame(stock_data)

            raise KeyError(key)

        @property
        def empty(self):
            if not self:
                return True
            return all(df.empty for df in self.values())

        @property
        def columns(self):
            if not self:
                return pd.Index([])
            first_df = next(iter(self.values()))
            return first_df.columns

    def get_price(self, security, start_date=None, end_date=None, frequency='1d', fields=None, fq=None, count=None):
        """获取历史行情数据"""
        if isinstance(fields, str):
            fields_list = [fields]
        elif fields is None:
            fields_list = ['open', 'high', 'low', 'close', 'volume', 'money', 'price']
        else:
            fields_list = fields

        is_single_stock = isinstance(security, str)
        stocks = [security] if is_single_stock else security

        if count is not None:
            end_dt = pd.Timestamp(end_date) if end_date else self.context.current_dt
            result = {}
            for stock in stocks:
                if stock not in self.data_context.stock_data_dict:
                    continue

                stock_df = self.data_context.stock_data_dict[stock]
                if not isinstance(stock_df, pd.DataFrame):
                    continue

                try:
                    date_dict, _ = self.get_stock_date_index(stock)
                    current_idx = date_dict.get(end_dt) or stock_df.index.get_loc(end_dt)
                except:
                    continue

                slice_df = stock_df.iloc[max(0, current_idx - count):current_idx]
                result[stock] = slice_df
        else:
            start_dt = pd.Timestamp(start_date) if start_date else None
            end_dt = pd.Timestamp(end_date) if end_date else self.context.current_dt

            result = {}
            for stock in stocks:
                if stock not in self.data_context.stock_data_dict:
                    continue

                stock_df = self.data_context.stock_data_dict[stock]
                if not isinstance(stock_df, pd.DataFrame):
                    continue

                if start_dt:
                    mask = (stock_df.index >= start_dt) & (stock_df.index < end_dt)
                else:
                    mask = stock_df.index < end_dt

                slice_df = stock_df[mask]
                result[stock] = slice_df

        if fq == 'pre':
            for stock in list(result.keys()):
                stock_df = result[stock]
                if isinstance(stock_df, pd.DataFrame):
                    adjusted_df = stock_df.copy()
                    price_cols = ['open', 'high', 'low', 'close', 'price']
                    for col in price_cols:
                        if col in adjusted_df.columns:
                            for date_idx in adjusted_df.index:
                                adjusted_price = self.get_adjusted_price(stock, date_idx, col, fq='pre')
                                if not np.isnan(adjusted_price):
                                    adjusted_df.loc[date_idx, col] = adjusted_price
                    result[stock] = adjusted_df

        if not result:
            return pd.DataFrame()

        if is_single_stock:
            stock_df = result.get(security)
            if stock_df is None:
                return pd.DataFrame()
            return stock_df[fields_list] if len(fields_list) > 0 else stock_df

        if len(fields_list) == 1:
            field_name = fields_list[0]
            data = {stock: stock_df[field_name] for stock, stock_df in result.items() if field_name in stock_df.columns}
            return pd.DataFrame(data) if data else pd.DataFrame()

        panel_data = {}
        for field_name in fields_list:
            data = {stock: stock_df[field_name] for stock, stock_df in result.items() if field_name in stock_df.columns}
            panel_data[field_name] = pd.DataFrame(data)

        return self.PanelLike(panel_data)

    @timing
    def get_history(self, count, frequency='1d', field='close', security_list=None, fq=None, include=False, fill='nan', is_dict=False):
        """模拟通用ptrade的get_history（优化批量处理+缓存）"""
        if isinstance(field, str):
            fields = [field]
        else:
            fields = field if field else ['close']

        stocks = security_list if security_list else []
        if isinstance(stocks, str):
            stocks = [stocks]

        # 批量快速返回空结果
        if not stocks:
            return {} if is_dict else pd.DataFrame()

        current_dt = self.context.current_dt

        # 缓存键：使用frozen set避免列表顺序问题，但这里保持tuple更快
        field_key = tuple(fields) if len(fields) > 1 else fields[0]
        cache_key = (tuple(sorted(stocks)), count, field_key, fq, current_dt, include)

        # 检查缓存
        if cache_key in self._history_cache:
            return self._history_cache[cache_key]

        # 优化1: 批量预加载股票数据（减少LazyDataDict的重复加载）
        stock_dfs = {}
        for stock in stocks:
            if stock in self.data_context.stock_data_dict:
                stock_dfs[stock] = self.data_context.stock_data_dict[stock]
            elif stock in self.data_context.benchmark_data:
                stock_dfs[stock] = self.data_context.benchmark_data[stock]

        # 优化2: 批量获取索引位置
        stock_info = {}
        for stock, data_source in stock_dfs.items():
            if not isinstance(data_source, pd.DataFrame):
                continue
            try:
                date_dict, _ = self.get_stock_date_index(stock)
                current_idx = date_dict.get(current_dt)
                if current_idx is None:
                    current_idx = data_source.index.get_loc(current_dt)
                stock_info[stock] = (data_source, current_idx)
            except:
                continue

        # 优化3+4: 批量切片+复权（减少循环开销）
        result = {}

        # 分离需要复权和不需要复权的股票
        needs_adj = fq == 'pre' and self.data_context.adj_pre_cache

        for stock, (data_source, current_idx) in stock_info.items():
            if include:
                start_idx = max(0, current_idx - count + 1)
                end_idx = current_idx + 1
            else:
                start_idx = max(0, current_idx - count)
                end_idx = current_idx

            slice_df = data_source.iloc[start_idx:end_idx]

            if len(slice_df) == 0:
                continue

            # 只对需要复权的股票copy和处理
            if needs_adj and stock in self.data_context.adj_pre_cache:
                slice_df = slice_df.copy()
                adj_factors = self.data_context.adj_pre_cache[stock]

                # 快速路径：索引对齐直接iloc切片
                aligned_factors = adj_factors.iloc[start_idx:end_idx]

                # 向量化应用复权（一次性处理所有价格列）
                price_cols = [col for col in ['open', 'high', 'low', 'close'] if col in slice_df.columns]
                if price_cols:
                    slice_df[price_cols] = slice_df[price_cols].multiply(aligned_factors, axis=0)

            # 直接提取numpy数组
            stock_result = {field_name: slice_df[field_name].values
                          for field_name in fields if field_name in slice_df.columns}

            if stock_result:
                result[stock] = stock_result

        # 转换为返回格式并缓存
        if not result:
            final_result = {} if is_dict else pd.DataFrame()
        elif is_dict:
            final_result = result
        else:
            is_single_stock = isinstance(security_list, str)
            stocks_list = [security_list] if is_single_stock else stocks

            if is_single_stock:
                if stocks_list[0] not in result:
                    final_result = pd.DataFrame()
                else:
                    df_data = {field_name: result[stocks_list[0]][field_name] for field_name in fields if field_name in result[stocks_list[0]]}
                    final_result = pd.DataFrame(df_data)

            elif len(fields) == 1:
                field_name = fields[0]
                df_data = {stock: result[stock][field_name] for stock in stocks_list if stock in result and field_name in result[stock]}
                final_result = pd.DataFrame(df_data)

            else:
                panel_data = {}
                for field_name in fields:
                    df_data = {stock: result[stock][field_name] for stock in stocks_list if stock in result and field_name in result[stock]}
                    panel_data[field_name] = pd.DataFrame(df_data)

                class _PanelLike(dict):
                    @property
                    def empty(self):
                        return not self or all(df.empty for df in self.values())

                final_result = _PanelLike(panel_data)

        # 缓存结果（限制缓存大小）
        if len(self._history_cache) > 100:
            # LRU淘汰：删除最旧的
            self._history_cache.pop(next(iter(self._history_cache)))
        self._history_cache[cache_key] = final_result

        return final_result

    # ==================== 股票信息API ====================

    def get_stock_blocks(self, stock):
        """获取股票所属板块"""
        if not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
            try:
                blocks_str = self.data_context.stock_metadata.loc[stock, 'blocks']
                if pd.notna(blocks_str) and blocks_str:
                    return json.loads(blocks_str)
            except:
                pass
        return {}

    def get_stock_info(self, stocks, field=None):
        """获取股票基础信息"""
        if isinstance(stocks, str):
            stocks = [stocks]

        if field is None:
            field = ['stock_name', 'listed_date', 'de_listed_date']
        elif isinstance(field, str):
            field = [field]

        result = {}
        for stock in stocks:
            stock_info = {}

            if not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                meta_row = self.data_context.stock_metadata.loc[stock]
                for f in field:
                    if f in meta_row.index:
                        stock_info[f] = meta_row[f]

            if 'stock_name' in field and 'stock_name' not in stock_info:
                stock_info['stock_name'] = stock
            if 'listed_date' in field and 'listed_date' not in stock_info:
                stock_info['listed_date'] = '2010-01-01'
            if 'de_listed_date' in field and 'de_listed_date' not in stock_info:
                stock_info['de_listed_date'] = '2900-01-01'

            result[stock] = stock_info

        return result

    def get_stock_name(self, stocks):
        """获取股票名称"""
        is_single = isinstance(stocks, str)
        if is_single:
            stocks = [stocks]

        result = {}
        for stock in stocks:
            if not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                result[stock] = self.data_context.stock_metadata.loc[stock, 'stock_name']
            else:
                result[stock] = stock

        return result[stocks[0]] if is_single else result

    @timing
    def get_stock_status(self, stocks, query_type='ST', query_date=None):
        """获取股票状态"""
        if isinstance(stocks, str):
            stocks = [stocks]

        query_dt = self.context.current_dt if query_date is None and self.context else pd.Timestamp(str(query_date or pd.Timestamp.now()))
        result = {}

        for stock in stocks:
            cache_key = (query_dt, stock, query_type)
            if cache_key in self._stock_status_cache:
                result[stock] = self._stock_status_cache[cache_key]
                continue

            is_problematic = False

            if self.data_context.stock_status_history:
                # 缓存排序后的日期列表（只排序一次）
                if self._sorted_status_dates is None:
                    self._sorted_status_dates = sorted(self.data_context.stock_status_history.keys())

                query_date_str = query_dt.strftime('%Y%m%d')

                # 二分查找最近日期
                pos = bisect.bisect_right(self._sorted_status_dates, query_date_str)
                nearest_date = self._sorted_status_dates[pos - 1] if pos > 0 else None

                if nearest_date and query_type in self.data_context.stock_status_history[nearest_date]:
                    status_dict = self.data_context.stock_status_history[nearest_date][query_type]
                    is_problematic = status_dict.get(stock, False) is True
                    self._stock_status_cache[cache_key] = is_problematic
                    result[stock] = is_problematic
                    continue

            if query_type == 'ST' and not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                stock_name = self.data_context.stock_metadata.loc[stock, 'stock_name']
                is_problematic = 'ST' in str(stock_name)

            elif query_type == 'HALT' and stock in self.data_context.stock_data_dict:
                stock_df = self.data_context.stock_data_dict[stock]
                if isinstance(stock_df, pd.DataFrame):
                    try:
                        valid_dates = stock_df.index[stock_df.index <= query_dt]
                        if len(valid_dates) > 0:
                            nearest_date = valid_dates[-1]
                            volume = stock_df.loc[nearest_date, 'volume']
                            is_problematic = (volume == 0 or pd.isna(volume))
                    except:
                        pass

            elif query_type == 'DELISTING' and not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                try:
                    de_listed_date = pd.Timestamp(self.data_context.stock_metadata.loc[stock, 'de_listed_date'])
                    is_problematic = (de_listed_date.year < 2900 and de_listed_date <= query_dt)
                except:
                    pass

            self._stock_status_cache[cache_key] = is_problematic
            result[stock] = is_problematic

        return result

    def get_stock_exrights(self, stock_code, date=None):
        """获取股票除权除息信息"""
        try:
            exrights_df = self.data_context.stock_data_store[f'/exrights/{stock_code}']

            if date is not None:
                query_date = pd.Timestamp(str(date))
                if query_date in exrights_df.index:
                    return exrights_df.loc[[query_date]]
                else:
                    return None
            else:
                return exrights_df
        except KeyError:
            return None
        except Exception:
            return None

    # ==================== 指数/行业API ====================

    def get_index_stocks(self, index_code, date=None):
        """获取指数成份股"""
        if not self.data_context.index_constituents:
            return []

        if date:
            date_str = pd.Timestamp(str(date)).strftime('%Y%m%d')
            if date_str in self.data_context.index_constituents and index_code in self.data_context.index_constituents[date_str]:
                return self.data_context.index_constituents[date_str][index_code]
        else:
            if self.data_context.index_constituents:
                latest_date = max(self.data_context.index_constituents.keys())
                if index_code in self.data_context.index_constituents[latest_date]:
                    return self.data_context.index_constituents[latest_date][index_code]

        return []

    def get_industry_stocks(self, industry_code=None):
        """推导行业成份股"""
        if self.data_context.stock_metadata.empty:
            return {} if industry_code is None else []

        industries = {}
        for stock_code, row in self.data_context.stock_metadata.iterrows():
            try:
                blocks = json.loads(row['blocks'])
                if 'HY' in blocks and blocks['HY']:
                    ind_code = blocks['HY'][0][0]
                    ind_name = blocks['HY'][0][1]

                    if ind_code not in industries:
                        industries[ind_code] = {
                            'name': ind_name,
                            'stocks': []
                        }
                    industries[ind_code]['stocks'].append(stock_code)
            except:
                pass

        if industry_code is None:
            return industries
        else:
            return industries.get(industry_code, {}).get('stocks', [])

    # ==================== 涨跌停API ====================

    def _get_price_limit_ratio(self, stock):
        """获取股票涨跌停幅度"""
        if stock.startswith('688') and stock.endswith('.SS'):
            return 0.20
        elif stock.startswith('30') and stock.endswith('.SZ'):
            return 0.20
        elif stock.endswith('.BJ'):
            return 0.30
        else:
            return 0.10

    def check_limit(self, security, query_date=None):
        """检查涨跌停状态"""
        if isinstance(security, str):
            securities = [security]
        else:
            securities = security

        if query_date is None:
            query_dt = self.context.current_dt if self.context else pd.Timestamp.now()
        else:
            query_dt = pd.Timestamp(query_date)

        result = {}
        for stock in securities:
            status = 0

            if stock not in self.data_context.stock_data_dict:
                result[stock] = status
                continue

            stock_df = self.data_context.stock_data_dict[stock]
            if not isinstance(stock_df, pd.DataFrame):
                result[stock] = status
                continue

            try:
                date_dict, _ = self.get_stock_date_index(stock)
                idx = date_dict.get(query_dt) or stock_df.index.get_loc(query_dt)

                if idx == 0:
                    result[stock] = status
                    continue

                current_close = stock_df.iloc[idx]['close']
                current_high = stock_df.iloc[idx]['high']
                current_low = stock_df.iloc[idx]['low']
                prev_close = stock_df.iloc[idx-1]['close']

                if np.isnan(prev_close) or prev_close <= 0:
                    result[stock] = status
                    continue

                limit_ratio = self._get_price_limit_ratio(stock)
                limit_up_price = prev_close * (1 + limit_ratio)
                limit_down_price = prev_close * (1 - limit_ratio)

                is_up_limit = (current_close >= current_high * 0.998) and (current_close >= limit_up_price * 0.998)
                is_down_limit = (current_close <= current_low * 1.002) and (current_close <= limit_down_price * 1.002)

                if is_up_limit:
                    status = 1
                elif is_down_limit:
                    status = -1

                result[stock] = status
            except:
                result[stock] = 0

        return result

    # ==================== 交易API ====================

    @validate_lifecycle
    def order(self, security, amount, limit_price=None):
        """买卖指定数量的股票

        Args:
            security: 股票代码
            amount: 交易数量，正数表示买入，负数表示卖出
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        if amount == 0:
            return None

        # 使用blotter创建订单
        if self.context and self.context.blotter:
            order = self.context.blotter.create_order(security, amount)
            if limit_price is not None:
                order.limit = limit_price
            return order.id
        return None

    @validate_lifecycle
    def order_target(self, stock, amount, limit_price=None):
        """下单到目标数量

        Args:
            stock: 股票代码
            amount: 期望的最终数量
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        from .trading_helpers import (
            get_execution_price, check_order_validity,
            create_order, execute_buy, execute_sell
        )

        current_amount = 0
        if stock in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[stock].amount

        delta = amount - current_amount

        if delta == 0:
            return None

        # 获取执行价格
        execution_price = get_execution_price(
            stock, self.context, self.data_context,
            self.get_stock_date_index, limit_price
        )
        if execution_price is None:
            self.log.warning(f"【订单失败】{stock} | 原因: 无法获取价格")
            return None

        # 检查涨跌停
        limit_status = self.check_limit(stock, self.context.current_dt)[stock]
        if not check_order_validity(stock, delta, limit_status, self.log):
            return None

        # 创建订单
        order_id, order = create_order(stock, delta, execution_price, self.context)

        if delta > 0:
            self.log.info(f"生成订单，订单号:{order_id}，股票代码：{stock}，数量：买入{delta}股")
            success = execute_buy(stock, delta, execution_price, self.context, self.log)
        else:
            self.log.info(f"生成订单，订单号:{order_id}，股票代码：{stock}，数量：卖出{abs(delta)}股")
            success = execute_sell(stock, abs(delta), execution_price, self.context, self.log)

        if success:
            order.status = '8'
            order.filled = delta

        return order.id if success else None

    @validate_lifecycle
    def order_value(self, stock, value, limit_price=None):
        """按金额下单

        Args:
            stock: 股票代码
            value: 股票价值
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        from .trading_helpers import (
            get_execution_price, check_order_validity,
            create_order, execute_buy
        )

        # 获取执行价格
        current_price = get_execution_price(
            stock, self.context, self.data_context,
            self.get_stock_date_index, limit_price
        )
        if current_price is None:
            self.log.warning(f"【下单失败】{stock} | 原因: 获取价格数据失败")
            return None

        # 计算买入数量（向下取整到100股）
        amount = int(value / current_price / 100) * 100
        if amount <= 0:
            self.log.warning(f"【下单失败】{stock} | 原因: 金额不足 (分配{value:.2f}元, 价格{current_price:.2f}元, 不足100股)")
            return None

        # 检查涨停
        limit_status = self.check_limit(stock, self.context.current_dt)[stock]
        if not check_order_validity(stock, amount, limit_status, self.log):
            return None

        # 创建订单
        order_id, order = create_order(stock, amount, current_price, self.context)

        self.log.info(f"生成订单，订单号:{order_id}，股票代码：{stock}，数量：买入{amount}股")

        # 执行订单
        success = execute_buy(stock, amount, current_price, self.context, self.log)

        if success:
            order.status = '8'
            order.filled = amount

        return order.id if success else None

    @validate_lifecycle
    def order_target_value(self, stock, value, limit_price=None):
        """调整股票持仓市值到目标价值

        Args:
            stock: 股票代码
            value: 期望的股票最终价值
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        # 获取当前持仓市值
        current_value = 0.0
        if stock in self.context.portfolio.positions:
            position = self.context.portfolio.positions[stock]
            current_value = position.amount * position.last_sale_price

        # 计算需要调整的价值
        delta_value = value - current_value

        if abs(delta_value) < 1:  # 价值差异小于1元，不调整
            return None

        # 使用 order_value 下单
        return self.order_value(stock, delta_value, limit_price)

    def get_open_orders(self):
        """获取未成交订单"""
        if self.context and self.context.blotter:
            return self.context.blotter.open_orders
        return []

    def get_orders(self, security=None):
        """获取当日全部订单

        Args:
            security: 股票代码，None表示获取所有订单

        Returns:
            订单列表
        """
        if not self.context or not self.context.blotter:
            return []

        if security is None:
            return self.context.blotter.open_orders
        else:
            return [o for o in self.context.blotter.open_orders if o.symbol == security]

    def get_order(self, order_id):
        """获取指定订单

        Args:
            order_id: 订单id

        Returns:
            Order对象或None
        """
        if not self.context or not self.context.blotter:
            return None

        for order in self.context.blotter.open_orders:
            if order.id == order_id:
                return order
        return None

    def get_trades(self):
        """获取当日成交订单

        Returns:
            成交订单列表
        """
        # 回测中所有已成交订单都会从open_orders移除，需要单独记录
        # 这里简化实现，返回空列表
        return []

    def get_position(self, security):
        """获取持仓信息

        Args:
            security: 股票代码

        Returns:
            Position对象或None
        """
        if self.context and self.context.portfolio:
            return self.context.portfolio.positions.get(security)
        return None

    def cancel_order(self, order):
        """取消订单"""
        if self.context and self.context.blotter:
            return self.context.blotter.cancel_order(order)
        return False

    # ==================== 配置API ====================

    @validate_lifecycle
    def set_benchmark(self, benchmark):
        """设置基准"""
        if benchmark not in self.data_context.benchmark_data:
            self.log.warning(f"基准 {benchmark} 不存在，保持当前基准")
            return
        self.context.benchmark = benchmark
        self.log.info(f"设置基准: {benchmark}")

    @validate_lifecycle
    def set_universe(self, stocks):
        """设置股票池并预加载数据"""
        if isinstance(stocks, list):
            new_stocks = set(stocks)
            to_preload = new_stocks - self.active_universe
            if to_preload:
                self.log.debug(f"预加载 {len(to_preload)} 只新股票数据")
                for stock in to_preload:
                    if stock in self.data_context.stock_data_dict:
                        _ = self.data_context.stock_data_dict[stock]
            self.active_universe = new_stocks
            self.log.debug(f"股票池更新: {len(self.active_universe)} 只")
        else:
            self.log.debug(f"设置股票池: {stocks}")

    def is_trade(self):
        """是否实盘"""
        return False

    @validate_lifecycle
    def set_commission(self, commission_ratio=0.0003, min_commission=5.0, type="STOCK"):
        """设置交易佣金"""
        if commission_ratio is not None:
            self.context.commission_ratio = commission_ratio
        if min_commission is not None:
            self.context.min_commission = min_commission
        if type is not None:
            self.context.commission_type = type

    @validate_lifecycle
    def set_slippage(self, slippage=0.0):
        """设置滑点"""
        if slippage is not None:
            self.context.slippage = slippage

    @validate_lifecycle
    def set_fixed_slippage(self, fixedslippage=0.001):
        """设置固定滑点"""
        if fixedslippage is not None:
            self.context.fixed_slippage = fixedslippage

    @validate_lifecycle
    def set_limit_mode(self, limit_mode='LIMIT'):
        """设置下单限制模式"""
        self.context.limit_mode = limit_mode

    @validate_lifecycle
    def set_volume_ratio(self, volume_ratio=0.25):
        """设置成交比例

        Args:
            volume_ratio: 成交比例，默认0.25，即单笔最大成交量为当日成交量的1/4
        """
        self.context.volume_ratio = volume_ratio

    @validate_lifecycle
    def set_yesterday_position(self, poslist):
        """设置底仓（回测用）

        Args:
            poslist: 持仓列表，每个元素为字典 {'security': 股票代码, 'amount': 数量, 'cost_basis': 成本价}
        """
        if not isinstance(poslist, list):
            self.log.warning("set_yesterday_position 参数必须是列表")
            return

        from simtradelab.ptrade.object import Position
        for pos_info in poslist:
            security = pos_info.get('security')
            amount = pos_info.get('amount', 0)
            cost_basis = pos_info.get('cost_basis', 0)

            if security and amount > 0 and cost_basis > 0:
                self.context.portfolio.positions[security] = Position(security, amount, cost_basis)
                self.log.info(f"设置底仓: {security}, 数量:{amount}, 成本价:{cost_basis}")

    def run_interval(self, context, func, seconds=10):
        """定时运行函数（秒级，仅实盘）

        Args:
            context: Context对象
            func: 自定义函数，接受context参数
            seconds: 时间间隔（秒），最小3秒
        """
        _ = (context, func, seconds)  # 回测中不执行
        pass

    def run_daily(self, context, func, time='9:31'):
        """定时运行函数

        Args:
            context: Context对象
            func: 自定义函数，接受context参数
            time: 触发时间，格式HH:MM
        """
        _ = (context, func, time)  # 回测中不执行
        pass
