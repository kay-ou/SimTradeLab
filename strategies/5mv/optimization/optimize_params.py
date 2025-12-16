# -*- coding: utf-8 -*-
"""
5mv策略参数优化器
"""

from pathlib import Path

from simtradelab.backtest.optimizer_framework import (
    BaseParameterSpace,
    BaseScoringStrategy,
    StrategyOptimizer,
)


# ==================== 参数空间定义 ====================
class FiveMVParameterSpace(BaseParameterSpace):
    """5mv策略参数空间"""

    @staticmethod
    def suggest_parameters(trial):
        """建议参数值"""
        return {
            'max_position': trial.suggest_int('max_position', 1, 5),
            'rotation_period': trial.suggest_int('rotation_period', 1, 200),
        }

    @staticmethod
    def validate_parameters(params):
        """验证参数"""
        # 持仓数量不能超过股票池大小
        if params['max_position'] > 5:
            params['max_position'] = 5
        return params


# ==================== 评分策略 ====================
class FiveMVScoringStrategy(BaseScoringStrategy):
    """5mv策略评分策略"""

    @staticmethod
    def calculate_score(metrics):
        """计算综合得分

        评分公式：年化收益率40% + 夏普比率30% + 最大回撤30%
        """
        return (
            metrics.get('annual_return', 0.0) * 0.4 +
            metrics.get('sharpe_ratio', 0.0) * 0.3 +
            (-metrics.get('max_drawdown', 0.0)) * 0.3
        )


# ==================== 主函数 ====================
def main():
    """执行优化"""
    # 策略路径
    strategy_path = Path(__file__).parent.parent / "backtest.py"

    # 自定义参数映射（5mv使用context而非g）
    custom_mapping = {
        'max_position': 'context.max_position',
        'rotation_period': 'context.rotation_period',
    }

    # 创建优化器
    optimizer = StrategyOptimizer(
        strategy_path=str(strategy_path),
        parameter_space=FiveMVParameterSpace(),
        scoring_strategy=FiveMVScoringStrategy(),
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_capital=100000.0,
        custom_mapping=custom_mapping,
    )

    # 执行优化
    study = optimizer.optimize(
        n_trials=100,
        resume=True,
        early_stopping_rounds=20
    )

    # 输出最佳参数详细信息
    print("\n" + "="*60)
    print("最佳参数详细信息:")
    print("="*60)
    for key, value in study.best_params.items():
        print("%s: %s" % (key, value))

    print("\n最佳指标:")
    best_trial = study.best_trial
    for key, value in best_trial.user_attrs.items():
        print("%s: %.4f" % (key, value))


if __name__ == "__main__":
    main()
