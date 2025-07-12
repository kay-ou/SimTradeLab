# -*- coding: utf-8 -*-
"""
PTrade 生命周期控制框架测试

测试生命周期控制器和API验证器与路由器的集成
"""

import logging

import pytest

from simtradelab.adapters.ptrade.api_validator import APIValidator
from simtradelab.adapters.ptrade.lifecycle_controller import (
    LifecycleController,
    LifecyclePhase,
)
from simtradelab.adapters.ptrade.routers.research import ResearchAPIRouter


class MockPTradeContext:
    """模拟PTrade上下文"""

    def __init__(self, mode: str = "research"):
        self.mode = mode


@pytest.mark.integration
def test_lifecycle_integration():
    """测试生命周期控制框架的完整集成"""

    # 1. 创建模拟上下文
    context = MockPTradeContext("research")

    # 2. 创建生命周期控制器和API验证器
    lifecycle_controller = LifecycleController("research")
    api_validator = APIValidator(lifecycle_controller)

    # 3. 创建研究模式路由器
    router = ResearchAPIRouter(
        context=context,
        lifecycle_controller=lifecycle_controller,
        api_validator=api_validator,
    )

    print("=== PTrade 生命周期控制框架集成测试 ===\n")

    # 4. 测试生命周期阶段设置
    print("1. 测试生命周期阶段设置:")
    try:
        router.set_lifecycle_phase("initialize")
        current_phase = router.get_current_lifecycle_phase()
        print(f"   ✓ 当前阶段设置为: {current_phase}")
    except Exception as e:
        print(f"   ✗ 阶段设置失败: {e}")

    # 5. 测试initialize阶段的API调用
    print("\n2. 测试initialize阶段API调用限制:")

    # 测试允许的API
    try:
        allowed = router.is_api_allowed_in_current_phase("set_universe")
        print(f"   ✓ set_universe 在 initialize 阶段允许: {allowed}")
    except Exception as e:
        print(f"   ✗ set_universe 检查失败: {e}")

    # 测试不允许的API
    try:
        allowed = router.is_api_allowed_in_current_phase("order")
        print(f"   ✓ order 在 initialize 阶段允许: {allowed}")
    except Exception as e:
        print(f"   ✗ order 检查失败: {e}")

    # 6. 测试阶段转换
    print("\n3. 测试生命周期阶段转换:")
    try:
        router.set_lifecycle_phase("handle_data")
        current_phase = router.get_current_lifecycle_phase()
        print(f"   ✓ 阶段转换成功: {current_phase}")

        # 现在order应该被允许
        allowed = router.is_api_allowed_in_current_phase("order")
        print(f"   ✓ order 在 handle_data 阶段允许: {allowed}")

    except Exception as e:
        print(f"   ✗ 阶段转换失败: {e}")

    # 7. 测试API调用统计
    print("\n4. 测试API调用统计:")
    try:
        stats = router.get_api_call_statistics()
        print(f"   ✓ 生命周期统计: {stats['lifecycle_stats']['total_api_calls']} 次调用")
        print(f"   ✓ 验证统计: {stats['validation_stats']['total_validations']} 次验证")
    except Exception as e:
        print(f"   ✗ 统计获取失败: {e}")

    # 8. 测试获取当前阶段允许的API
    print("\n5. 测试获取当前阶段允许的API:")
    try:
        allowed_apis = router.get_allowed_apis_for_current_phase()
        print(f"   ✓ handle_data 阶段允许 {len(allowed_apis)} 个API")
        print(f"   ✓ 包括: {', '.join(allowed_apis[:5])}...")
    except Exception as e:
        print(f"   ✗ 获取允许API失败: {e}")

    # 9. 测试无效阶段转换
    print("\n6. 测试无效生命周期阶段转换:")
    try:
        router.set_lifecycle_phase("invalid_phase")
        print("   ✗ 应该抛出异常但没有")
    except Exception as e:
        print(f"   ✓ 正确抛出异常: {type(e).__name__}")

    # 10. 测试状态重置
    print("\n7. 测试生命周期状态重置:")
    try:
        router.reset_lifecycle_state()
        current_phase = router.get_current_lifecycle_phase()
        print(f"   ✓ 重置后当前阶段: {current_phase}")

        stats = router.get_api_call_statistics()
        print(f"   ✓ 重置后调用统计: {stats['lifecycle_stats']['total_api_calls']} 次")
    except Exception as e:
        print(f"   ✗ 状态重置失败: {e}")

    print("\n=== 集成测试完成 ===")


@pytest.mark.integration
def demonstrate_lifecycle_validation():
    """演示生命周期验证的实际效果"""

    print("\n=== PTrade 生命周期验证演示 ===\n")

    # 创建控制器
    lifecycle_controller = LifecycleController("backtest")
    api_validator = APIValidator(lifecycle_controller)

    # 1. 演示初始化阶段的限制
    print("1. 演示初始化阶段 (initialize) 的API限制:")
    lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

    test_cases = [
        ("set_universe", [["000001.SZ", "000002.SZ"]]),  # 修正：传入列表
        ("set_commission", [0.0003]),
        ("order", ["000001.SZ", 100]),  # 应该失败
        ("get_price", ["000001.SZ"]),  # 应该成功
    ]

    for api_name, args in test_cases:
        try:
            result = api_validator.validate_api_call(api_name, *args)
            if result.is_valid:
                print(f"   ✓ {api_name}: 验证通过")
            else:
                print(f"   ✗ {api_name}: {result.error_message}")
        except Exception as e:
            print(f"   ✗ {api_name}: {e}")

    # 2. 演示交易阶段的限制
    print("\n2. 演示交易阶段 (handle_data) 的API限制:")
    lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    for api_name, args in test_cases:
        try:
            result = api_validator.validate_api_call(api_name, *args)
            if result.is_valid:
                print(f"   ✓ {api_name}: 验证通过")
            else:
                print(f"   ✗ {api_name}: {result.error_message}")
        except Exception as e:
            print(f"   ✗ {api_name}: {e}")

    # 3. 演示参数验证
    print("\n3. 演示API参数验证:")

    parameter_test_cases = [
        ("order", ["000001.SZ", 0]),  # amount不能为0
        ("order", ["", 100]),  # security不能为空
        ("order", ["000001.SZ", "abc"]),  # amount必须是整数
        ("set_commission", [-0.1]),  # commission不能为负
        ("set_commission", [2.0]),  # commission不应超过100%
    ]

    for api_name, args in parameter_test_cases:
        try:
            result = api_validator.validate_api_call(api_name, *args)
            if result.is_valid:
                print(f"   ✓ {api_name}{args}: 验证通过")
            else:
                print(f"   ✗ {api_name}{args}: {result.error_message}")
        except Exception as e:
            print(f"   ✗ {api_name}{args}: {e}")

    # 4. 展示调用统计
    print("\n4. API调用和验证统计:")
    lifecycle_stats = lifecycle_controller.get_call_statistics()
    validation_stats = api_validator.get_validation_statistics()

    print(f"   • 总API调用: {lifecycle_stats['total_api_calls']}")
    print(f"   • 失败调用: {lifecycle_stats['failed_calls']}")
    print(f"   • 成功率: {lifecycle_stats['success_rate']:.2%}")
    print(f"   • 总验证: {validation_stats['total_validations']}")
    print(f"   • 验证失败: {validation_stats['validation_failures']}")
    print(f"   • 验证成功率: {validation_stats['success_rate']:.2%}")

    print("\n=== 生命周期验证演示完成 ===")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)

    # 运行集成测试
    test_lifecycle_integration()

    # 运行验证演示
    demonstrate_lifecycle_validation()
