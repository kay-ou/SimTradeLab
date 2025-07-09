# -*- coding: utf-8 -*-
"""
PTrade实盘交易模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ....core.event_bus import EventBus
from .base import BaseAPIRouter

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class LiveTradingAPIRouter(BaseAPIRouter):
    """实盘交易模式API路由器"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        super().__init__(context, event_bus)
        self._supported_apis = {
            "order",
            "order_value",
            "order_target",
            "order_target_value",
            "order_market",
            "cancel_order",
            "cancel_order_ex",
            "get_all_orders",
            "ipo_stocks_order",
            "after_trading_order",
            "after_trading_cancel_order",
            "get_position",
            "get_positions",
            "get_open_orders",
            "get_order",
            "get_orders",
            "get_trades",
            "get_history",
            "get_price",
            "get_snapshot",
            "set_universe",
            "set_benchmark",
            "set_parameters",
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            "get_stock_info",
            "get_fundamentals",
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            "log",
            "check_limit",
            "handle_data",
        }

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在实盘交易模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """实盘交易下单逻辑"""
        if self.event_bus:
            self.event_bus.publish(
                "trading.order.request",
                data={
                    "security": security,
                    "amount": amount,
                    "limit_price": limit_price,
                },
                source="ptrade_adapter",
            )
        return "live_order_placeholder"

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        # 获取当前价格
        current_price = limit_price or 10.0  # 默认价格

        # 计算股数
        amount = int(value / current_price)
        if amount <= 0:
            return None

        return self.order(security, amount, limit_price)

    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定目标数量买卖"""
        # 获取当前持仓
        current_amount = 0
        if security in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[security].amount

        # 计算需要交易的数量
        trade_amount = target_amount - current_amount
        if trade_amount == 0:
            return None

        return self.order(security, trade_amount, limit_price)

    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定持仓市值买卖"""
        # 获取当前价格
        current_price = limit_price or 10.0  # 默认价格

        # 计算目标股数
        target_amount = int(target_value / current_price)

        return self.order_target(security, target_amount, limit_price)

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托"""
        # 实盘交易模式下，市价单不需要指定价格
        return self.order(security, amount, None)

    def cancel_order(self, order_id: str) -> bool:
        """实盘交易撤单"""
        if self.event_bus:
            self.event_bus.publish(
                "trading.cancel_order.request",
                data={"order_id": order_id},
                source="ptrade_adapter",
            )
        return True

    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展"""
        # 在实盘交易模式下，扩展撤单与cancel_order功能相同
        return self.cancel_order(order_id)

    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        # 在实盘交易模式下，返回所有订单
        return self.get_orders()

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        # 实盘交易模式下支持新股申购
        if self.event_bus:
            self.event_bus.publish(
                "trading.ipo_order.request",
                data={"amount_per_stock": amount_per_stock},
                source="ptrade_adapter",
            )
        return ["ipo_order_placeholder"]

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        # 实盘交易模式下支持盘后交易
        if self.event_bus:
            self.event_bus.publish(
                "trading.after_trading_order.request",
                data={
                    "security": security,
                    "amount": amount,
                    "limit_price": limit_price,
                },
                source="ptrade_adapter",
            )
        return "after_trading_order_placeholder"

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        # 实盘交易模式下支持盘后撤单
        if self.event_bus:
            self.event_bus.publish(
                "trading.after_trading_cancel_order.request",
                data={"order_id": order_id},
                source="ptrade_adapter",
            )
        return True

    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓信息"""
        return self.context.portfolio.positions.get(security)

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息"""
        positions = {}
        for security in security_list:
            position = self.get_position(security)
            if position:
                positions[security] = {
                    "sid": position.sid,
                    "amount": position.amount,
                    "enable_amount": position.enable_amount,
                    "cost_basis": position.cost_basis,
                    "last_sale_price": position.last_sale_price,
                    "market_value": position.market_value,
                    "pnl": position.pnl,
                    "returns": position.returns,
                    "today_amount": position.today_amount,
                    "business_type": position.business_type,
                }
            else:
                positions[security] = {
                    "sid": security,
                    "amount": 0,
                    "enable_amount": 0,
                    "cost_basis": 0.0,
                    "last_sale_price": 0.0,
                    "market_value": 0.0,
                    "pnl": 0.0,
                    "returns": 0.0,
                    "today_amount": 0,
                    "business_type": "stock",
                }
        return positions

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单"""
        if not self.context.blotter:
            return []

        open_orders = []
        for order in self.context.blotter.orders.values():
            if order.status in ["new", "submitted", "partially_filled"]:
                if security is None or order.symbol == security:
                    open_orders.append(order)
        return open_orders

    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定订单"""
        if self.context.blotter:
            return self.context.blotter.get_order(order_id)
        return None

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取全部订单"""
        if not self.context.blotter:
            return []

        orders = []
        for order in self.context.blotter.orders.values():
            if security is None or order.symbol == security:
                orders.append(order)

        orders.sort(key=lambda o: o.dt, reverse=True)
        return orders

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单"""
        if not self.context.blotter:
            return []

        trades = []
        for order in self.context.blotter.orders.values():
            if order.status == "filled" and order.filled != 0:
                if security is None or order.symbol == security:
                    trades.append(
                        {
                            "order_id": order.id,
                            "security": order.symbol,
                            "amount": order.filled,
                            "price": order.limit or 0.0,
                            "filled_amount": order.filled,
                            "commission": 0.0,
                            "datetime": order.dt,
                            "side": "buy" if order.amount > 0 else "sell",
                        }
                    )

        trades.sort(key=lambda t: t["datetime"], reverse=True)
        return trades

    def get_history(
        self,
        count: int,
        frequency: str = "1d",
        field: Union[str, List[str]] = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "money",
            "price",
        ],
        security_list: Optional[List[str]] = None,
        fq: Optional[str] = None,
        include: bool = False,
        fill: str = "nan",
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """获取历史行情数据"""
        # 实盘交易模式需要从实时数据源获取
        securities = security_list or self.context.universe or ["000001.XSHE"]

        if isinstance(field, str):
            field = [field]

        if is_dict:
            return {security: {f: [] for f in field} for security in securities}
        else:
            return pd.DataFrame()

    def get_price(
        self,
        security: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取价格数据"""
        # 实盘交易模式需要从实时数据源获取
        return pd.DataFrame()

    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
        # 实盘交易模式需要从实时数据源获取
        data = []
        for security in security_list:
            data.append(
                {
                    "security": security,
                    "current_price": np.random.randn() * 0.01 + 10,
                    "volume": np.random.randint(1000, 10000),
                    "timestamp": pd.Timestamp.now(),
                }
            )
        return pd.DataFrame(data).set_index("security")

    def get_trading_day(self, date: str, offset: int = 0) -> str:
        """获取交易日期"""
        from datetime import datetime, timedelta

        try:
            # 解析输入日期
            if isinstance(date, str):
                base_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                base_date = date

            # 计算偏移
            target_date = base_date + timedelta(days=offset)

            # 简单的工作日逻辑(忽略节假日)
            while target_date.weekday() > 4:  # 0-6: 周一到周日
                if offset > 0:
                    target_date += timedelta(days=1)
                else:
                    target_date -= timedelta(days=1)

            return target_date.strftime("%Y-%m-%d")
        except Exception as e:
            self._logger.error(f"Error calculating trading day: {e}")
            return date

    def get_all_trades_days(self) -> List[str]:
        """获取全部交易日期"""
        from datetime import datetime, timedelta

        try:
            # 生成过去一年的交易日（简化版）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            trading_days = []
            current_date = start_date

            while current_date <= end_date:
                # 只包含工作日（简化版，忽略节假日）
                if current_date.weekday() < 5:  # 0-4: 周一到周五
                    trading_days.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            return trading_days
        except Exception as e:
            self._logger.error(f"Error getting all trading days: {e}")
            return []

    def get_trade_days(self, start_date: str, end_date: str) -> List[str]:
        """获取指定范围交易日期"""
        from datetime import datetime, timedelta

        try:
            # 解析日期
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            trading_days = []
            current_date = start

            while current_date <= end:
                # 只包含工作日（简化版，忽略节假日）
                if current_date.weekday() < 5:  # 0-4: 周一到周五
                    trading_days.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            return trading_days
        except Exception as e:
            self._logger.error(
                f"Error getting trade days from {start_date} to {end_date}: {e}"
            )
            return []

    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息"""
        stock_info = {}

        for security in security_list:
            # 模拟股票基本信息
            if security.endswith(".XSHE"):  # 深圳证券交易所
                market = "SZSE"
                name = f"深圳股票{security[:6]}"
            elif security.endswith(".XSHG"):  # 上海证券交易所
                market = "SSE"
                name = f"上海股票{security[:6]}"
            else:
                market = "Unknown"
                name = f"股票{security}"

            stock_info[security] = {
                "symbol": security,
                "display_name": name,
                "name": name,
                "market": market,
                "type": "stock",
                "lot_size": 100,  # 最小交易单位
                "tick_size": 0.01,  # 最小价格变动单位
                "start_date": "2010-01-01",
                "end_date": "2099-12-31",
            }

        return stock_info

    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息"""
        import random

        try:
            # 模拟财务数据
            data = []
            for stock in stocks:
                row = {"code": stock, "date": date}

                # 根据不同的表格和字段生成模拟数据
                for field in fields:
                    if field in ["revenue", "total_revenue"]:  # 营业收入
                        row[field] = random.uniform(1000000, 10000000)  # 1M-10M
                    elif field in ["net_profit", "net_income"]:  # 净利润
                        row[field] = random.uniform(100000, 1000000)  # 100K-1M
                    elif field in ["total_assets"]:  # 总资产
                        row[field] = random.uniform(10000000, 100000000)  # 10M-100M
                    elif field in ["total_liab"]:  # 总负债
                        row[field] = random.uniform(5000000, 50000000)  # 5M-50M
                    elif field in ["pe_ratio"]:  # 市盈率
                        row[field] = random.uniform(10, 50)
                    elif field in ["pb_ratio"]:  # 市净率
                        row[field] = random.uniform(1, 10)
                    elif field in ["roe"]:  # 净资产收益率
                        row[field] = random.uniform(0.05, 0.25)
                    elif field in ["eps"]:  # 每股收益
                        row[field] = random.uniform(0.1, 5.0)
                    else:
                        row[field] = random.uniform(0, 1000000)

                data.append(row)

            return pd.DataFrame(data)
        except Exception as e:
            self._logger.error(f"Error getting fundamentals: {e}")
            return pd.DataFrame()

    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        self.context.universe = securities
        self._logger.info(f"Universe set to {len(securities)} securities")

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        self.context.benchmark = benchmark
        self._logger.info(f"Benchmark set to {benchmark}")

    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        # 实盘交易模式下不支持设置佣金费率
        self._logger.warning("Setting commission is not supported in live trading mode")

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        # 实盘交易模式下不支持设置滑点
        self._logger.warning("Setting slippage is not supported in live trading mode")

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        # 实盘交易模式下不支持设置固定滑点
        self._logger.warning(
            "Setting fixed slippage is not supported in live trading mode"
        )

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        # 实盘交易模式下不支持设置成交比例
        self._logger.warning(
            "Setting volume ratio is not supported in live trading mode"
        )

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        # 实盘交易模式下不支持设置限制模式
        self._logger.warning("Setting limit mode is not supported in live trading mode")

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        # 实盘交易模式下不支持设置底仓
        self._logger.warning(
            "Setting yesterday position is not supported in live trading mode"
        )

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        # 存储在上下文中
        if not hasattr(self.context, "_parameters"):
            self.context._parameters = {}
        self.context._parameters.update(params)
        self._logger.info(f"Parameters set: {params}")

    def get_MACD(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标"""
        try:
            close_series = pd.Series(close)
            exp1 = close_series.ewm(span=short).mean()
            exp2 = close_series.ewm(span=long).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=m).mean()
            histogram = macd_line - signal_line

            return pd.DataFrame(
                {
                    "MACD": macd_line,
                    "MACD_signal": signal_line,
                    "MACD_hist": histogram * 2,
                }
            )
        except Exception as e:
            self._logger.error(f"Error calculating MACD: {e}")
            periods = len(close)
            return pd.DataFrame(
                {
                    "MACD": np.random.randn(periods) * 0.1,
                    "MACD_signal": np.random.randn(periods) * 0.1,
                    "MACD_hist": np.random.randn(periods) * 0.05,
                }
            )

    def get_KDJ(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标"""
        try:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            highest = high_series.rolling(window=n).max()
            lowest = low_series.rolling(window=n).min()
            rsv = (close_series - lowest) / (highest - lowest) * 100
            k = rsv.ewm(alpha=1 / m1).mean()
            d = k.ewm(alpha=1 / m2).mean()
            j = 3 * k - 2 * d

            return pd.DataFrame({"K": k, "D": d, "J": j})
        except Exception as e:
            self._logger.error(f"Error calculating KDJ: {e}")
            periods = len(close)
            return pd.DataFrame(
                {
                    "K": np.random.uniform(0, 100, periods),
                    "D": np.random.uniform(0, 100, periods),
                    "J": np.random.uniform(0, 100, periods),
                }
            )

    def get_RSI(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标"""
        try:
            close_series = pd.Series(close)
            delta = close_series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=n).mean()
            avg_loss = loss.rolling(window=n).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return pd.DataFrame({"RSI": rsi})
        except Exception as e:
            self._logger.error(f"Error calculating RSI: {e}")
            periods = len(close)
            return pd.DataFrame({"RSI": np.random.uniform(0, 100, periods)})

    def get_CCI(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标"""
        try:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            typical_price = (high_series + low_series + close_series) / 3
            ma = typical_price.rolling(window=n).mean()
            mad = typical_price.rolling(window=n).apply(
                lambda x: abs(x - x.mean()).mean()
            )
            cci = (typical_price - ma) / (0.015 * mad)

            return pd.DataFrame({"CCI": cci})
        except Exception as e:
            self._logger.error(f"Error calculating CCI: {e}")
            periods = len(close)
            return pd.DataFrame({"CCI": np.random.randn(periods) * 50})

    def log(self, content: str, level: str = "info") -> None:
        """日志记录"""
        if hasattr(self._logger, level):
            getattr(self._logger, level)(content)
        else:
            self._logger.info(content)

    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """代码涨跌停状态判断"""
        # 实盘交易模式需要从实时数据源获取
        return {
            security: {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": None,
                "limit_down_price": None,
                "current_price": 10.0,
            }
        }

    def handle_data(self, data: Dict[str, Any]) -> None:
        """实盘交易数据处理"""
        # 更新当前价格数据
        for security, price_data in data.items():
            if security in self.context.portfolio.positions:
                position = self.context.portfolio.positions[security]
                position.last_sale_price = price_data.get(
                    "price", position.last_sale_price
                )

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()
