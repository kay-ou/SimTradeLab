# -*- coding: utf-8 -*-
"""
PTrade回测模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ....core.event_bus import EventBus
from .base import BaseAPIRouter

if TYPE_CHECKING:
    from ..models import Order, Position
    from ..context import PTradeContext


class BacktestAPIRouter(BaseAPIRouter):
    """回测模式API路由器"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        slippage_rate: float = 0.0,
        commission_rate: float = 0.0,
    ):
        super().__init__(context, event_bus)
        self._slippage_rate = slippage_rate
        self._commission_rate = commission_rate
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
            "set_commission",
            "set_slippage",
            "set_parameters",
            "set_fixed_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
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
        """检查API是否在回测模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """回测模式下单逻辑"""
        if not self.context.blotter:
            return None
        
        # 检查资金是否充足（仅对买入订单）
        if amount > 0:  # 买入订单
            price = limit_price or 10.0
            execution_price = price * (1 + self._slippage_rate)
            commission = abs(amount * execution_price * self._commission_rate)
            required_cash = amount * execution_price + commission
            
            if self.context.portfolio.cash < required_cash:
                self._logger.warning(f"Order rejected: insufficient cash for {security}")
                return None
            
        order_id = self.context.blotter.create_order(security, amount, limit_price)
        self._simulate_order_execution(order_id)
        return order_id

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        # 获取当前价格
        current_price = limit_price or self._get_current_price(security)
        
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
        current_price = limit_price or self._get_current_price(security)
        
        # 计算目标股数
        target_amount = int(target_value / current_price)
        
        return self.order_target(security, target_amount, limit_price)

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托"""
        # 在回测模式下，市价单使用当前价格
        current_price = self._get_current_price(security)
        return self.order(security, amount, current_price)

    def cancel_order(self, order_id: str) -> bool:
        """回测模式撤单"""
        if self.context.blotter:
            return self.context.blotter.cancel_order(order_id)
        return False

    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展"""
        # 在回测模式下，扩展撤单与cancel_order功能相同
        return self.cancel_order(order_id)

    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        # 在回测模式下，返回所有订单
        return self.get_orders()

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        # 回测模式下不支持新股申购，返回空列表
        self._logger.warning("IPO orders are not supported in backtest mode")
        return []

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        # 回测模式下不支持盘后交易，返回None
        self._logger.warning("After trading orders are not supported in backtest mode")
        return None

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        # 回测模式下不支持盘后交易，返回False
        self._logger.warning("After trading cancel orders are not supported in backtest mode")
        return False

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
        # 这里需要与数据插件集成
        # 暂时返回模拟数据
        securities = security_list or self.context.universe or ["000001.XSHE"]

        if isinstance(field, str):
            field = [field]

        # 如果请求字典格式
        if is_dict:
            result = {}
            for security in securities:
                result[security] = {}
                for f in field:
                    # 生成模拟数据
                    if f in ["open", "high", "low", "close", "price"]:
                        base_price = 15.0 if security.startswith("000") else 20.0
                        prices = [base_price + i * 0.1 for i in range(count)]
                        result[security][f] = prices
                    elif f == "volume":
                        result[security][f] = [100000 + i * 1000 for i in range(count)]
                    elif f == "money":
                        result[security][f] = [1000000 + i * 10000 for i in range(count)]
                    else:
                        result[security][f] = [0.0] * count
            return result
        else:
            # 返回DataFrame格式
            data = []
            for security in securities:
                for i in range(count):
                    row: Dict[str, Any] = {"security": security}
                    date = pd.Timestamp.now() - pd.Timedelta(days=count-i-1)
                    row["date"] = date
                    
                    base_price = 15.0 if security.startswith("000") else 20.0
                    price = base_price + i * 0.1
                    
                    for f in field:
                        if f in ["open", "high", "low", "close", "price"]:
                            row[f] = price
                        elif f == "volume":
                            row[f] = 100000 + i * 1000
                        elif f == "money":
                            row[f] = 1000000 + i * 10000
                        else:
                            row[f] = 0.0
                    
                    data.append(row)
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index(["security", "date"], inplace=True)
            return df

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
        # 暂时返回模拟数据
        return pd.DataFrame()

    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
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
        # 暂时返回模拟数据
        return date

    def get_all_trades_days(self) -> List[str]:
        """获取全部交易日期"""
        # 暂时返回模拟数据
        return []

    def get_trade_days(self, start_date: str, end_date: str) -> List[str]:
        """获取指定范围交易日期"""
        # 暂时返回模拟数据
        return []

    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息"""
        # 暂时返回模拟数据
        return {}

    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息"""
        # 暂时返回模拟数据
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
        self._commission_rate = commission
        self._logger.info(f"Commission rate set to {commission}")

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        self._slippage_rate = slippage
        self._logger.info(f"Slippage rate set to {slippage}")

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        self._slippage_rate = slippage
        self._logger.info(f"Fixed slippage rate set to {slippage}")

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        # 暂时存储在上下文中
        if not hasattr(self.context, '_volume_ratio'):
            self.context._volume_ratio = ratio
        self._logger.info(f"Volume ratio set to {ratio}")

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        # 暂时存储在上下文中
        if not hasattr(self.context, '_limit_mode'):
            self.context._limit_mode = mode
        self._logger.info(f"Limit mode set to {mode}")

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        # 暂时存储在上下文中
        if not hasattr(self.context, '_yesterday_position'):
            self.context._yesterday_position = positions
        self._logger.info(f"Yesterday position set with {len(positions)} positions")

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        # 暂时存储在上下文中
        if not hasattr(self.context, '_parameters'):
            self.context._parameters = params
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
        # 模拟涨跌停检查
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
        """回测模式数据处理"""
        # 更新当前价格数据
        for security, price_data in data.items():
            if security in self.context.portfolio.positions:
                position = self.context.portfolio.positions[security]
                position.last_sale_price = price_data.get(
                    "price", position.last_sale_price
                )

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()

    def _simulate_order_execution(self, order_id: str) -> None:
        """模拟订单执行"""
        if not self.context.blotter:
            return

        order = self.context.blotter.get_order(order_id)
        if not order:
            return

        security = order.symbol
        amount = order.amount
        price = order.limit or 10.0

        # 计算实际成交价格（包含滑点）
        execution_price = price * (
            1 + self._slippage_rate if amount > 0 else 1 - self._slippage_rate
        )

        # 计算手续费
        commission = abs(amount * execution_price * self._commission_rate)

        # 检查资金是否充足（仅对买入订单）
        portfolio = self.context.portfolio
        if amount > 0:  # 买入订单
            required_cash = amount * execution_price + commission
            if portfolio.cash < required_cash:
                # 资金不足，订单失败
                order.status = "rejected"
                self._logger.warning(f"Order {order_id} rejected: insufficient cash")
                return

        # 更新持仓
        if security in portfolio.positions:
            position = portfolio.positions[security]
            total_cost = (
                position.amount * position.cost_basis + amount * execution_price
            )
            total_amount = position.amount + amount
            if total_amount == 0:
                del portfolio.positions[security]
            else:
                position.amount = total_amount
                position.cost_basis = total_cost / total_amount
                position.last_sale_price = execution_price
        else:
            if amount != 0:
                # 动态导入Position类以避免循环导入
                from ..models import Position
                
                portfolio.positions[security] = Position(
                    sid=security,
                    enable_amount=amount,
                    amount=amount,
                    cost_basis=execution_price,
                    last_sale_price=execution_price,
                )

        # 更新现金
        portfolio.cash -= amount * execution_price + commission

        # 更新投资组合价值
        portfolio.update_portfolio_value()

        # 更新订单状态
        order.status = "filled"
        order.filled = amount

        self._logger.info(
            f"Order executed: {order_id}, {security}, {amount} @ {execution_price}"
        )

    def _get_current_price(self, security: str) -> float:
        """获取股票当前价格"""
        # 从上下文获取价格数据
        if hasattr(self.context, 'current_data') and security in self.context.current_data:
            return self.context.current_data[security].get('price', 10.0)
        
        # 使用默认价格
        base_price = 15.0 if security.startswith("000") else 20.0
        return base_price