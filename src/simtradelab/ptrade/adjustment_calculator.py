# -*- coding: utf-8 -*-
"""
统一复权计算器

整合StockData和PtradeAPI中的复权逻辑
"""

import pandas as pd
from typing import Optional, Dict, Any


class AdjustmentCalculator:
    """复权计算器

    统一处理前复权、后复权计算
    """

    def __init__(self, data_context):
        """初始化复权计算器

        Args:
            data_context: 数据上下文对象
        """
        self.data_context = data_context

    def apply_pre_adjustment_to_data(self, stock: str, data: Dict[str, Any],
                                     strategy_date: pd.Timestamp) -> Dict[str, Any]:
        """对股票数据应用前复权

        用于StockData对象加载数据时使用

        注意：此方法暂时不应用复权，data[stock]返回未复权数据
        只有get_history(fq='pre')才返回前复权数据

        Args:
            stock: 股票代码
            data: 包含价格字段的字典
            strategy_date: 策略当前日期

        Returns:
            应用复权后的数据字典
        """
        # data[stock]应该返回未复权数据，不做任何调整
        return data

    def get_adjusted_price(self, stock: str, date: pd.Timestamp,
                          price_type: str = 'close', fq: str = 'none') -> float:
        """获取复权后的价格

        用于PtradeAPI获取特定日期的复权价格

        Args:
            stock: 股票代码
            date: 日期
            price_type: 价格类型 (close/open/high/low)
            fq: 复权类型 ('none'-不复权, 'pre'-前复权, 'post'-后复权)

        Returns:
            复权后价格，失败返回NaN
        """

        if fq == 'none' or stock not in self.data_context.stock_data_dict:
            # 不复权，直接返回原始价格
            return self._get_original_price(stock, date, price_type)

        if fq == 'pre':
            return self._get_pre_adjusted_price(stock, date, price_type)
        elif fq == 'post':
            # 后复权暂不实现，返回原始价格
            return self._get_original_price(stock, date, price_type)

        # 其他情况返回原始价
        return self._get_original_price(stock, date, price_type)

    def _get_original_price(self, stock: str, date: pd.Timestamp, price_type: str) -> float:
        """获取原始价格"""
        import numpy as np

        try:
            stock_df = self.data_context.stock_data_dict[stock]
            return stock_df.loc[date, price_type]
        except:
            return np.nan

    def _get_pre_adjusted_price(self, stock: str, date: pd.Timestamp, price_type: str) -> float:
        """获取前复权价格

        使用adj_pre_cache中的累计未来分红计算
        前复权价 = 未复权价 - 累计未来分红
        """
        import numpy as np

        # 优先使用adj_pre_cache（累计分红方式）
        if (hasattr(self.data_context, 'adj_pre_cache') and
            self.data_context.adj_pre_cache and
            stock in self.data_context.adj_pre_cache):

            try:
                stock_df = self.data_context.stock_data_dict[stock]
                cum_dividend = self.data_context.adj_pre_cache[stock]

                date_normalized = pd.Timestamp(date).normalize()
                original_price = stock_df.loc[date_normalized, price_type]

                if date_normalized in cum_dividend.index:
                    dividend = cum_dividend.loc[date_normalized]
                    return original_price - dividend
                else:
                    return original_price
            except:
                return np.nan

        # 降级方案：使用旧的exrights方式
        if not hasattr(self.data_context, 'exrights_dict') or stock not in self.data_context.exrights_dict:
            return self._get_original_price(stock, date, price_type)

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
                if exer_a != 0:
                    return (original_price - exer_b) / exer_a
                else:
                    return original_price
            else:
                # 该日期没有除权，返回原始价
                return original_price
        except:
            return np.nan

    def precompute_adjustment_factors(self, stock: str, end_date: pd.Timestamp) -> Optional[pd.Series]:
        """预计算前复权因子

        Args:
            stock: 股票代码
            end_date: 截止日期（只计算到此日期的因子）

        Returns:
            前复权因子序列，失败返回None
        """
        if not hasattr(self.data_context, 'exrights_dict') or stock not in self.data_context.exrights_dict:
            return None

        try:
            stock_df = self.data_context.stock_data_dict[stock]
            exrights_df = self.data_context.exrights_dict[stock]

            # 只计算到end_date的数据
            stock_df_filtered = stock_df[stock_df.index <= end_date]

            # 计算每个交易日的前复权因子
            factors = pd.Series(index=stock_df_filtered.index, dtype=float)

            for date in stock_df_filtered.index:
                date_str = date.strftime('%Y%m%d')
                if date_str in exrights_df.index:
                    exer_a = exrights_df.loc[date_str, 'exer_backward_a']
                    # exer_b = exrights_df.loc[date_str, 'exer_backward_b']  # 暂未使用
                    # 简化的前复权因子（假设b=0的简单情况）
                    factors.loc[date] = 1.0 / exer_a if exer_a != 0 else 1.0
                else:
                    factors.loc[date] = 1.0

            return factors
        except:
            return None
