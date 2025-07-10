# -*- coding: utf-8 -*-
"""
SimTradeLab异常系统测试

专注测试异常系统的核心业务价值：
1. 在量化交易中提供有意义的错误信息
2. 支持系统错误恢复和故障诊断
3. 确保交易系统的稳定性和可靠性
"""

import pytest

from simtradelab.exceptions import (
    ConfigurationError,
    DataLoadError,
    DataSourceError,
    DataValidationError,
    EngineError,
    InsufficientFundsError,
    InsufficientPositionError,
    InvalidOrderError,
    ReportGenerationError,
    SimTradeLabError,
    StrategyError,
    TradingError,
)


class TestTradingSystemExceptionHandling:
    """测试交易系统异常处理的核心业务场景"""

    def test_insufficient_funds_trading_scenario(self):
        """测试资金不足场景 - 风险控制的关键功能"""
        # 模拟交易场景：账户余额10000，尝试买入价值15000的股票
        available_cash = 10000
        order_value = 15000
        symbol = "000001.XSHE"

        def place_large_order():
            if order_value > available_cash:
                raise InsufficientFundsError(
                    f"Cannot place order for {symbol}: "
                    f"Required ${order_value:,} exceeds available cash ${available_cash:,}"
                )

        # 验证业务价值：系统正确阻止了超出资金限制的交易
        with pytest.raises(InsufficientFundsError) as exc_info:
            place_large_order()

        error_message = str(exc_info.value)
        assert symbol in error_message
        assert "$15,000" in error_message
        assert "$10,000" in error_message
        assert "exceeds available cash" in error_message

        # 验证异常继承关系支持统一处理
        assert isinstance(exc_info.value, TradingError)
        assert isinstance(exc_info.value, SimTradeLabError)

    def test_position_management_exception_scenario(self):
        """测试持仓管理异常场景 - 卖空风控的核心需求"""
        # 模拟持仓场景：持有500股，尝试卖出800股
        current_position = 500
        sell_quantity = 800
        symbol = "000002.XSHE"

        def place_sell_order():
            if sell_quantity > current_position:
                raise InsufficientPositionError(
                    f"Cannot sell {sell_quantity} shares of {symbol}: "
                    f"Only {current_position} shares available"
                )

        # 验证业务价值：系统防止了卖空超出持仓的操作
        with pytest.raises(InsufficientPositionError) as exc_info:
            place_sell_order()

        error_message = str(exc_info.value)
        assert "800 shares" in error_message
        assert symbol in error_message
        assert "500 shares available" in error_message

    def test_invalid_order_parameters_scenario(self):
        """测试无效订单参数场景 - 订单验证的关键功能"""
        # 模拟无效订单场景：负价格、零数量
        invalid_price = -10.5
        invalid_quantity = 0
        symbol = "000003.XSHE"

        def validate_order_parameters():
            if invalid_price <= 0:
                raise InvalidOrderError(
                    f"Invalid price for {symbol}: {invalid_price}. Price must be positive"
                )
            if invalid_quantity <= 0:
                raise InvalidOrderError(
                    f"Invalid quantity for {symbol}: {invalid_quantity}. Quantity must be positive"
                )

        # 验证业务价值：系统阻止了无效的订单参数
        with pytest.raises(InvalidOrderError) as exc_info:
            validate_order_parameters()

        error_message = str(exc_info.value)
        assert symbol in error_message
        assert "must be positive" in error_message

    def test_strategy_execution_failure_scenario(self):
        """测试策略执行失败场景 - 策略可靠性的核心保障"""
        # 模拟策略执行失败
        strategy_name = "momentum_strategy_v2"
        error_details = "Division by zero in Sharpe ratio calculation"

        def execute_strategy():
            try:
                # 模拟策略计算错误
                sharpe_ratio = 0.15 / 0  # 除零错误
            except ZeroDivisionError:
                raise StrategyError(
                    f"Strategy execution failed: {strategy_name} - {error_details}"
                )

        # 验证业务价值：策略错误被正确捕获和报告
        with pytest.raises(StrategyError) as exc_info:
            execute_strategy()

        error_message = str(exc_info.value)
        assert strategy_name in error_message
        assert error_details in error_message

        # 验证异常可以被引擎层统一处理
        assert isinstance(exc_info.value, EngineError)

    def test_data_source_reliability_scenario(self):
        """测试数据源可靠性场景 - 数据质量保障的核心需求"""
        # 模拟数据源问题
        data_provider = "market_data_api"
        symbol = "000001.XSHE"

        def fetch_market_data():
            # 模拟网络连接失败
            raise DataSourceError(
                f"Failed to fetch data for {symbol} from {data_provider}: Connection timeout"
            )

        def validate_data_quality():
            # 模拟数据验证失败
            raise DataValidationError(
                f"Invalid price data for {symbol}: Negative close price detected"
            )

        # 验证业务价值：数据问题被正确识别和分类
        with pytest.raises(DataSourceError):
            fetch_market_data()

        with pytest.raises(DataValidationError):
            validate_data_quality()

        # 验证异常可以被统一的数据层处理
        try:
            fetch_market_data()
        except DataSourceError as e:
            assert isinstance(e, SimTradeLabError)
            assert data_provider in str(e)
            assert symbol in str(e)

    def test_configuration_error_in_production_scenario(self):
        """测试生产环境配置错误场景 - 系统部署的关键保障"""
        # 模拟配置错误
        missing_config = "database_connection_string"
        invalid_config = "risk_threshold"

        def validate_system_configuration():
            # 模拟缺失配置
            if not missing_config:
                raise ConfigurationError(
                    f"Required configuration missing: {missing_config}"
                )

            # 模拟无效配置值
            risk_threshold = -0.1  # 负值风险阈值
            if risk_threshold < 0:
                raise ConfigurationError(
                    f"Invalid {invalid_config}: {risk_threshold}. Must be non-negative"
                )

        # 验证业务价值：配置问题在系统启动时被检测
        with pytest.raises(ConfigurationError) as exc_info:
            validate_system_configuration()

        error_message = str(exc_info.value)
        assert "Must be non-negative" in error_message


class TestSystemRecoveryAndDiagnostics:
    """测试系统恢复和诊断的核心能力"""

    def test_trading_system_error_recovery_flow(self):
        """测试交易系统错误恢复流程 - 系统韧性的关键验证"""
        system_errors = []
        recovery_actions = []

        def simulate_trading_day():
            try:
                # 模拟数据获取失败
                raise DataLoadError("Market data feed interrupted")
            except DataLoadError:
                system_errors.append("data_feed_failure")
                recovery_actions.append("switched_to_backup_feed")

                try:
                    # 模拟策略执行失败
                    raise StrategyError(
                        "Strategy calculation error due to missing data"
                    )
                except StrategyError:
                    system_errors.append("strategy_failure")
                    recovery_actions.append("halted_strategy_execution")

                    # 模拟最终的引擎错误
                    raise EngineError(
                        "Trading engine stopped due to multiple component failures"
                    )

        # 验证业务价值：系统能够跟踪错误链并执行恢复策略
        with pytest.raises(EngineError) as exc_info:
            simulate_trading_day()

        # 验证错误恢复链被正确记录
        assert len(system_errors) == 2
        assert "data_feed_failure" in system_errors
        assert "strategy_failure" in system_errors
        assert len(recovery_actions) == 2
        assert "switched_to_backup_feed" in recovery_actions
        assert "halted_strategy_execution" in recovery_actions

    def test_exception_context_preservation_for_debugging(self):
        """测试异常上下文保持 - 问题诊断的关键能力"""
        trading_context = {
            "strategy": "momentum_reversal",
            "symbol": "000001.XSHE",
            "timestamp": "2024-01-15 09:30:00",
            "market_condition": "high_volatility",
        }

        def problematic_calculation():
            # 模拟嵌套的计算错误
            try:
                # 低层数据错误
                raise DataValidationError("Invalid price data: NaN values detected")
            except DataValidationError as data_error:
                # 中层策略错误
                try:
                    raise StrategyError(
                        f"Strategy {trading_context['strategy']} failed due to data issues"
                    ) from data_error
                except StrategyError as strategy_error:
                    # 高层引擎错误
                    raise EngineError(
                        f"Engine failure at {trading_context['timestamp']} "
                        f"for {trading_context['symbol']} in {trading_context['market_condition']} conditions"
                    ) from strategy_error

        # 验证业务价值：完整的错误上下文有助于快速诊断问题
        with pytest.raises(EngineError) as exc_info:
            problematic_calculation()

        # 验证异常链保持了完整的诊断信息
        engine_error = exc_info.value
        assert trading_context["timestamp"] in str(engine_error)
        assert trading_context["symbol"] in str(engine_error)
        assert trading_context["market_condition"] in str(engine_error)

        # 验证异常链
        assert engine_error.__cause__ is not None
        strategy_error = engine_error.__cause__
        assert isinstance(strategy_error, StrategyError)
        assert trading_context["strategy"] in str(strategy_error)

        assert strategy_error.__cause__ is not None
        data_error = strategy_error.__cause__
        assert isinstance(data_error, DataValidationError)
        assert "NaN values" in str(data_error)

    def test_production_monitoring_exception_patterns(self):
        """测试生产监控异常模式 - 系统稳定性监控的核心需求"""
        # 模拟生产环境中的常见异常模式
        exception_patterns = []

        # 资金管理异常
        try:
            raise InsufficientFundsError(
                "Portfolio cash depleted: $125.50 remaining, order requires $50,000"
            )
        except InsufficientFundsError as e:
            exception_patterns.append(
                {
                    "type": "fund_management",
                    "severity": "high",
                    "message": str(e),
                    "requires_immediate_attention": True,
                }
            )

        # 数据质量异常
        try:
            raise DataValidationError(
                "Price anomaly detected: 000001.XSHE jumped 150% in 1 second"
            )
        except DataValidationError as e:
            exception_patterns.append(
                {
                    "type": "data_quality",
                    "severity": "medium",
                    "message": str(e),
                    "requires_immediate_attention": False,
                }
            )

        # 策略性能异常
        try:
            raise StrategyError(
                "Strategy performance degraded: -15% return in last 5 trading days"
            )
        except StrategyError as e:
            exception_patterns.append(
                {
                    "type": "strategy_performance",
                    "severity": "medium",
                    "message": str(e),
                    "requires_immediate_attention": False,
                }
            )

        # 验证业务价值：异常被正确分类和优先级排序
        assert len(exception_patterns) == 3

        high_severity_count = sum(
            1 for p in exception_patterns if p["severity"] == "high"
        )
        immediate_attention_count = sum(
            1 for p in exception_patterns if p["requires_immediate_attention"]
        )

        assert high_severity_count == 1  # 资金管理问题
        assert immediate_attention_count == 1  # 需要立即关注的问题

        # 验证具体的业务信息被保留
        fund_pattern = next(
            p for p in exception_patterns if p["type"] == "fund_management"
        )
        assert "$125.50" in fund_pattern["message"]
        assert "$50,000" in fund_pattern["message"]


class TestSimpleExceptionFunctionality:
    """测试异常的基本功能完整性"""

    def test_all_exception_types_instantiable(self):
        """验证所有异常类型都可以正常实例化并包含有意义的信息"""
        exceptions_to_test = [
            (SimTradeLabError, "Base system error"),
            (DataSourceError, "Data connection failed"),
            (DataLoadError, "File load error"),
            (DataValidationError, "Data validation failed"),
            (TradingError, "Trading operation failed"),
            (InsufficientFundsError, "Insufficient funds"),
            (InsufficientPositionError, "Insufficient position"),
            (InvalidOrderError, "Invalid order"),
            (EngineError, "Engine error"),
            (StrategyError, "Strategy error"),
            (ConfigurationError, "Configuration error"),
            (ReportGenerationError, "Report generation failed"),
        ]

        for exception_class, test_message in exceptions_to_test:
            # 验证异常可以正常创建和使用
            error = exception_class(test_message)
            assert str(error) == test_message
            assert isinstance(error, SimTradeLabError)
            assert isinstance(error, Exception)

    def test_exception_hierarchy_for_unified_handling(self):
        """验证异常层次结构支持统一的错误处理策略"""
        # 交易相关异常都可以被TradingError捕获
        trading_exceptions = [
            InsufficientFundsError("Funds issue"),
            InsufficientPositionError("Position issue"),
            InvalidOrderError("Order issue"),
        ]

        for exception in trading_exceptions:
            with pytest.raises(TradingError):
                raise exception

        # 引擎相关异常都可以被EngineError捕获
        engine_exceptions = [
            StrategyError("Strategy issue"),
        ]

        for exception in engine_exceptions:
            with pytest.raises(EngineError):
                raise exception

        # 数据相关异常都可以被DataSourceError捕获
        data_exceptions = [
            DataLoadError("Load issue"),
            DataValidationError("Validation issue"),
        ]

        for exception in data_exceptions:
            with pytest.raises(DataSourceError):
                raise exception
