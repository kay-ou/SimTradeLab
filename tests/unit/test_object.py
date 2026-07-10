# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
测试核心对象: Portfolio, Position
"""

import pytest
from datetime import datetime

from simtradelab.ptrade.object import Portfolio, Position


class TestPortfolio:
    """测试Portfolio类"""

    def test_init_portfolio(self):
        """测试Portfolio初始化"""
        portfolio = Portfolio(initial_capital=1000000.0)

        assert portfolio._cash == 1000000.0
        assert portfolio.starting_cash == 1000000.0
        assert portfolio.positions == {}
        assert portfolio.positions_value == 0.0

    def test_add_position(self):
        """测试建仓"""
        portfolio = Portfolio(initial_capital=1000000.0)

        # 建仓
        portfolio.add_position(
            stock='600000.SH',
            amount=1000,
            price=10.0,
            date=datetime(2024, 1, 1)
        )

        assert '600000.SH' in portfolio.positions
        position = portfolio.positions['600000.SH']
        assert position.amount == 1000
        assert position.cost_basis == 10.0

    def test_add_position_multiple(self):
        """测试加仓"""
        portfolio = Portfolio(initial_capital=1000000.0)

        # 第一次建仓
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))

        # 加仓
        portfolio.add_position('600000.SH', 500, 11.0, datetime(2024, 1, 2))

        position = portfolio.positions['600000.SH']
        assert position.amount == 1500
        # 成本=(1000*10 + 500*11)/1500 = 10.333...
        assert abs(position.cost_basis - 10.333333) < 0.001

    def test_add_position_preserves_enable_amount_for_t_plus_1(self):
        """T+1 加仓时，当日买入数量不可立即卖出。"""
        from types import SimpleNamespace

        context = SimpleNamespace(t_plus_1=True)
        portfolio = Portfolio(initial_capital=1000000.0, context_obj=context)
        portfolio.add_position('600000.SH', 100, 10.0, datetime(2024, 1, 1))
        portfolio.positions['600000.SH'].enable_amount = 100

        portfolio.add_position('600000.SH', 100, 11.0, datetime(2024, 1, 2))

        position = portfolio.positions['600000.SH']
        assert position.amount == 200
        assert position.enable_amount == 100

    def test_remove_position_partial(self):
        """测试减仓"""
        portfolio = Portfolio(initial_capital=1000000.0)

        # 建仓
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))

        # 减仓
        portfolio.remove_position('600000.SH', 500, datetime(2024, 1, 2))

        assert '600000.SH' in portfolio.positions
        position = portfolio.positions['600000.SH']
        assert position.amount == 500

    def test_remove_position_full(self):
        """测试清仓"""
        portfolio = Portfolio(initial_capital=1000000.0)

        # 建仓
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))

        # 清仓
        portfolio.remove_position('600000.SH', 1000, datetime(2024, 1, 2))

        assert '600000.SH' not in portfolio.positions

    def test_remove_position_exceed_amount(self):
        """测试卖出超过持仓应该报错"""
        portfolio = Portfolio(initial_capital=1000000.0)

        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))

        # 卖出超过持仓
        with pytest.raises(ValueError, match="卖出数量.*超过持仓"):
            portfolio.remove_position('600000.SH', 1500, datetime(2024, 1, 2))


class TestPosition:
    """测试Position类"""

    def test_init_position(self):
        """测试Position初始化"""
        position = Position(
            stock='600000.SH',
            amount=1000,
            cost_basis=10.0
        )

        assert position.stock == '600000.SH'
        assert position.amount == 1000
        assert position.cost_basis == 10.0


class TestPortfolioDividendTax:
    """测试Portfolio分红税计算"""

    def test_add_dividend(self, portfolio):
        """测试记录分红"""
        from datetime import datetime
        
        # 建立持仓
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))
        
        # 记录分红 (每股0.5元)
        portfolio.add_dividend('600000.SH', 0.5)
        
        # 验证分红记录
        assert '600000.SH' in portfolio._position_lots
        lot = portfolio._position_lots['600000.SH'][0]
        assert len(lot['dividends']) == 1
        assert lot['dividends'][0] == 500.0  # 1000股 * 0.5元
        assert lot['dividends_total'] == 500.0

    def test_multiple_dividends(self, portfolio):
        """测试多次分红"""
        from datetime import datetime
        
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))
        
        # 多次分红
        portfolio.add_dividend('600000.SH', 0.3)
        portfolio.add_dividend('600000.SH', 0.2)
        
        lot = portfolio._position_lots['600000.SH'][0]
        assert len(lot['dividends']) == 2
        assert lot['dividends_total'] == 500.0  # (0.3 + 0.2) * 1000

    def test_dividend_tax_short_term(self, portfolio):
        """测试短期持股分红税（≤30天）"""
        from datetime import datetime, timedelta
        
        buy_date = datetime(2024, 1, 1)
        sell_date = datetime(2024, 1, 15)  # 持有14天
        
        portfolio.add_position('600000.SH', 1000, 10.0, buy_date)
        portfolio.add_dividend('600000.SH', 0.5)  # 分红500元
        
        # 卖出时计算税
        tax_adj = portfolio.remove_position('600000.SH', 1000, sell_date)
        
        # 短期持股税率20%，调整值为 500 * (0.20 - 0.20) = 0
        assert tax_adj == 0.0

    def test_dividend_tax_medium_term(self, portfolio):
        """测试中期持股分红税（31-365天）"""
        from datetime import datetime, timedelta

        buy_date = datetime(2024, 1, 1)
        sell_date = datetime(2024, 3, 1)  # 持有60天

        portfolio.add_position('600000.SH', 1000, 10.0, buy_date)
        portfolio.add_dividend('600000.SH', 0.5)

        tax_adj = portfolio.remove_position('600000.SH', 1000, sell_date)

        # Ptrade行为：分红时预扣20%，卖出时不做税务调整
        assert tax_adj == 0.0

    def test_dividend_tax_long_term(self, portfolio):
        """测试长期持股分红税（>365天）"""
        from datetime import datetime, timedelta

        buy_date = datetime(2024, 1, 1)
        sell_date = datetime(2025, 2, 1)  # 持有397天

        portfolio.add_position('600000.SH', 1000, 10.0, buy_date)
        portfolio.add_dividend('600000.SH', 0.5)

        tax_adj = portfolio.remove_position('600000.SH', 1000, sell_date)

        # Ptrade行为：分红时预扣20%，卖出时不做税务调整
        assert tax_adj == 0.0

    def test_fifo_tax_calculation(self, portfolio):
        """测试FIFO批次分红税计算"""
        from datetime import datetime, timedelta
        
        # 第一批：1000股，持有短期
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))
        portfolio.add_dividend('600000.SH', 0.3)  # 分红300元
        
        # 第二批：500股，持有长期
        portfolio.add_position('600000.SH', 500, 11.0, datetime(2023, 1, 1))
        portfolio.add_dividend('600000.SH', 0.2)  # 分红(1000+500)*0.2
        
        # FIFO卖出800股（先卖第一批1000股中的800股，然后卖第二批）
        sell_date = datetime(2024, 2, 1)  # 第一批持有31天（中期）
        
        # 实际会扣除第一批的800股
        tax_adj = portfolio.remove_position('600000.SH', 800, sell_date)
        
        # 验证计算有结果（具体值取决于分红总和）
        assert isinstance(tax_adj, float)


class TestPortfolioProperties:
    """测试Portfolio属性和方法"""

    def test_cash_property(self, portfolio):
        """测试cash属性"""
        assert portfolio.cash == 1000000.0
        
        # 修改内部现金
        portfolio._cash = 500000.0
        assert portfolio.cash == 500000.0

    def test_starting_cash(self, portfolio):
        """测试starting_cash记录初始资金"""
        assert portfolio.starting_cash == 1000000.0
        
        # starting_cash不应该随着交易变化
        portfolio._cash = 500000.0
        assert portfolio.starting_cash == 1000000.0

    def test_positions_value(self, portfolio):
        """测试positions_value"""
        from datetime import datetime
        
        # 初始为0
        assert portfolio.positions_value == 0.0
        
        # 可以手动设置（由外部更新）
        portfolio.positions_value = 50000.0
        assert portfolio.positions_value == 50000.0

    def test_cache_invalidation(self, portfolio):
        """测试缓存失效机制"""
        from datetime import datetime

        # 设置缓存
        portfolio._cached_portfolio_value = 1000000.0
        portfolio._cache_date = datetime(2024, 1, 1)

        # 建仓应该清空 portfolio_value 缓存
        portfolio.add_position('600000.SH', 100, 10.0, datetime(2024, 1, 2))
        assert portfolio._cached_portfolio_value is None

        # 重新设置缓存
        portfolio._cached_portfolio_value = 1100000.0

        # 减仓应该清空 portfolio_value 缓存
        portfolio.remove_position('600000.SH', 50, datetime(2024, 1, 3))
        assert portfolio._cached_portfolio_value is None


class TestPortfolioMultipleLots:
    """测试Portfolio多批次持仓"""

    def test_single_lot(self, portfolio):
        """测试单批次持仓"""
        from datetime import datetime
        
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))
        
        assert '600000.SH' in portfolio._position_lots
        lots = portfolio._position_lots['600000.SH']
        assert len(lots) == 1
        assert lots[0]['amount'] == 1000
        assert lots[0]['date'] == datetime(2024, 1, 1)

    def test_multiple_lots(self, portfolio):
        """测试多批次持仓"""
        from datetime import datetime
        
        # 第一批
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))
        # 第二批
        portfolio.add_position('600000.SH', 500, 11.0, datetime(2024, 1, 10))
        # 第三批
        portfolio.add_position('600000.SH', 200, 12.0, datetime(2024, 1, 20))
        
        lots = portfolio._position_lots['600000.SH']
        assert len(lots) == 3
        assert lots[0]['amount'] == 1000
        assert lots[1]['amount'] == 500
        assert lots[2]['amount'] == 200
        
        # 持仓总量应该正确
        assert portfolio.positions['600000.SH'].amount == 1700

    def test_lots_cleanup_on_full_sell(self, portfolio):
        """测试清仓时批次清理"""
        from datetime import datetime
        
        portfolio.add_position('600000.SH', 1000, 10.0, datetime(2024, 1, 1))
        
        # 完全卖出
        portfolio.remove_position('600000.SH', 1000, datetime(2024, 2, 1))
        
        # 批次记录应该被清理
        assert '600000.SH' not in portfolio._position_lots
        assert '600000.SH' not in portfolio.positions
