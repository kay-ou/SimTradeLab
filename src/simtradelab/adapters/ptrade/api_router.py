# -*- coding: utf-8 -*-
"""
PTrade API 路由器

根据运行模式（回测、实盘交易、研究）将API调用路由到不同的实现。
符合 SimTradeLab v4.0 架构的模式感知适配器设计。
"""
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ...core.event_bus import EventBus

if TYPE_CHECKING:
    from .adapter import Order, Position, PTradeContext


class BaseAPIRouter(ABC):
    """API路由器基类 - 定义完整的 PTrade API 接口"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        self.context = context
        self.event_bus = event_bus
        self._logger = logging.getLogger(self.__class__.__name__)

    # ==========================================
    # 交易相关 API (核心方法)
    # ==========================================

    @abstractmethod
    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """下单"""
        pass

    @abstractmethod
    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        pass

    @abstractmethod
    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓信息"""
        pass

    @abstractmethod
    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息"""
        pass

    @abstractmethod
    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单"""
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定订单"""
        pass

    @abstractmethod
    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取全部订单"""
        pass

    @abstractmethod
    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单"""
        pass

    # ==========================================
    # 数据获取 API (核心方法)
    # ==========================================

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
        pass

    # ==========================================
    # 设置函数 API
    # ==========================================

    @abstractmethod
    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        pass

    @abstractmethod
    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        pass

    # ==========================================
    # 计算函数 API
    # ==========================================

    @abstractmethod
    def get_MACD(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_RSI(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标"""
        pass

    @abstractmethod
    def get_CCI(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标"""
        pass

    # ==========================================
    # 工具函数 API
    # ==========================================

    @abstractmethod
    def log(self, content: str, level: str = "info") -> None:
        """日志记录"""
        pass

    @abstractmethod
    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """代码涨跌停状态判断"""
        pass

    # ==========================================
    # 模式相关的处理方法
    # ==========================================

    @abstractmethod
    def handle_data(self, data: Dict[str, Any]) -> None:
        """处理市场数据"""
        pass

    @abstractmethod
    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在当前模式下支持"""
        pass

    def validate_and_execute(
        self, api_name: str, method_func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """验证并执行API调用"""
        if not self.is_mode_supported(api_name):
            raise ValueError(f"API '{api_name}' is not supported in current mode")

        try:
            return method_func(*args, **kwargs)
        except Exception as e:
            self._logger.error(f"Error executing API '{api_name}': {e}")
            raise


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
            "cancel_order",
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
        current_price = limit_price or 10.0  # 默认价格
        
        # 计算股数
        amount = int(value / current_price)
        if amount <= 0:
            return None
            
        return self.order(security, amount, limit_price)

    def cancel_order(self, order_id: str) -> bool:
        """回测模式撤单"""
        if self.context.blotter:
            return self.context.blotter.cancel_order(order_id)
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

    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        self.context.universe = securities
        self._logger.info(f"Universe set to {len(securities)} securities")

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        self.context.benchmark = benchmark
        self._logger.info(f"Benchmark set to {benchmark}")

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
                from .adapter import Position
                
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


class LiveTradingAPIRouter(BaseAPIRouter):
    """实盘交易模式API路由器"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        super().__init__(context, event_bus)
        self._supported_apis = {
            "order",
            "order_value",
            "cancel_order",
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

    def cancel_order(self, order_id: str) -> bool:
        """实盘交易撤单"""
        if self.event_bus:
            self.event_bus.publish(
                "trading.cancel_order.request",
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

    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        self.context.universe = securities
        self._logger.info(f"Universe set to {len(securities)} securities")

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        self.context.benchmark = benchmark
        self._logger.info(f"Benchmark set to {benchmark}")

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


class ResearchAPIRouter(BaseAPIRouter):
    """研究模式API路由器"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        super().__init__(context, event_bus)
        self._supported_apis = {
            "get_history",
            "get_price",
            "get_snapshot",
            "set_universe",
            "set_benchmark",
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            "log",
            "check_limit",
            "handle_data",
        }

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在研究模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def cancel_order(self, order_id: str) -> bool:
        """研究模式不支持交易"""
        raise NotImplementedError(
            "Trading operations are not supported in research mode"
        )

    def get_position(self, security: str) -> Optional["Position"]:
        """研究模式不支持持仓查询"""
        raise NotImplementedError("Position queries are not supported in research mode")

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """研究模式不支持持仓查询"""
        raise NotImplementedError("Position queries are not supported in research mode")

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def get_order(self, order_id: str) -> Optional["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """研究模式不支持订单查询"""
        raise NotImplementedError("Order queries are not supported in research mode")

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """研究模式不支持交易查询"""
        raise NotImplementedError("Trade queries are not supported in research mode")

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
        # 研究模式专注于数据分析
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

    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        self.context.universe = securities
        self._logger.info(f"Research universe set to {len(securities)} securities")

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        self.context.benchmark = benchmark
        self._logger.info(f"Research benchmark set to {benchmark}")

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
        """研究模式数据处理"""
        # 研究模式主要用于数据分析，不涉及交易
        pass
