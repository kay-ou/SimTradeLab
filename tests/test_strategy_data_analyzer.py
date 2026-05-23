"""策略数据依赖分析器测试"""

import tempfile
import os
import ast

from simtradelab.ptrade.strategy_data_analyzer import (
    StrategyDataAnalyzer,
    analyze_strategy_data_requirements,
    DataDependencies,
)


def _analyze_code(code: str) -> DataDependencies:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        return analyze_strategy_data_requirements(path)
    finally:
        os.unlink(path)


class TestGetFundamentalsTableDetection:
    """get_fundamentals 表名参数检测"""

    # ── 位置参数 ──

    def test_positional_table_valuation(self):
        deps = _analyze_code("df = get_fundamentals(stock, 'valuation')")
        assert deps.needs_fundamentals is True
        assert deps.needs_valuation is True
        assert deps.fundamental_tables == {"valuation"}

    def test_positional_table_balance(self):
        deps = _analyze_code("df = get_fundamentals(stock, 'balance')")
        assert deps.needs_fundamentals is True
        assert deps.needs_valuation is False
        assert deps.fundamental_tables == {"balance"}

    def test_positional_table_cashflow(self):
        deps = _analyze_code("df = get_fundamentals(stock, 'cash_flow')")
        assert deps.needs_fundamentals is True
        assert deps.fundamental_tables == {"cash_flow"}

    # ── 关键字参数 ──

    def test_keyword_table_valuation(self):
        deps = _analyze_code("df = get_fundamentals(context.test_stock, table='valuation')")
        assert deps.needs_fundamentals is True
        assert deps.needs_valuation is True
        assert deps.fundamental_tables == {"valuation"}

    def test_keyword_table_balance(self):
        deps = _analyze_code("df = get_fundamentals(stock, table='balance', date='2025-01-01')")
        assert deps.needs_fundamentals is True
        assert deps.needs_valuation is False
        assert deps.fundamental_tables == {"balance"}

    def test_keyword_table_income(self):
        deps = _analyze_code("df = get_fundamentals(stock, fields='net_profit', table='income')")
        assert deps.needs_fundamentals is True
        assert deps.fundamental_tables == {"income"}

    # ── 单参数（无 table） ──

    def test_single_arg_no_table(self):
        deps = _analyze_code("df = get_fundamentals(stock)")
        assert deps.needs_fundamentals is True
        assert deps.fundamental_tables == set()

    # ── 多次调用 ──

    def test_multiple_calls_different_tables(self):
        deps = _analyze_code("""
df1 = get_fundamentals(stock, 'valuation')
df2 = get_fundamentals(stock, table='balance')
""")
        assert deps.needs_fundamentals is True
        assert deps.needs_valuation is True
        assert deps.fundamental_tables == {"valuation", "balance"}

    def test_multiple_calls_same_table(self):
        deps = _analyze_code("""
df1 = get_fundamentals(s1, 'valuation')
df2 = get_fundamentals(s2, table='valuation')
""")
        assert deps.fundamental_tables == {"valuation"}


class TestPriceDataDetection:
    """价格数据依赖检测"""

    def test_get_history_triggers_price(self):
        deps = _analyze_code("hist = get_history(20, '1d', 'close', stocks)")
        assert deps.needs_price_data is True
        assert deps.needs_exrights is True

    def test_get_price_triggers_price(self):
        deps = _analyze_code("p = get_price('000001.SZ')")
        assert deps.needs_price_data is True

    def test_order_triggers_price(self):
        deps = _analyze_code("order('000001.SZ', 100)")
        assert deps.needs_price_data is True

    def test_no_price_api(self):
        deps = _analyze_code("log.info('hello')")
        assert deps.needs_price_data is False
        assert deps.needs_exrights is False


class TestErrorHandling:
    """容错处理"""

    def test_invalid_syntax(self):
        deps = _analyze_code("def broken(")
        assert deps.needs_price_data is True
        assert deps.needs_valuation is True
        assert deps.needs_fundamentals is True
        assert deps.needs_exrights is True

    def test_empty_file(self):
        deps = _analyze_code("")
        assert deps.needs_price_data is False


class TestVariableTableName:
    """变量作为表名 — 静态分析无法解析，不崩溃即可"""

    def test_variable_table_keyword(self):
        table_name = "valuation"
        code = f"df = get_fundamentals(stock, table=table_name)"
        deps = _analyze_code(code)
        assert deps.needs_fundamentals is True
        # 变量名无法静态解析，needs_valuation 不应被触发
        assert deps.needs_valuation is False

    def test_variable_table_positional(self):
        code = "df = get_fundamentals(stock, table_var)"
        deps = _analyze_code(code)
        assert deps.needs_fundamentals is True
        assert deps.needs_valuation is False


class TestStrategyDataAnalyzerDirect:
    """直接测试 StrategyDataAnalyzer AST 遍历"""

    def test_visit_call_keyword_table(self):
        tree = ast.parse("get_fundamentals(stock, table='valuation')")
        analyzer = StrategyDataAnalyzer()
        analyzer.visit(tree)
        deps = analyzer.analyze()
        assert deps.needs_valuation is True
        assert deps.fundamental_tables == {"valuation"}

    def test_visit_call_no_table_arg(self):
        tree = ast.parse("get_fundamentals(stock)")
        analyzer = StrategyDataAnalyzer()
        analyzer.visit(tree)
        deps = analyzer.analyze()
        assert deps.needs_fundamentals is True
        assert deps.fundamental_tables == set()
