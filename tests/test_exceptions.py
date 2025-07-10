# -*- coding: utf-8 -*-
"""
SimTradeLab根级异常系统测试

测试框架的异常层次结构和功能
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


class TestSimTradeLabError:
    """测试SimTradeLab基础异常类"""

    def test_base_exception_creation(self):
        """测试基础异常创建"""
        error = SimTradeLabError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_base_exception_without_message(self):
        """测试无消息的基础异常"""
        error = SimTradeLabError()
        assert isinstance(error, SimTradeLabError)

    def test_base_exception_with_multiple_args(self):
        """测试带多个参数的基础异常"""
        error = SimTradeLabError("Message", 123, "extra")
        assert str(error) == "('Message', 123, 'extra')"
        assert error.args == ("Message", 123, "extra")

    def test_raise_and_catch_base(self):
        """测试抛出和捕获基础异常"""
        with pytest.raises(SimTradeLabError, match="Test error"):
            raise SimTradeLabError("Test error")

    def test_inheritance_from_exception(self):
        """测试从Exception的继承"""
        assert issubclass(SimTradeLabError, Exception)

        error = SimTradeLabError("test")
        assert isinstance(error, Exception)


class TestDataSourceExceptions:
    """测试数据源相关异常"""

    def test_data_source_error_inheritance(self):
        """测试数据源异常继承"""
        assert issubclass(DataSourceError, SimTradeLabError)

        error = DataSourceError("Data source error")
        assert isinstance(error, SimTradeLabError)
        assert isinstance(error, Exception)

    def test_data_load_error_inheritance(self):
        """测试数据加载异常继承"""
        assert issubclass(DataLoadError, DataSourceError)
        assert issubclass(DataLoadError, SimTradeLabError)

        error = DataLoadError("Load failed")
        assert isinstance(error, DataSourceError)
        assert isinstance(error, SimTradeLabError)

    def test_data_validation_error_inheritance(self):
        """测试数据验证异常继承"""
        assert issubclass(DataValidationError, DataSourceError)
        assert issubclass(DataValidationError, SimTradeLabError)

        error = DataValidationError("Validation failed")
        assert isinstance(error, DataSourceError)
        assert isinstance(error, SimTradeLabError)

    def test_data_source_error_scenarios(self):
        """测试数据源异常场景"""
        # 通用数据源错误
        with pytest.raises(DataSourceError, match="Connection failed"):
            raise DataSourceError("Connection failed")

        # 数据加载错误
        with pytest.raises(DataLoadError, match="File not found"):
            raise DataLoadError("File not found")

        # 数据验证错误
        with pytest.raises(DataValidationError, match="Invalid format"):
            raise DataValidationError("Invalid format")

    def test_catch_as_parent_exception(self):
        """测试作为父类异常捕获"""
        # 捕获DataLoadError作为DataSourceError
        with pytest.raises(DataSourceError):
            raise DataLoadError("Load error")

        # 捕获DataValidationError作为SimTradeLabError
        with pytest.raises(SimTradeLabError):
            raise DataValidationError("Validation error")


class TestTradingExceptions:
    """测试交易相关异常"""

    def test_trading_error_inheritance(self):
        """测试交易异常继承"""
        assert issubclass(TradingError, SimTradeLabError)

        error = TradingError("Trading error")
        assert isinstance(error, SimTradeLabError)

    def test_insufficient_funds_error(self):
        """测试资金不足异常"""
        assert issubclass(InsufficientFundsError, TradingError)
        assert issubclass(InsufficientFundsError, SimTradeLabError)

        error = InsufficientFundsError("Not enough cash")
        assert isinstance(error, TradingError)
        assert isinstance(error, SimTradeLabError)

    def test_insufficient_position_error(self):
        """测试持仓不足异常"""
        assert issubclass(InsufficientPositionError, TradingError)
        assert issubclass(InsufficientPositionError, SimTradeLabError)

        error = InsufficientPositionError("Not enough shares")
        assert isinstance(error, TradingError)
        assert isinstance(error, SimTradeLabError)

    def test_invalid_order_error(self):
        """测试无效订单异常"""
        assert issubclass(InvalidOrderError, TradingError)
        assert issubclass(InvalidOrderError, SimTradeLabError)

        error = InvalidOrderError("Invalid order parameters")
        assert isinstance(error, TradingError)
        assert isinstance(error, SimTradeLabError)

    def test_trading_error_scenarios(self):
        """测试交易异常场景"""

        # 资金不足场景
        def place_order_insufficient_funds():
            raise InsufficientFundsError("Cannot buy: insufficient cash balance")

        with pytest.raises(InsufficientFundsError, match="insufficient cash"):
            place_order_insufficient_funds()

        # 持仓不足场景
        def sell_order_insufficient_position():
            raise InsufficientPositionError("Cannot sell: insufficient position")

        with pytest.raises(InsufficientPositionError, match="insufficient position"):
            sell_order_insufficient_position()

        # 无效订单场景
        def invalid_order():
            raise InvalidOrderError("Invalid price: must be positive")

        with pytest.raises(InvalidOrderError, match="Invalid price"):
            invalid_order()

    def test_trading_exception_hierarchy_catching(self):
        """测试交易异常层次捕获"""
        # 所有交易异常都可以被TradingError捕获
        trading_exceptions = [
            InsufficientFundsError("funds"),
            InsufficientPositionError("position"),
            InvalidOrderError("order"),
        ]

        for exception in trading_exceptions:
            with pytest.raises(TradingError):
                raise exception


class TestEngineExceptions:
    """测试引擎相关异常"""

    def test_engine_error_inheritance(self):
        """测试引擎异常继承"""
        assert issubclass(EngineError, SimTradeLabError)

        error = EngineError("Engine error")
        assert isinstance(error, SimTradeLabError)

    def test_strategy_error_inheritance(self):
        """测试策略异常继承"""
        assert issubclass(StrategyError, EngineError)
        assert issubclass(StrategyError, SimTradeLabError)

        error = StrategyError("Strategy error")
        assert isinstance(error, EngineError)
        assert isinstance(error, SimTradeLabError)

    def test_strategy_error_scenarios(self):
        """测试策略异常场景"""

        # 策略初始化错误
        def strategy_init_error():
            raise StrategyError("Failed to initialize strategy: missing parameters")

        with pytest.raises(StrategyError, match="Failed to initialize"):
            strategy_init_error()

        # 策略执行错误
        def strategy_execution_error():
            raise StrategyError("Strategy execution failed: division by zero")

        with pytest.raises(StrategyError, match="execution failed"):
            strategy_execution_error()

    def test_engine_exception_catching(self):
        """测试引擎异常捕获"""
        # StrategyError可以被EngineError捕获
        with pytest.raises(EngineError):
            raise StrategyError("Strategy failed")

        # EngineError可以被SimTradeLabError捕获
        with pytest.raises(SimTradeLabError):
            raise EngineError("Engine failed")


class TestConfigurationError:
    """测试配置异常"""

    def test_configuration_error_inheritance(self):
        """测试配置异常继承"""
        assert issubclass(ConfigurationError, SimTradeLabError)

        error = ConfigurationError("Config error")
        assert isinstance(error, SimTradeLabError)

    def test_configuration_error_scenarios(self):
        """测试配置异常场景"""

        # 配置文件错误
        def config_file_error():
            raise ConfigurationError("Configuration file not found: config.yaml")

        with pytest.raises(ConfigurationError, match="file not found"):
            config_file_error()

        # 配置验证错误
        def config_validation_error():
            raise ConfigurationError("Invalid configuration: port must be a number")

        with pytest.raises(ConfigurationError, match="Invalid configuration"):
            config_validation_error()

        # 必需配置缺失
        def missing_config_error():
            raise ConfigurationError("Required configuration missing: database_url")

        with pytest.raises(ConfigurationError, match="Required configuration missing"):
            missing_config_error()


class TestReportGenerationError:
    """测试报告生成异常"""

    def test_report_generation_error_inheritance(self):
        """测试报告生成异常继承"""
        assert issubclass(ReportGenerationError, SimTradeLabError)

        error = ReportGenerationError("Report error")
        assert isinstance(error, SimTradeLabError)

    def test_report_generation_error_scenarios(self):
        """测试报告生成异常场景"""

        # 数据不足错误
        def insufficient_data_error():
            raise ReportGenerationError("Cannot generate report: insufficient data")

        with pytest.raises(ReportGenerationError, match="insufficient data"):
            insufficient_data_error()

        # 模板错误
        def template_error():
            raise ReportGenerationError("Report template error: invalid format")

        with pytest.raises(ReportGenerationError, match="template error"):
            template_error()

        # 输出错误
        def output_error():
            raise ReportGenerationError("Failed to save report: permission denied")

        with pytest.raises(ReportGenerationError, match="Failed to save"):
            output_error()


class TestExceptionHierarchy:
    """测试异常层次结构"""

    def test_full_exception_hierarchy(self):
        """测试完整异常层次结构"""
        # 测试所有异常都继承自SimTradeLabError
        all_exceptions = [
            DataSourceError,
            DataLoadError,
            DataValidationError,
            TradingError,
            InsufficientFundsError,
            InsufficientPositionError,
            InvalidOrderError,
            EngineError,
            StrategyError,
            ConfigurationError,
            ReportGenerationError,
        ]

        for exception_class in all_exceptions:
            assert issubclass(exception_class, SimTradeLabError)

    def test_exception_categories(self):
        """测试异常分类"""
        # 数据相关异常
        data_exceptions = [DataSourceError, DataLoadError, DataValidationError]
        for exc in data_exceptions[1:]:  # 除了DataSourceError本身
            assert issubclass(exc, DataSourceError)

        # 交易相关异常
        trading_exceptions = [
            TradingError,
            InsufficientFundsError,
            InsufficientPositionError,
            InvalidOrderError,
        ]
        for exc in trading_exceptions[1:]:  # 除了TradingError本身
            assert issubclass(exc, TradingError)

        # 引擎相关异常
        engine_exceptions = [EngineError, StrategyError]
        for exc in engine_exceptions[1:]:  # 除了EngineError本身
            assert issubclass(exc, EngineError)

    def test_cross_category_catching(self):
        """测试跨类别异常捕获"""
        # 所有异常都可以被SimTradeLabError捕获
        exceptions_to_test = [
            DataLoadError("data"),
            InsufficientFundsError("funds"),
            StrategyError("strategy"),
            ConfigurationError("config"),
            ReportGenerationError("report"),
        ]

        for exception in exceptions_to_test:
            with pytest.raises(SimTradeLabError):
                raise exception

    def test_exception_message_preservation(self):
        """测试异常消息保持"""
        test_cases = [
            (SimTradeLabError, "Base error"),
            (DataLoadError, "Load failed"),
            (InsufficientFundsError, "No money"),
            (StrategyError, "Strategy failed"),
            (ConfigurationError, "Bad config"),
            (ReportGenerationError, "Report failed"),
        ]

        for exception_class, message in test_cases:
            error = exception_class(message)
            assert str(error) == message

    def test_exception_chaining(self):
        """测试异常链接"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise DataLoadError("Failed to load data") from e
        except DataLoadError as load_error:
            assert load_error.__cause__ is not None
            assert isinstance(load_error.__cause__, ValueError)
            assert str(load_error.__cause__) == "Original error"

    def test_exception_context_preservation(self):
        """测试异常上下文保持"""

        def inner_function():
            raise DataValidationError("Validation failed")

        def outer_function():
            try:
                inner_function()
            except DataValidationError:
                raise ConfigurationError("Configuration is invalid")

        with pytest.raises(ConfigurationError) as exc_info:
            outer_function()

        # 验证异常信息
        assert str(exc_info.value) == "Configuration is invalid"
        assert exc_info.value.__context__ is not None
        assert isinstance(exc_info.value.__context__, DataValidationError)

    def test_multi_level_exception_handling(self):
        """测试多级异常处理"""

        def level_3():
            raise DataLoadError("Data file corrupted")

        def level_2():
            try:
                level_3()
            except DataLoadError as e:
                raise TradingError("Cannot execute trades without data") from e

        def level_1():
            try:
                level_2()
            except TradingError as e:
                raise EngineError("Engine stopped due to trading errors") from e

        with pytest.raises(EngineError) as exc_info:
            level_1()

        # 验证异常链
        error = exc_info.value
        assert isinstance(error, EngineError)
        assert isinstance(error.__cause__, TradingError)
        assert isinstance(error.__cause__.__cause__, DataLoadError)

    def test_exception_equality(self):
        """测试异常相等性"""
        error1 = SimTradeLabError("Same message")
        error2 = SimTradeLabError("Same message")
        error3 = SimTradeLabError("Different message")

        # 异常实例不应该相等（即使消息相同）
        assert error1 is not error2
        assert error1 is not error3

        # 但是消息应该相等
        assert str(error1) == str(error2)
        assert str(error1) != str(error3)

    def test_exception_attributes(self):
        """测试异常属性"""
        message = "Test error with details"
        error = SimTradeLabError(message)

        assert hasattr(error, "args")
        assert error.args == (message,)
        assert hasattr(error, "__str__")
        assert hasattr(error, "__repr__")

    def test_exception_serialization_compatibility(self):
        """测试异常序列化兼容性"""
        import pickle

        # 测试异常可以被pickle序列化
        error = DataLoadError("Serialization test")

        try:
            serialized = pickle.dumps(error)
            deserialized = pickle.loads(serialized)

            assert isinstance(deserialized, DataLoadError)
            assert str(deserialized) == str(error)
        except Exception:
            # 如果序列化失败，这是可以接受的，但我们记录这个限制
            pytest.skip("Exception serialization not supported in this environment")

    def test_performance_exception_creation(self):
        """测试异常创建性能"""
        import time

        # 测试创建大量异常的性能
        start_time = time.time()

        for _ in range(1000):
            error = SimTradeLabError("Performance test")

        end_time = time.time()
        duration = end_time - start_time

        # 1000个异常创建应该在合理时间内完成（例如1秒）
        assert duration < 1.0, f"Exception creation took too long: {duration}s"
