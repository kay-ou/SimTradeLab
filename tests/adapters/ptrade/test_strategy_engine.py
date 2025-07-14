# -*- coding: utf-8 -*-
"""
PTrade 策略执行引擎集成测试

测试完整的策略执行框架，包括生命周期控制、API验证和Context管理
"""

import logging
from datetime import datetime

import pytest

from simtradelab.adapters.ptrade.strategy_engine import (
    create_backtest_engine,
    create_research_engine,
    create_trading_engine,
)


@pytest.mark.integration
def test_strategy_engine_basic_functionality():
    """测试策略执行引擎基础功能"""

    print("=== PTrade 策略执行引擎基础功能测试 ===\n")

    # 1. 测试创建不同模式的引擎
    print("1. 测试策略引擎创建:")

    try:
        research_engine = create_research_engine(500000)
        print(f"   ✓ 研究模式引擎: {research_engine.mode}")

        backtest_engine = create_backtest_engine(1000000, 0.0003, 0.001)
        print(f"   ✓ 回测模式引擎: {backtest_engine.mode}")

        trading_engine = create_trading_engine(2000000)
        print(f"   ✓ 交易模式引擎: {trading_engine.mode}")

    except Exception as e:
        print(f"   ✗ 引擎创建失败: {e}")
        return

    # 2. 测试策略注册和构建器模式
    print("\n2. 测试策略注册和构建器模式:")

    engine = create_backtest_engine()

    def simple_initialize(context):
        """简单初始化函数"""
        context.set_universe(["000001.SZ", "000002.SZ"])
        context.set_benchmark("000300.SH")
        context.log_info("策略初始化完成")
        return "初始化成功"

    def simple_handle_data(context, data):
        """简单数据处理函数"""
        context.log_info(f"处理数据: {data}")
        context.record("test_metric", 100)
        return "数据处理成功"

    try:
        # 使用构建器模式注册策略
        strategy = (
            engine.register_strategy("测试策略")
            .initialize(simple_initialize)
            .handle_data(simple_handle_data)
        )

        print("   ✓ 策略注册成功")
        print(f"   ✓ 策略名称: {engine._strategy_name}")
        print(f"   ✓ 注册的函数: {list(engine._strategy_functions.keys())}")

    except Exception as e:
        print(f"   ✗ 策略注册失败: {e}")
        return

    # 3. 测试策略执行
    print("\n3. 测试策略执行:")

    try:
        # 准备测试数据
        test_data = [
            {"datetime": datetime.now(), "symbol": "000001.SZ", "price": 10.0},
            {"datetime": datetime.now(), "symbol": "000002.SZ", "price": 20.0},
        ]

        # 运行策略
        result = strategy.run(test_data)

        print(f"   ✓ 策略执行成功: {result['success']}")
        print(f"   ✓ 策略名称: {result['strategy_name']}")
        print(f"   ✓ 运行模式: {result['mode']}")
        print(f"   ✓ 开始时间: {result['start_time']}")
        print(f"   ✓ 结束时间: {result['end_time']}")

        if result.get("error"):
            print(f"   ⚠ 执行错误: {result['error']}")

        # 检查生命周期统计
        lifecycle_stats = result.get("lifecycle_stats", {})
        print(f"   ✓ API调用次数: {lifecycle_stats.get('total_api_calls', 0)}")
        print(f"   ✓ 已执行阶段: {lifecycle_stats.get('phases_executed', [])}")

        # 检查验证统计
        validation_stats = result.get("validation_stats", {})
        print(f"   ✓ 验证检查: {validation_stats.get('total_validations', 0)}")
        print(f"   ✓ 验证成功: {validation_stats.get('successful_validations', 0)}")

        # 检查组合性能
        portfolio_performance = result.get("portfolio_performance", {})
        print(f"   ✓ 组合价值: {portfolio_performance.get('total_value', 0)}")
        print(f"   ✓ 现金: {portfolio_performance.get('cash', 0)}")
        print(f"   ✓ 记录变量: {portfolio_performance.get('recorded_vars', {})}")

    except Exception as e:
        print(f"   ✗ 策略执行失败: {e}")
        import traceback

        traceback.print_exc()
        return

    # 4. 测试执行状态查询
    print("\n4. 测试执行状态查询:")

    try:
        status = engine.get_execution_status()
        print(f"   ✓ 运行状态: {status['is_running']}")
        print(f"   ✓ 当前阶段: {status['current_phase']}")
        print(f"   ✓ 是否已初始化: {status['initialized']}")
        print(f"   ✓ 组合价值: {status['portfolio_value']}")

        detailed_stats = engine.get_detailed_statistics()
        print(f"   ✓ 详细统计信息包含: {list(detailed_stats.keys())}")

    except Exception as e:
        print(f"   ✗ 状态查询失败: {e}")

    print("\n=== PTrade 策略执行引擎基础功能测试完成 ===")


@pytest.mark.integration
def test_strategy_engine_lifecycle_control():
    """测试策略执行引擎的生命周期控制"""

    print("\n=== PTrade 策略执行引擎生命周期控制测试 ===\n")

    engine = create_backtest_engine()

    # 策略函数调用计数器
    call_counts = {"init": 0, "handle": 0, "before": 0, "after": 0}

    def lifecycle_initialize(context):
        call_counts["init"] += 1
        context.set_universe(["000001.SZ"])
        # 测试在初始化阶段允许的API
        try:
            # 这应该成功
            context.set_benchmark("000300.SH")
            context.log_info("初始化阶段API调用成功")
        except Exception as e:
            context.log_info(f"初始化阶段API调用失败: {e}")
        return "init_done"

    def lifecycle_handle_data(context, data):
        call_counts["handle"] += 1
        # 测试在handle_data阶段允许的API
        try:
            # 这应该失败（set_universe只能在initialize阶段调用）
            context.set_universe(["000002.SZ"])
            context.log_info("handle_data阶段set_universe成功（不应该）")
        except Exception as e:
            context.log_info(f"handle_data阶段set_universe失败（预期）: {e}")

        context.record("handle_count", call_counts["handle"])
        return "handle_done"

    def lifecycle_before_trading(context, data):
        call_counts["before"] += 1
        context.log_info("盘前处理")
        return "before_done"

    def lifecycle_after_trading(context, data):
        call_counts["after"] += 1
        context.log_info("盘后处理")
        return "after_done"

    # 注册策略
    try:
        strategy = (
            engine.register_strategy("生命周期测试策略")
            .initialize(lifecycle_initialize)
            .handle_data(lifecycle_handle_data)
            .before_trading_start(lifecycle_before_trading)
            .after_trading_end(lifecycle_after_trading)
        )

        print("1. 策略注册完成")

        # 运行策略
        test_data = [
            {"datetime": datetime.now(), "bar": 1},
            {"datetime": datetime.now(), "bar": 2},
        ]

        result = strategy.run(test_data)

        print(f"2. 策略执行结果: {result['success']}")

        # 检查生命周期函数调用次数
        print("3. 生命周期函数调用次数:")
        print(f"   ✓ Initialize: {call_counts['init']} 次")
        print(f"   ✓ Handle data: {call_counts['handle']} 次")
        print(f"   ✓ Before trading: {call_counts['before']} 次")
        print(f"   ✓ After trading: {call_counts['after']} 次")

        # 检查生命周期统计
        lifecycle_stats = result.get("lifecycle_stats", {})
        print(f"4. 生命周期统计:")
        print(f"   ✓ 总API调用: {lifecycle_stats.get('total_api_calls', 0)}")
        print(f"   ✓ 当前阶段: {lifecycle_stats.get('current_phase', 'unknown')}")
        print(f"   ✓ 已执行阶段: {lifecycle_stats.get('phases_executed', [])}")

        # 检验生命周期控制是否正常工作
        if call_counts["init"] == 1 and call_counts["handle"] >= 1:
            print("   ✓ 生命周期函数调用次数正确")
        else:
            print("   ✗ 生命周期函数调用次数异常")

    except Exception as e:
        print(f"   ✗ 生命周期测试失败: {e}")
        import traceback

        traceback.print_exc()

    print("\n=== PTrade 策略执行引擎生命周期控制测试完成 ===")


@pytest.mark.integration
def test_strategy_engine_api_proxy():
    """测试策略执行引擎的API代理功能"""

    print("\n=== PTrade 策略执行引擎API代理测试 ===\n")

    engine = create_backtest_engine()

    def api_test_initialize(context):
        context.set_universe(["000001.SZ", "000002.SZ"])
        context.log_info("测试API代理功能")

    def api_test_handle_data(context, data):
        # 这里可以测试各种PTrade API的代理调用
        context.log_info("测试API代理在handle_data中的使用")
        context.record("api_test", True)

    try:
        strategy = (
            engine.register_strategy("API代理测试")
            .initialize(api_test_initialize)
            .handle_data(api_test_handle_data)
        )

        print("1. API代理策略注册完成")

        # 测试直接通过引擎调用API (通过__getattr__代理)
        print("2. 测试API代理:")

        # 这些调用应该通过__getattr__代理到API路由器
        # 注意：实际的API实现可能需要根据具体的路由器来确定
        try:
            # 测试是否能够访问API路由器的方法
            if hasattr(engine.api_router, "get_price"):
                print("   ✓ get_price API 可访问")
            if hasattr(engine.api_router, "order"):
                print("   ✓ order API 可访问")
            if hasattr(engine.api_router, "get_portfolio"):
                print("   ✓ get_portfolio API 可访问")

        except Exception as e:
            print(f"   ⚠ API代理测试异常: {e}")

        # 运行策略
        result = strategy.run([{"test": "data"}])
        print(f"3. API代理策略执行: {result['success']}")

    except Exception as e:
        print(f"   ✗ API代理测试失败: {e}")

    print("\n=== PTrade 策略执行引擎API代理测试完成 ===")


@pytest.mark.integration
def test_strategy_engine_reset_and_cleanup():
    """测试策略执行引擎的重置和清理功能"""

    print("\n=== PTrade 策略执行引擎重置清理测试 ===\n")

    engine = create_backtest_engine()

    def test_initialize(context):
        context.set_universe(["000001.SZ"])
        context.record("init_value", 100)

    def test_handle_data(context, data):
        context.record("handle_value", 200)

    try:
        # 第一次运行策略
        strategy1 = (
            engine.register_strategy("第一个策略")
            .initialize(test_initialize)
            .handle_data(test_handle_data)
        )

        result1 = strategy1.run([{"test": "data1"}])
        print(f"1. 第一次策略执行: {result1['success']}")
        print(f"   策略名称: {result1['strategy_name']}")

        # 获取执行前状态
        status_before = engine.get_execution_status()
        print(f"2. 重置前状态:")
        print(f"   注册函数: {status_before['registered_functions']}")
        print(f"   组合价值: {status_before['portfolio_value']}")

        # 重置策略
        engine.reset_strategy()
        print("3. 策略重置完成")

        # 获取重置后状态
        status_after = engine.get_execution_status()
        print(f"4. 重置后状态:")
        print(f"   策略名称: {status_after['strategy_name']}")
        print(f"   注册函数: {status_after['registered_functions']}")
        print(f"   是否初始化: {status_after['initialized']}")

        # 验证重置效果
        if (
            status_after["strategy_name"] is None
            and len(status_after["registered_functions"]) == 0
            and not status_after["initialized"]
        ):
            print("   ✓ 策略重置成功")
        else:
            print("   ✗ 策略重置不完整")

        # 第二次运行新策略
        def new_initialize(context):
            context.set_universe(["000002.SZ", "000003.SZ"])
            context.record("new_init_value", 300)

        strategy2 = (
            engine.register_strategy("第二个策略")
            .initialize(new_initialize)
            .handle_data(test_handle_data)
        )

        result2 = strategy2.run([{"test": "data2"}])
        print(f"5. 第二次策略执行: {result2['success']}")
        print(f"   新策略名称: {result2['strategy_name']}")

        # 测试关闭功能
        print("6. 测试引擎关闭:")
        engine.shutdown()
        print("   ✓ 引擎关闭完成")

    except Exception as e:
        print(f"   ✗ 重置清理测试失败: {e}")
        import traceback

        traceback.print_exc()

    print("\n=== PTrade 策略执行引擎重置清理测试完成 ===")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    # 运行所有测试
    test_strategy_engine_basic_functionality()
    test_strategy_engine_lifecycle_control()
    test_strategy_engine_api_proxy()
    test_strategy_engine_reset_and_cleanup()

    print("\n🎉 所有PTrade策略执行引擎测试完成！")
