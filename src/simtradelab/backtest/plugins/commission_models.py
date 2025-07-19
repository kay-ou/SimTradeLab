# -*- coding: utf-8 -*-
"""
手续费模型插件实现

提供多种手续费模型，模拟不同的交易费用结构：
- 中国A股手续费模型：符合A股市场规则
- 固定手续费模型：简单的固定费率
- 阶梯手续费模型：基于交易量的阶梯费率
- 综合手续费模型：包含多种费用类型
"""

from decimal import Decimal
from typing import Dict, List

from simtradelab.backtest.plugins.base import BaseCommissionModel, Fill, PluginMetadata
from simtradelab.backtest.plugins.config import (
    CommissionModelConfig,
    FixedCommissionModelConfig,
    TieredCommissionModelConfig,
)


class ChinaAStockCommissionModel(BaseCommissionModel):
    """
    中国A股手续费模型

    严格按照A股市场规则计算手续费：
    - 印花税（仅卖出）：0.1%
    - 佣金（买卖双向）：万分之三（最低5元）
    - 过户费（仅沪市）：万分之0.2
    - 经手费：万分之0.487
    - 监管费：万分之0.2
    """

    config_model = CommissionModelConfig

    METADATA = PluginMetadata(
        name="china_a_stock_commission_model",
        version="1.0.0",
        description="中国A股市场手续费模型",
        author="SimTradeLab",
        category="commission_model",
        tags=["backtest", "commission", "china", "astock"],
    )

    # 预定义常量 - 高性能优化
    _DEFAULT_STAMP_TAX_RATE = Decimal("0.001")  # 印花税0.1%
    _DEFAULT_COMMISSION_RATE = Decimal("0.0003")  # 佣金万三
    _DEFAULT_MIN_COMMISSION = Decimal("5.0")  # 最低佣金5元
    _DEFAULT_TRANSFER_FEE_RATE = Decimal("0.00002")  # 过户费万0.2
    _DEFAULT_EXCHANGE_FEE_RATE = Decimal("0.0000487")  # 经手费万0.487
    _DEFAULT_REGULATORY_FEE_RATE = Decimal("0.00002")  # 监管费万0.2

    def __init__(self, metadata: PluginMetadata, config: CommissionModelConfig):
        super().__init__(metadata, config)

        # 直接使用Pydantic配置对象，不再支持向后兼容
        self._stamp_tax_rate = config.stamp_duty_rate
        self._commission_rate = config.commission_rate
        self._min_commission = config.min_commission
        self._transfer_fee_rate = config.transfer_fee_rate
        self._exchange_fee_rate = self._DEFAULT_EXCHANGE_FEE_RATE
        self._regulatory_fee_rate = self._DEFAULT_REGULATORY_FEE_RATE

        # 市场配置
        self._sh_markets = ["SH", "SSE"]
        self._sz_markets = ["SZ", "SZSE"]

    def _on_initialize(self) -> None:
        """初始化中国A股手续费模型"""
        self.logger.info("ChinaAStockCommissionModel initialized")

    def _on_start(self) -> None:
        """启动中国A股手续费模型"""
        self.logger.info("ChinaAStockCommissionModel started")

    def _on_stop(self) -> None:
        """停止中国A股手续费模型"""
        self.logger.info("ChinaAStockCommissionModel stopped")

    def calculate_commission(self, fill: Fill) -> Decimal:
        """
        计算A股手续费总额

        Args:
            fill: 成交信息

        Returns:
            手续费总额
        """
        breakdown = self.calculate_commission_breakdown(fill)
        return Decimal(str(sum(breakdown.values())))

    def calculate_commission_breakdown(self, fill: Fill) -> Dict[str, Decimal]:
        """
        计算A股手续费明细

        Args:
            fill: 成交信息

        Returns:
            手续费明细字典
        """
        trade_value = fill.price * fill.quantity
        breakdown = {}

        # 1. 印花税（仅卖出）
        stamp_tax = Decimal("0")
        if fill.side == "sell":
            stamp_tax = trade_value * self._stamp_tax_rate
        breakdown["stamp_tax"] = stamp_tax

        # 2. 佣金（买卖双向，有最低限制）
        commission = trade_value * self._commission_rate
        commission = max(commission, self._min_commission)
        breakdown["commission"] = commission

        # 3. 过户费（仅沪市）
        transfer_fee = Decimal("0")
        if self._is_sh_market(fill.symbol):
            transfer_fee = trade_value * self._transfer_fee_rate
        breakdown["transfer_fee"] = transfer_fee

        # 4. 经手费
        breakdown["exchange_fee"] = trade_value * self._exchange_fee_rate

        # 5. 监管费
        breakdown["regulatory_fee"] = trade_value * self._regulatory_fee_rate

        # 计算总额
        total = Decimal(str(sum(breakdown.values())))
        breakdown["total"] = total

        self.logger.debug(
            f"A股手续费明细 - 订单{fill.order_id}: "
            f"印花税={breakdown['stamp_tax']:.2f}, "
            f"佣金={breakdown['commission']:.2f}, "
            f"过户费={breakdown['transfer_fee']:.2f}, "
            f"经手费={breakdown['exchange_fee']:.2f}, "
            f"监管费={breakdown['regulatory_fee']:.2f}, "
            f"总计={breakdown['total']:.2f}"
        )

        return breakdown

    def _is_sh_market(self, symbol: str) -> bool:
        """判断是否为沪市股票"""
        for market in self._sh_markets:
            if market.upper() in symbol.upper():
                return True
        return False


class FixedCommissionModel(BaseCommissionModel):
    """
    固定手续费模型

    使用固定费率计算手续费：
    - 买入手续费率
    - 卖出手续费率
    - 最低手续费限制
    """

    config_model = FixedCommissionModelConfig

    METADATA = PluginMetadata(
        name="fixed_commission_model",
        version="1.0.0",
        description="固定费率手续费模型",
        author="SimTradeLab",
        category="commission_model",
        tags=["backtest", "commission", "fixed", "simple"],
    )

    # 预定义常量 - 高性能优化
    _DEFAULT_BUY_COMMISSION_RATE = Decimal("0.0003")
    _DEFAULT_SELL_COMMISSION_RATE = Decimal("0.0003")
    _DEFAULT_MIN_COMMISSION = Decimal("1.0")
    _DEFAULT_MAX_COMMISSION = Decimal("1000.0")

    def __init__(self, metadata: PluginMetadata, config: FixedCommissionModelConfig):
        super().__init__(metadata, config)
        self._config = config or FixedCommissionModelConfig()
        # 直接使用Pydantic配置对象，统一的费率配置
        self._buy_commission_rate = self._config.commission_rate  # 使用统一的commission_rate
        self._sell_commission_rate = (
            self._config.commission_rate
        )  # 使用统一的commission_rate
        self._commission_rate = self._config.commission_rate
        self._min_commission = self._config.min_commission
        self._max_commission = self._DEFAULT_MAX_COMMISSION

    def _on_initialize(self) -> None:
        """初始化固定手续费模型"""
        self.logger.info("FixedCommissionModel initialized")

    def _on_start(self) -> None:
        """启动固定手续费模型"""
        self.logger.info("FixedCommissionModel started")

    def _on_stop(self) -> None:
        """停止固定手续费模型"""
        self.logger.info("FixedCommissionModel stopped")

    def calculate_commission(self, fill: Fill) -> Decimal:
        """
        计算固定手续费

        Args:
            fill: 成交信息

        Returns:
            手续费总额
        """
        trade_value = fill.price * fill.quantity

        # 选择费率
        commission_rate = (
            self._buy_commission_rate
            if fill.side == "buy"
            else self._sell_commission_rate
        )

        # 计算手续费
        commission = trade_value * commission_rate

        # 应用最小和最大限制
        commission = max(commission, self._min_commission)
        commission = min(commission, self._max_commission)

        self.logger.debug(
            f"Fixed commission for order {fill.order_id}: {commission} "
            f"(rate: {commission_rate:.4f})"
        )

        return commission


class TieredCommissionModel(BaseCommissionModel):
    """
    阶梯手续费模型

    基于交易量的阶梯费率：
    - 交易量越大，费率越低
    - 支持多个阶梯区间
    - 可配置累积和单笔两种模式
    """

    config_model = TieredCommissionModelConfig

    METADATA = PluginMetadata(
        name="tiered_commission_model",
        version="1.0.0",
        description="阶梯费率手续费模型",
        author="SimTradeLab",
        category="commission_model",
        tags=["backtest", "commission", "tiered", "volume"],
    )

    # 预定义常量 - 高性能优化
    _DEFAULT_MIN_COMMISSION = Decimal("1.0")
    _DEFAULT_MAX_VALUE = Decimal("999999999")  # 代替infinity

    def __init__(self, metadata: PluginMetadata, config: TieredCommissionModelConfig):
        super().__init__(metadata, config)

        # 直接使用Pydantic配置对象，不再支持向后兼容
        # 累积交易量跟踪
        self._cumulative_volume: Dict[str, Decimal] = {}
        self._cumulative_mode = False  # 简化处理
        self._min_commission = config.min_commission
        self._tier_thresholds = config.tier_thresholds
        self._tier_rates = config.tier_rates

        # 构建阶梯配置
        self._tiers = self._build_tiers_from_config()

    def _build_tiers_from_config(self) -> List[Dict[str, Decimal]]:
        """从Pydantic配置构建阶梯配置"""
        tiers = []
        sorted_thresholds = sorted(self._tier_thresholds.items(), key=lambda x: x[1])

        # 添加第一个阶梯：0到第一个阈值
        if sorted_thresholds:
            first_tier_rate = self._tier_rates.get("tier1", Decimal("0.0003"))
            tiers.append(
                {
                    "min_value": Decimal("0"),
                    "max_value": sorted_thresholds[0][1],
                    "rate": first_tier_rate,
                }
            )

        for i, (tier_name, threshold) in enumerate(sorted_thresholds):
            tier_rate_key = f"tier{i+2}"  # 从tier2开始，因为tier1已用于0-第一阈值
            if tier_rate_key not in self._tier_rates:
                tier_rate_key = tier_name

            rate = self._tier_rates.get(tier_rate_key, Decimal("0.0003"))

            # 设置最大值为下一个阈值或无穷大
            if i < len(sorted_thresholds) - 1:
                max_value = sorted_thresholds[i + 1][1]
            else:
                max_value = Decimal("999999999")  # 代替无穷大

            tiers.append(
                {
                    "min_value": threshold,
                    "max_value": max_value,
                    "rate": rate,
                }
            )

        return tiers

    def _on_initialize(self) -> None:
        """初始化阶梯手续费模型"""
        self.logger.info("TieredCommissionModel initialized")

    def _on_start(self) -> None:
        """启动阶梯手续费模型"""
        self.logger.info("TieredCommissionModel started")

    def _on_stop(self) -> None:
        """停止阶梯手续费模型"""
        self.logger.info("TieredCommissionModel stopped")

    def calculate_commission(self, fill: Fill) -> Decimal:
        """
        计算阶梯手续费

        Args:
            fill: 成交信息

        Returns:
            手续费总额
        """
        trade_value = fill.price * fill.quantity

        # 获取适用费率
        commission_rate = self._get_applicable_rate(fill.symbol, trade_value)

        # 计算手续费
        commission = trade_value * commission_rate
        commission = max(commission, self._min_commission)

        # 更新累积交易量（简化处理）
        if fill.symbol not in self._cumulative_volume:
            self._cumulative_volume[fill.symbol] = Decimal("0")
        self._cumulative_volume[fill.symbol] += trade_value

        self.logger.debug(
            f"Tiered commission for order {fill.order_id}: {commission} "
            f"(rate: {commission_rate:.4f}, value: {trade_value})"
        )

        return commission

    def _get_applicable_rate(self, symbol: str, trade_value: Decimal) -> Decimal:
        """
        获取适用费率

        Args:
            symbol: 证券代码
            trade_value: 交易金额

        Returns:
            适用费率
        """
        # 使用当前交易金额
        base_value = trade_value

        # 查找适用阶梯
        for tier in self._tiers:
            if tier["min_value"] <= base_value < tier["max_value"]:
                return tier["rate"]

        # 如果没有找到，返回最后一个阶梯的费率
        return self._tiers[-1]["rate"] if self._tiers else Decimal("0.0003")


class ComprehensiveCommissionModel(BaseCommissionModel):
    """
    综合手续费模型

    包含多种费用类型的综合模型：
    - 基础佣金
    - 印花税
    - 过户费
    - 清算费
    - 其他费用
    """

    config_model = CommissionModelConfig

    METADATA = PluginMetadata(
        name="comprehensive_commission_model",
        version="1.0.0",
        description="综合手续费模型",
        author="SimTradeLab",
        category="commission_model",
        tags=["backtest", "commission", "comprehensive", "multiple"],
    )

    # 预定义常量 - 高性能优化
    _DEFAULT_BASE_COMMISSION_RATE = Decimal("0.0003")
    _DEFAULT_STAMP_TAX_RATE = Decimal("0.001")
    _DEFAULT_TRANSFER_FEE_RATE = Decimal("0.00002")
    _DEFAULT_CLEARING_FEE_RATE = Decimal("0.00001")
    _DEFAULT_OTHER_FEE_RATE = Decimal("0.00001")
    _DEFAULT_MIN_COMMISSION = Decimal("1.0")

    def __init__(self, metadata: PluginMetadata, config: CommissionModelConfig):
        super().__init__(metadata, config)

        # 直接使用Pydantic配置对象，不再支持向后兼容
        self._base_commission_rate = config.commission_rate
        self._stamp_tax_rate = config.stamp_duty_rate
        self._transfer_fee_rate = config.transfer_fee_rate
        self._clearing_fee_rate = self._DEFAULT_CLEARING_FEE_RATE
        self._other_fee_rate = self._DEFAULT_OTHER_FEE_RATE
        self._min_commission = config.min_commission
        self._stamp_tax_on_sell_only = config.enable_stamp_duty
        self._transfer_fee_on_sh_only = config.enable_transfer_fee

    def _on_initialize(self) -> None:
        """初始化综合手续费模型"""
        self.logger.info("ComprehensiveCommissionModel initialized")

    def _on_start(self) -> None:
        """启动综合手续费模型"""
        self.logger.info("ComprehensiveCommissionModel started")

    def _on_stop(self) -> None:
        """停止综合手续费模型"""
        self.logger.info("ComprehensiveCommissionModel stopped")

    def calculate_commission(self, fill: Fill) -> Decimal:
        """
        计算综合手续费总额

        Args:
            fill: 成交信息

        Returns:
            手续费总额
        """
        breakdown = self.calculate_commission_breakdown(fill)
        return breakdown["total"]

    def calculate_commission_breakdown(self, fill: Fill) -> Dict[str, Decimal]:
        """
        计算综合手续费明细

        Args:
            fill: 成交信息

        Returns:
            手续费明细字典
        """
        trade_value = fill.price * fill.quantity
        breakdown = {}

        # 1. 基础佣金
        base_commission = trade_value * self._base_commission_rate
        base_commission = max(base_commission, self._min_commission)
        breakdown["base_commission"] = base_commission

        # 2. 印花税
        stamp_tax = Decimal("0")
        if self._stamp_tax_on_sell_only and fill.side == "sell":
            stamp_tax = trade_value * self._stamp_tax_rate
        elif not self._stamp_tax_on_sell_only:
            stamp_tax = trade_value * self._stamp_tax_rate
        breakdown["stamp_tax"] = stamp_tax

        # 3. 过户费
        transfer_fee = Decimal("0")
        if self._transfer_fee_on_sh_only and self._is_sh_market(fill.symbol):
            transfer_fee = trade_value * self._transfer_fee_rate
        elif not self._transfer_fee_on_sh_only:
            transfer_fee = trade_value * self._transfer_fee_rate
        breakdown["transfer_fee"] = transfer_fee

        # 4. 清算费
        breakdown["clearing_fee"] = trade_value * self._clearing_fee_rate

        # 5. 其他费用
        breakdown["other_fee"] = trade_value * self._other_fee_rate

        # 计算总额
        total = Decimal(str(sum(breakdown.values())))
        breakdown["total"] = total

        self.logger.debug(
            f"Comprehensive commission breakdown for order {fill.order_id}: "
            f"base={breakdown['base_commission']:.2f}, "
            f"stamp={breakdown['stamp_tax']:.2f}, "
            f"transfer={breakdown['transfer_fee']:.2f}, "
            f"clearing={breakdown['clearing_fee']:.2f}, "
            f"other={breakdown['other_fee']:.2f}, "
            f"total={breakdown['total']:.2f}"
        )

        return breakdown

    def _is_sh_market(self, symbol: str) -> bool:
        """判断是否为沪市股票"""
        return "SH" in symbol.upper() or "SSE" in symbol.upper()


class PerShareCommissionModel(BaseCommissionModel):
    """
    按股计费模型

    按成交股数计算手续费：
    - 每股固定费用
    - 最低手续费限制
    - 适用于美股等市场
    """

    config_model = CommissionModelConfig

    METADATA = PluginMetadata(
        name="per_share_commission_model",
        version="1.0.0",
        description="按股计费手续费模型",
        author="SimTradeLab",
        category="commission_model",
        tags=["backtest", "commission", "per_share", "us_stock"],
    )

    # 预定义常量 - 高性能优化
    _DEFAULT_PER_SHARE_FEE = Decimal("0.005")  # 每股0.5分
    _DEFAULT_MIN_COMMISSION = Decimal("1.0")
    _DEFAULT_MAX_COMMISSION = Decimal("100.0")

    def __init__(self, metadata: PluginMetadata, config: CommissionModelConfig):
        super().__init__(metadata, config)

        # 直接使用Pydantic配置对象，不再支持向后兼容
        self._per_share_fee = self._DEFAULT_PER_SHARE_FEE  # 使用默认值，配置类中暂无此字段
        self._min_commission = config.min_commission
        self._max_commission = self._DEFAULT_MAX_COMMISSION

    def _on_initialize(self) -> None:
        """初始化按股计费模型"""
        self.logger.info("PerShareCommissionModel initialized")

    def _on_start(self) -> None:
        """启动按股计费模型"""
        self.logger.info("PerShareCommissionModel started")

    def _on_stop(self) -> None:
        """停止按股计费模型"""
        self.logger.info("PerShareCommissionModel stopped")

    def calculate_commission(self, fill: Fill) -> Decimal:
        """
        计算按股手续费

        Args:
            fill: 成交信息

        Returns:
            手续费总额
        """
        # 按股数计算
        commission = fill.quantity * self._per_share_fee

        # 应用最小和最大限制
        commission = max(commission, self._min_commission)
        commission = min(commission, self._max_commission)

        self.logger.debug(
            f"Per-share commission for order {fill.order_id}: {commission} "
            f"(shares: {fill.quantity}, fee per share: {self._per_share_fee})"
        )

        return commission
