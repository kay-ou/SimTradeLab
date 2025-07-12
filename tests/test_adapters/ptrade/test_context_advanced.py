# -*- coding: utf-8 -*-
"""
PTrade Context 集成测试和规范兼容性验证

测试增强后的 PTradeContext 对象是否完全符合 PTrade 规范，
以及与系统其他组件的集成是否正确。

对于基础的单元测试，请参考 test_context.py。
"""

import logging

import pytest

from simtradelab.adapters.ptrade.context import (
    create_backtest_context,
    create_research_context,
    create_trading_context,
)


@pytest.mark.integration
def test_ptrade_context_completeness():
    """测试PTrade Context对象的完整性"""

    print("=== PTrade Context 对象完整性测试 ===\n")

    # 1. 测试创建不同模式的Context
    print("1. 测试Context创建和基础属性:")

    # 创建回测模式上下文
    context = create_backtest_context(capital_base=1000000, commission_rate=0.0003)

    print(f"   ✓ 模式: {context.mode}")
    print(f"   ✓ 起始资金: {context.capital_base}")
    print(f"   ✓ 当前现金: {context.portfolio.cash}")
    print(f"   ✓ 是否已初始化: {context.initialized}")
    print(f"   ✓ 佣金费率: {context.commission.cost}")
    print(f"   ✓ 滑点: {context.slippage.price_impact}")

    # 2. 测试PTrade官方Context属性
    print("\n2. 测试PTrade官方Context属性:")

    required_attrs = [
        "capital_base",
        "previous_date",
        "sim_params",
        "portfolio",
        "initialized",
        "slippage",
        "commission",
        "blotter",
        "recorded_vars",
    ]

    for attr in required_attrs:
        if hasattr(context, attr):
            print(f"   ✓ {attr}: 已实现")
        else:
            print(f"   ✗ {attr}: 缺失")

    # 3. 测试g全局对象
    print("\n3. 测试g全局对象:")
    try:
        context.g.test_var = "测试值"
        context.g.counter = 1
        print(f"   ✓ g.test_var: {context.g.test_var}")
        print(f"   ✓ g.counter: {context.g.counter}")
    except Exception as e:
        print(f"   ✗ g对象测试失败: {e}")

    # 4. 测试生命周期管理
    print("\n4. 测试生命周期管理:")

    # 注册策略函数
    def test_initialize(ctx):
        ctx.log_info("Initialize called")
        ctx.set_universe(["000001.SZ", "000002.SZ"])
        ctx.set_benchmark("000300.SH")

    def test_handle_data(ctx, data):
        ctx.log_info("Handle data called")
        ctx.record("test_value", 100)

    context.register_initialize(test_initialize)
    context.register_handle_data(test_handle_data)

    # 执行生命周期
    try:
        print(f"   • 当前阶段: {context.get_current_lifecycle_phase()}")

        context.execute_initialize()
        print(f"   ✓ Initialize执行完成, 当前阶段: {context.get_current_lifecycle_phase()}")
        print(f"   ✓ 股票池: {context.universe}")
        print(f"   ✓ 基准: {context.benchmark}")

        context.execute_handle_data({"test": "data"})
        print(f"   ✓ Handle data执行完成, 当前阶段: {context.get_current_lifecycle_phase()}")
        print(f"   ✓ 记录的变量: {context.recorded_vars}")

    except Exception as e:
        print(f"   ✗ 生命周期执行失败: {e}")

    # 5. 测试策略配置管理
    print("\n5. 测试策略配置管理:")

    config_tests = [
        ("set_commission", [0.0005], "commission.cost"),
        ("set_slippage", [0.001], "slippage.price_impact"),
        ("set_volume_ratio", [0.3], "_volume_ratio"),
        ("set_limit_mode", ["amount"], "_limit_mode"),
        ("set_parameters", [{"param1": "value1"}], "_parameters"),
    ]

    for method_name, args, attr_path in config_tests:
        try:
            method = getattr(context, method_name)
            method(*args)

            # 获取属性值
            obj = context
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)

            print(f"   ✓ {method_name}: 设置成功, 值: {obj}")
        except Exception as e:
            print(f"   ✗ {method_name}: 设置失败 - {e}")

    # 6. 测试调度任务管理
    print("\n6. 测试调度任务管理:")

    def daily_task():
        print("Daily task executed")

    def interval_task():
        print("Interval task executed")

    try:
        context.run_daily(daily_task, "09:30")
        context.run_interval(interval_task, 60)

        print(f"   ✓ 日级任务数: {len(context._daily_tasks)}")
        print(f"   ✓ 间隔任务数: {len(context._interval_tasks)}")

        if context._daily_tasks:
            print(f"   ✓ 日级任务时间: {context._daily_tasks[0]['time']}")

        if context._interval_tasks:
            print(f"   ✓ 间隔任务间隔: {context._interval_tasks[0]['interval']}")

    except Exception as e:
        print(f"   ✗ 调度任务测试失败: {e}")

    # 7. 测试API权限检查
    print("\n7. 测试API权限检查:")

    api_tests = [
        ("set_universe", "initialize"),
        ("order", "handle_data"),
        ("get_price", "all"),
    ]

    for api_name, expected_phase in api_tests:
        allowed = context.is_api_allowed(api_name)
        current_phase = context.get_current_lifecycle_phase()
        print(f"   • {api_name} 在 {current_phase} 阶段: {'允许' if allowed else '不允许'}")

    # 8. 测试期货期权支持
    print("\n8. 测试期货期权支持:")

    try:
        context.set_future_commission(0.0002)
        context.set_margin_rate("IC2312", 0.15)

        print(f"   ✓ 期货手续费: {context._future_params.commission}")
        print(f"   ✓ IC2312保证金比例: {context._margin_rate_overrides.get('IC2312')}")

    except Exception as e:
        print(f"   ✗ 期货期权测试失败: {e}")

    # 9. 测试统计信息
    print("\n9. 测试统计信息:")

    try:
        stats = context.get_lifecycle_statistics()
        print(f"   ✓ 总API调用: {stats['total_api_calls']}")
        print(f"   ✓ 当前阶段: {stats['current_phase']}")
        print(f"   ✓ 已执行阶段: {stats['phases_executed']}")

    except Exception as e:
        print(f"   ✗ 统计信息获取失败: {e}")

    print("\n=== PTrade Context 完整性测试完成 ===")


@pytest.mark.unit
def test_context_factory_functions():
    """测试Context工厂函数"""

    print("\n=== Context 工厂函数测试 ===\n")

    # 1. 测试研究模式Context
    print("1. 测试研究模式Context:")
    research_ctx = create_research_context(500000)
    print(f"   ✓ 模式: {research_ctx.mode}")
    print(f"   ✓ 起始资金: {research_ctx.capital_base}")

    # 2. 测试回测模式Context
    print("\n2. 测试回测模式Context:")
    backtest_ctx = create_backtest_context(1000000, 0.0003, 0.001)
    print(f"   ✓ 模式: {backtest_ctx.mode}")
    print(f"   ✓ 佣金费率: {backtest_ctx.commission.cost}")
    print(f"   ✓ 滑点: {backtest_ctx.slippage.price_impact}")

    # 3. 测试交易模式Context
    print("\n3. 测试交易模式Context:")
    trading_ctx = create_trading_context(2000000)
    print(f"   ✓ 模式: {trading_ctx.mode}")
    print(f"   ✓ 起始资金: {trading_ctx.capital_base}")

    print("\n=== Context 工厂函数测试完成 ===")


@pytest.mark.integration
def test_context_lifecycle_integration():
    """测试Context与生命周期控制器的集成"""

    print("\n=== Context 生命周期集成测试 ===\n")

    context = create_backtest_context()

    # 策略函数计数器
    call_counts = {"init": 0, "handle": 0, "before": 0, "after": 0}

    def init_func(ctx):
        call_counts["init"] += 1
        ctx.set_universe(["000001.SZ"])
        return "init_result"

    def handle_func(ctx, data):
        call_counts["handle"] += 1
        return "handle_result"

    def before_func(ctx, data):
        call_counts["before"] += 1
        return "before_result"

    def after_func(ctx, data):
        call_counts["after"] += 1
        return "after_result"

    # 注册策略函数
    context.register_initialize(init_func)
    context.register_handle_data(handle_func)
    context.register_before_trading_start(before_func)
    context.register_after_trading_end(after_func)

    # 执行完整的生命周期
    print("1. 执行完整策略生命周期:")

    try:
        # Initialize
        result = context.execute_initialize()
        print(f"   ✓ Initialize: 调用{call_counts['init']}次, 结果: {result}")
        print(f"   ✓ 初始化状态: {context.initialized}")

        # Before trading start
        result = context.execute_before_trading_start({"market": "opening"})
        print(f"   ✓ Before trading: 调用{call_counts['before']}次, 结果: {result}")

        # Handle data (多次调用)
        for i in range(3):
            result = context.execute_handle_data({"bar": i})

        print(f"   ✓ Handle data: 调用{call_counts['handle']}次")

        # After trading end
        result = context.execute_after_trading_end({"market": "closed"})
        print(f"   ✓ After trading: 调用{call_counts['after']}次, 结果: {result}")

        # 检查生命周期统计
        stats = context.get_lifecycle_statistics()
        print(f"   ✓ 生命周期统计: {len(stats['phases_executed'])} 个阶段已执行")

    except Exception as e:
        print(f"   ✗ 生命周期执行失败: {e}")

    # 2. 测试重置功能
    print("\n2. 测试Context重置功能:")

    try:
        context.reset_for_new_strategy()
        print(f"   ✓ 重置后初始化状态: {context.initialized}")
        print(f"   ✓ 重置后记录变量: {len(context.recorded_vars)}")
        print(f"   ✓ 重置后调度任务: {len(context._daily_tasks)}")

        stats = context.get_lifecycle_statistics()
        print(f"   ✓ 重置后API调用数: {stats['total_api_calls']}")

    except Exception as e:
        print(f"   ✗ 重置功能测试失败: {e}")

    print("\n=== Context 生命周期集成测试完成 ===")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    test_ptrade_context_completeness()
    test_context_factory_functions()
    test_context_lifecycle_integration()
