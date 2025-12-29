# -*- coding: utf-8 -*-
"""
5mv策略参数优化器
"""

from simtradelab.backtest.optimizer_framework import (
    ParameterSpace,
    optimize_strategy,
)


# ==================== 参数空间定义 ====================
class FiveMVParameterSpace(ParameterSpace):
    """5mv策略参数空间

    使用类属性定义参数候选值（框架自动推导）
    """

    # 参数候选值定义
    max_position = [1, 2, 3, 4, 5]
    rotation_period = list(range(1, 201, 1))  # [1, 6, 11, ..., 196]

    @staticmethod
    def validate(params):
        """验证参数（可选）"""
        # 持仓数量不能超过股票池大小
        if params['max_position'] > 5:
            raise ValueError("max_position={} 不能超过5".format(params['max_position']))
        return params

# ==================== 主函数 ====================

if __name__ == "__main__":
    # 自定义参数映射（5mv使用context而非g）
    custom_mapping = {
        'max_position': 'context.max_position',
        'rotation_period': 'context.rotation_period',
    }

    # 根据实际数据范围调整时间段（数据范围：2025-01-02 到 2025-10-31）
    # 优化期使用前8个月，留存期使用后2个月
    optimize_strategy(
        parameter_space=FiveMVParameterSpace,
        optimization_period=("2025-01-02", "2025-08-31"),  # 8个月优化期
        holdout_period=("2025-09-01", "2025-10-31"),       # 2个月留存期
        regularization_weight=0.5,
        stability_weight=0.5,
        custom_mapping=custom_mapping,
        walk_forward_config={
            'train_months': 3,   # 3月训练期
            'test_months': 1,    # 1月测试期
            'step_months': 1     # 1月步长
        }
    )
