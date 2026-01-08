# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
通用策略参数优化框架 - 防过拟合增强版

关键改进:
1. Walk-Forward Analysis - 滚动窗口验证
2. 多时间段稳定性评估 - 参数鲁棒性检验
3. 正则化惩罚 - 避免参数极值
4. 样本外验证机制 - holdout set validation

使用方法:
1. 创建strategies/{strategy_name}/optimization/目录
2. 复制模板创建optimize_params.py
3. 修改ParameterSpace类中的参数空间定义
4. 修改ScoringStrategy类中的评分策略
5. 运行: poetry run python strategies/{strategy_name}/optimization/optimize_params.py
"""


from __future__ import annotations

import json
import optuna
import pickle
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Type
from tqdm import tqdm

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig


# ==================== 优化配置 ====================
DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2025-10-31"
DEFAULT_INITIAL_CAPITAL = 100000.0
DEFAULT_N_TRIALS = 50

# Walk-Forward配置
DEFAULT_TRAIN_MONTHS = 6
DEFAULT_TEST_MONTHS = 2
DEFAULT_STEP_MONTHS = 1

# 优化器配置
DEFAULT_REGULARIZATION_WEIGHT = 0.1
DEFAULT_STABILITY_WEIGHT = 0.5
DEFAULT_USE_OPTIMAL_STOPPING = True
DEFAULT_PATIENCE = 30

# 正则化配置
REGULARIZATION_BOUNDARY_THRESHOLD = 0.1  # 边界阈值10%
REGULARIZATION_PENALTY_MULTIPLIER = 10   # 惩罚倍数


# ==================== 参数空间基类 ====================
class ParameterSpace:
    """参数空间定义基类 - 支持类属性和方法两种定义方式"""

    @classmethod
    def get_parameter_choices(cls) -> dict[str, list[Any]]:
        """自动从类属性提取参数候选值（框架自动实现）

        返回所有非私有、非方法的类属性作为参数空间
        支持list、tuple、numpy.ndarray类型

        Returns:
            dict[str, list]: {'param_name': [choice1, choice2, ...]}
        """
        choices = {}
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            attr_value = getattr(cls, attr_name)
            # 跳过方法
            if callable(attr_value):
                continue
            # 支持list、tuple、numpy.ndarray
            if isinstance(attr_value, (list, tuple)):
                choices[attr_name] = list(attr_value)
            elif hasattr(attr_value, '__iter__') and hasattr(attr_value, 'tolist'):
                # numpy.ndarray
                choices[attr_name] = attr_value.tolist()
        return choices

    @classmethod
    def calculate_space_size(cls) -> int:
        """自动计算参数空间大小（框架实现，子类无需覆盖）

        Returns:
            int: 理论参数组合总数
        """
        choices = cls.get_parameter_choices()
        size = 1
        for param_choices in choices.values():
            size *= len(param_choices)
        return size

    @classmethod
    def suggest_parameters(cls, trial: optuna.Trial) -> dict[str, Any]:
        """基于get_parameter_choices自动生成参数（框架实现，子类无需覆盖）

        Args:
            trial: Optuna trial对象

        Returns:
            Dict[str, Any]: 参数字典
        """
        choices = cls.get_parameter_choices()
        return {
            param: trial.suggest_categorical(param, choices_list)
            for param, choices_list in choices.items()
        }

    @classmethod
    def get_extreme_params(cls) -> Dict[str, Tuple[Any, Any]]:
        """自动推导极端参数范围（框架实现，子类无需覆盖）

        设计理念：
        - 只对参数空间较大（>=5个候选值）的参数启用正则化
        - 小空间（<5个值）的离散候选应公平竞争，不应惩罚边界值
        - 避免人为限制参数搜索空间

        Returns:
            Dict[str, Tuple]: {param_name: (min_value, max_value)}
        """
        choices = cls.get_parameter_choices()
        extreme_params = {}
        for param, choices_list in choices.items():
            # 只对参数候选值>=5的参数启用正则化
            if len(choices_list) >= 5:
                extreme_params[param] = (min(choices_list), max(choices_list))
        return extreme_params

    @staticmethod
    def validate(params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数（可选，子类可覆盖）

        默认实现：不做任何验证，直接返回原参数

        如果需要验证，有两种方式：
        1. 返回修改后的参数（会导致optuna报错，不推荐）
        2. 检测到不合法参数时抛出ValueError，让optuna标记为FAIL

        Args:
            params: 参数字典

        Returns:
            Dict[str, Any]: 验证后的参数字典

        Raises:
            ValueError: 参数不合法时抛出

        Example:
            @staticmethod
            def validate(params):
                if params['ma_short'] >= params['ma_long']:
                    raise ValueError(f"ma_short={params['ma_short']} 必须小于 ma_long={params['ma_long']}")
                return params
        """
        return params


# ==================== 参数映射辅助函数 ====================

def resolve_variable_name(param_name: str, custom_mapping: Optional[Dict[str, str]] = None) -> str:
    """解析参数对应的策略变量名

    Args:
        param_name: 优化参数名
        custom_mapping: 自定义映射字典（可选），仅在参数名与变量名不一致时使用

    Returns:
        str: 策略中的变量名

    Example:
        # 默认自动映射
        resolve_variable_name('max_positions')  # -> 'g.max_positions'

        # 自定义映射
        custom = {'stop_loss': 'g.stop_loss_rate'}
        resolve_variable_name('stop_loss', custom)  # -> 'g.stop_loss_rate'
    """
    if custom_mapping and param_name in custom_mapping:
        return custom_mapping[param_name]
    return f'g.{param_name}'


def apply_parameter_replacement(
    original_code: str,
    params: Dict[str, Any],
    custom_mapping: Optional[Dict[str, str]] = None
) -> str:
    """统一的参数替换逻辑（消除代码重复）

    Args:
        original_code: 原始策略代码
        params: 参数字典
        custom_mapping: 自定义参数映射

    Returns:
        替换后的代码
    """
    import re

    modified_code = original_code

    for param_name, param_value in params.items():
        var_name = resolve_variable_name(param_name, custom_mapping)
        pattern = rf'(^\s*{re.escape(var_name)}\s*=\s*)[^#\n]+'

        # 根据值类型决定替换格式
        if isinstance(param_value, str):
            replacement = f"\\g<1>'{param_value}'"
        elif isinstance(param_value, bool):
            replacement = f"\\g<1>{param_value}"
        else:
            replacement = f"\\g<1>{param_value}"

        modified_code = re.sub(pattern, replacement, modified_code, flags=re.MULTILINE)

    return modified_code



# ==================== 评分策略基类 ====================
class ScoringStrategy:
    """评分策略基类"""

    @staticmethod
    def calculate_score(metrics: Dict[str, float]) -> float:
        """计算综合得分（提供默认实现，子类可选覆盖）

        默认策略（改进版，避免指标冗余）：
        - 夏普比率 40% - 风险调整后收益（已包含收益信息）
        - 最大回撤 30% - 回撤控制（量化策略核心指标）
        - 信息比率 20% - 相对基准超额收益
        - 胜率 10% - 交易质量（避免高频止损策略）

        设计理念：
        1. 移除annual_return（避免与sharpe_ratio冗余）
        2. 提高max_drawdown权重（回撤控制是量化策略生命线）
        3. 加入information_ratio（衡量相对市场的alpha能力）
        4. 加入win_rate（确保策略交易质量）

        Args:
            metrics: 回测指标字典

        Returns:
            float: 综合得分

        Example:
            # 使用默认评分
            class MyStrategy(ScoringStrategy):
                pass

            # 自定义评分
            class MyStrategy(ScoringStrategy):
                @staticmethod
                def calculate_score(metrics: Dict[str, float]) -> float:
                    return metrics['annual_return'] * 0.5 + metrics['sharpe_ratio'] * 0.5
        """
        score = (
            metrics.get('sharpe_ratio', 0.0) * 0.40 +        # 夏普比率 40%
            (-metrics.get('max_drawdown', 0.0)) * 0.30 +     # 最大回撤 30%
            metrics.get('information_ratio', 0.0) * 0.20 +   # 信息比率 20%
            metrics.get('win_rate', 0.0) * 0.10              # 胜率 10%
        )
        return score

    @staticmethod
    def get_tracked_metrics() -> List[str]:
        """获取需要跟踪的指标列表（可选）

        Returns:
            List[str]: 指标名称列表
        """
        return [
            'total_return', 'annual_return', 'sharpe_ratio',
            'max_drawdown', 'information_ratio', 'alpha',
            'beta', 'win_rate', 'profit_loss_ratio'
        ]

    @staticmethod
    def calculate_regularization_penalty(params: Dict[str, Any], extreme_params: Optional[Dict[str, Tuple[float, float]]] = None) -> float:
        """计算正则化惩罚（防止参数极值）

        Args:
            params: 参数字典
            extreme_params: 极端参数定义 {param_name: (min_extreme, max_extreme)}

        Returns:
            float: 惩罚值（0-1之间，越接近极端值惩罚越大）
        """
        if not extreme_params:
            return 0.0

        penalty = 0.0
        for param_name, (min_val, max_val) in extreme_params.items():
            if param_name not in params:
                continue

            value = params[param_name]
            range_size = max_val - min_val
            if range_size == 0:
                continue

            # 计算距离边界的归一化距离
            distance_to_min = abs(value - min_val) / range_size
            distance_to_max = abs(value - max_val) / range_size

            # 如果非常接近边界（<REGULARIZATION_BOUNDARY_THRESHOLD范围），增加惩罚
            if distance_to_min < REGULARIZATION_BOUNDARY_THRESHOLD:
                penalty += (REGULARIZATION_BOUNDARY_THRESHOLD - distance_to_min) * REGULARIZATION_PENALTY_MULTIPLIER
            if distance_to_max < REGULARIZATION_BOUNDARY_THRESHOLD:
                penalty += (REGULARIZATION_BOUNDARY_THRESHOLD - distance_to_max) * REGULARIZATION_PENALTY_MULTIPLIER

        return penalty


# ==================== 策略优化器（通用） ====================
class StrategyOptimizer:
    """通用策略参数优化器 - 防过拟合增强版"""

    def __init__(
        self,
        strategy_path: str,
        parameter_space: ParameterSpace,
        scoring_strategy: ScoringStrategy,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
        custom_mapping: Optional[Dict[str, str]] = None,
        use_walk_forward: bool = True,
        train_months: int = DEFAULT_TRAIN_MONTHS,
        test_months: int = DEFAULT_TEST_MONTHS,
        step_months: int = DEFAULT_STEP_MONTHS,
        regularization_weight: float = DEFAULT_REGULARIZATION_WEIGHT,
        stability_weight: float = DEFAULT_STABILITY_WEIGHT,
        use_optimal_stopping: bool = DEFAULT_USE_OPTIMAL_STOPPING,
        patience: int = DEFAULT_PATIENCE,
        verbose: bool = False,
    ):
        """初始化优化器

        Args:
            strategy_path: 策略文件路径
            parameter_space: 参数空间定义
            scoring_strategy: 评分策略
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_capital: 初始资金
            custom_mapping: 自定义参数映射（可选），仅在参数名与变量名不一致时使用
            use_walk_forward: 是否使用Walk-Forward分析（默认True）
            train_months: 训练窗口月数
            test_months: 测试窗口月数
            step_months: 滑动步长月数
            regularization_weight: 正则化权重
            stability_weight: 稳定性惩罚权重（默认0.5）
            use_optimal_stopping: 是否启用早停（默认True）
            patience: 无改进容忍次数，连续patience次trial无改进则停止（默认50）
            verbose: 是否输出详细调试信息（默认False）
        """
        self.strategy_path = Path(strategy_path)
        self.parameter_space = parameter_space
        self.scoring_strategy = scoring_strategy
        self.custom_mapping = custom_mapping or {}
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.use_walk_forward = use_walk_forward
        self.train_months = train_months
        self.test_months = test_months
        self.step_months = step_months

        # 自动从参数空间推导extreme_params
        self.extreme_params = parameter_space.get_extreme_params()
        self.regularization_weight = regularization_weight
        self.stability_weight = stability_weight

        self.use_optimal_stopping = use_optimal_stopping
        self.patience = patience
        self.verbose = verbose

        # 计算参数空间大小
        self.space_size = parameter_space.calculate_space_size()

        # 优化配置
        self.optimization_dir = self.strategy_path.parent / "optimization"
        self.results_dir = self.optimization_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 缓存目录
        self.cache_dir = self.results_dir / "backtest_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 创建共享的BacktestRunner实例（重用数据缓存）
        self._runner = None

        # 早停状态
        self._best_score = -float('inf')
        self._no_improvement_count = 0

        # 缓存Walk-Forward时间窗口（避免每个trial重复计算）
        self._cached_time_windows: Optional[List[Tuple[str, str, str, str]]] = None
        if self.use_walk_forward:
            self._cached_time_windows = self._generate_time_windows()

        # 缓存原始策略代码（避免重复读取文件）
        self._cached_strategy_code: Optional[str] = None

    @property
    def original_strategy_code(self) -> str:
        """获取原始策略代码（懒加载+缓存）"""
        if self._cached_strategy_code is None:
            with open(self.strategy_path, 'r', encoding='utf-8') as f:
                self._cached_strategy_code = f.read()
        return self._cached_strategy_code

    def create_strategy_code(self, params: Dict[str, Any]) -> str:
        """基于参数创建策略代码"""
        # 使用统一的参数替换函数（使用缓存的策略代码）
        return apply_parameter_replacement(self.original_strategy_code, params, self.custom_mapping)

    def run_backtest_with_params(self, params: Dict[str, Any], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[float, Dict[str, Any]]:
        """使用给定参数运行回测（支持缓存）"""
        import hashlib

        # 生成缓存key
        cache_key_str = f"{sorted(params.items())}_{start_date}_{end_date}"
        cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        # 尝试从缓存读取
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # 缓存损坏，删除并重新计算
                cache_file.unlink(missing_ok=True)

        # 执行回测
        result = self._run_backtest_impl(params, start_date, end_date)

        # 保存缓存
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception:
            pass  # 缓存失败不影响主流程

        return result

    def _run_backtest_impl(self, params: Dict[str, Any], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[float, Dict[str, Any]]:
        """实际执行回测的内部方法"""
        temp_strategy_dir = None
        try:
            # 创建临时策略
            from simtradelab.utils.paths import STRATEGIES_PATH
            import uuid
            temp_strategy_name = f"temp_strategy_{uuid.uuid4().hex[:8]}"
            temp_strategy_dir = Path(STRATEGIES_PATH) / temp_strategy_name
            temp_strategy_dir.mkdir(parents=True, exist_ok=True)
            temp_strategy_path = temp_strategy_dir / "backtest.py"

            # 生成策略代码
            strategy_code = self.create_strategy_code(params)
            with open(temp_strategy_path, 'w', encoding='utf-8') as f:
                f.write(strategy_code)

            # 静默执行回测
            from contextlib import redirect_stdout, redirect_stderr
            from io import StringIO

            # 首次创建或重用runner实例（数据缓存）
            if self._runner is None:
                self._runner = BacktestRunner()

            config = BacktestConfig(
                strategy_name=temp_strategy_name,
                start_date=start_date or self.start_date,
                end_date=end_date or self.end_date,
                initial_capital=self.initial_capital,
                enable_logging=False,
                enable_charts=False
            )

            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                report = self._runner.run(config=config)

            if not report:
                return -999.0, {}

            # 提取指标
            tracked_metrics = self.scoring_strategy.get_tracked_metrics()
            metrics = {
                metric: report.get(metric, 0.0 if 'rate' not in metric else -99.0)
                for metric in tracked_metrics
            }

            # 计算得分
            score = self.scoring_strategy.calculate_score(metrics)

            # 应用正则化惩罚
            if self.extreme_params and self.regularization_weight > 0:
                penalty = self.scoring_strategy.calculate_regularization_penalty(params, self.extreme_params)
                score -= penalty * self.regularization_weight

            return score, metrics

        except Exception as e:
            if self.verbose:
                tqdm.write(f"回测执行失败: {e}")  # type: ignore[attr-defined]
            return -999.0, {}
        finally:
            # 清理临时文件
            import shutil
            if temp_strategy_dir and temp_strategy_dir.exists():
                try:
                    shutil.rmtree(temp_strategy_dir)
                except Exception as cleanup_error:
                    if self.verbose:
                        tqdm.write(f"警告：临时目录清理失败 {temp_strategy_dir}: {cleanup_error}")  # type: ignore[attr-defined]

    def _generate_time_windows(self) -> list[tuple[str, str, str, str]]:
        """生成Walk-Forward时间窗口

        Returns:
            List[Tuple]: [(train_start, train_end, test_start, test_end), ...]
        """
        from dateutil.relativedelta import relativedelta

        start = datetime.strptime(self.start_date, '%Y-%m-%d')  # type: ignore[misc]
        end = datetime.strptime(self.end_date, '%Y-%m-%d')  # type: ignore[misc]

        windows = []
        current_start = start

        while True:
            # 训练窗口
            train_start = current_start
            train_end = train_start + relativedelta(months=self.train_months)

            # 测试窗口
            test_start = train_end
            test_end = test_start + relativedelta(months=self.test_months)

            # 如果测试窗口超出范围，停止
            if test_end > end:
                break

            windows.append((
                train_start.strftime('%Y-%m-%d'),
                train_end.strftime('%Y-%m-%d'),
                test_start.strftime('%Y-%m-%d'),
                test_end.strftime('%Y-%m-%d')
            ))

            # 滑动窗口
            current_start = current_start + relativedelta(months=self.step_months)

        return windows

    def objective(self, trial: optuna.Trial) -> float:
        """Optuna优化目标函数（支持Walk-Forward + 中间剪枝）"""
        # 生成参数
        params = self.parameter_space.suggest_parameters(trial)

        # 可选的参数验证（允许抛出异常标记trial为FAIL）
        try:
            params = self.parameter_space.validate(params)
        except ValueError as e:
            # 参数不合法，标记为失败
            trial.set_user_attr('validation_error', str(e))
            return -9999.0

        if self.use_walk_forward:
            # Walk-Forward分析（支持中间剪枝）
            # 使用缓存的时间窗口（避免重复计算）
            windows = self._cached_time_windows

            train_scores = []
            test_scores = []

            for step, (train_start, train_end, test_start, test_end) in enumerate(windows):
                # 训练期得分
                train_score, _ = self.run_backtest_with_params(
                    params, train_start, train_end
                )
                train_scores.append(train_score)

                # 测试期得分
                test_score, _ = self.run_backtest_with_params(
                    params, test_start, test_end
                )
                test_scores.append(test_score)

                # 关键：每个窗口后report中间结果，让Pruner决定是否剪枝
                # 改进：前3个窗口不剪枝，给参数足够观察时间（覆盖不同市场周期）
                if step >= 3:
                    # 使用当前的测试期平均得分作为中间值
                    intermediate_value = sum(test_scores) / len(test_scores)
                    trial.report(intermediate_value, step)

                    # Pruner判断：如果当前方向不promising，抛出异常提前终止
                    if trial.should_prune():
                        raise optuna.TrialPruned()

            # 使用测试期平均得分作为目标（防止过拟合）
            avg_test_score = sum(test_scores) / len(test_scores) if test_scores else -999.0
            avg_train_score = sum(train_scores) / len(train_scores) if train_scores else -999.0

            # 稳定性惩罚（训练/测试差异过大）
            test_std = np.std(test_scores) if len(test_scores) > 1 else 0.0
            stability_penalty = test_std * self.stability_weight

            # 记录指标
            trial.set_user_attr('avg_train_score', avg_train_score)
            trial.set_user_attr('avg_test_score', avg_test_score)
            trial.set_user_attr('test_score_std', test_std)
            trial.set_user_attr('train_test_gap', avg_train_score - avg_test_score)

            final_score = float(avg_test_score - stability_penalty)

        else:
            # 传统单一时间段优化
            final_score, metrics = self.run_backtest_with_params(params)

            # 记录指标
            for key, value in metrics.items():
                trial.set_user_attr(key, value)

        return final_score

    def optimize(self, resume: bool = True) -> optuna.Study:
        """执行智能参数优化（集成早停机制）

        Args:
            resume: 是否从上次中断处继续（默认 True）

        Returns:
            optuna.Study: 优化研究对象
        """
        # 计算n_trials
        if self.use_optimal_stopping:
            n_trials = self.space_size  # 最多跑完所有组合
        else:
            n_trials = DEFAULT_N_TRIALS  # 降级为默认值

        # 使用 SQLite 持久化存储
        storage_path = self.results_dir / "optuna_study.db"
        storage = f"sqlite:///{storage_path}"

        # 固定的 study 名称，用于断点续传
        study_name = f"{self.strategy_path.parent.name}_optimization"

        # 尝试加载或创建 study
        try:
            if resume:
                # 尝试加载已有的 study
                study = optuna.load_study(
                    study_name=study_name,
                    storage=storage
                )
                # 统计有效试验数（完成+剪枝）
                completed_trials = len([t for t in study.trials
                                       if t.state in [optuna.trial.TrialState.COMPLETE,
                                                     optuna.trial.TrialState.PRUNED]])
                print(f"\n发现已有优化进度: {completed_trials} 个已完成试验（含剪枝）")
                print(f"将继续优化至最多 {n_trials} 个试验...")

                # 恢复早停状态
                if self.use_optimal_stopping and study.best_trial:
                    self._best_score = study.best_value
                    # 计算无改进计数：从最佳trial之后有多少个完成的trial
                    best_trial_number = study.best_trial.number
                    self._no_improvement_count = len([
                        t for t in study.trials
                        if t.number > best_trial_number
                        and t.state == optuna.trial.TrialState.COMPLETE
                        and t.value is not None
                        and t.value <= self._best_score
                    ])
                    print(f"恢复早停状态: 最佳得分={self._best_score:.4f}, 无改进计数={self._no_improvement_count}/{self.patience}")

                # 计算还需要运行多少次
                remaining_trials = max(0, n_trials - completed_trials)
                if remaining_trials == 0:
                    print(f"已完成 {n_trials} 个试验，无需继续优化")
                    return study
            else:
                raise optuna.exceptions.DuplicatedStudyError  # 强制创建新 study

        except (optuna.exceptions.DuplicatedStudyError, KeyError):
            # 创建新的 study
            print(f"\n创建新的优化任务: {study_name}")

            # 使用更智能的采样器和剪枝器
            sampler = optuna.samplers.TPESampler(
                seed=42,
                n_startup_trials=10,  # 前10次随机探索
                multivariate=True,     # 考虑参数间相关性
                warn_independent_sampling=False
            )

            # 增强剪枝策略
            # MedianPruner: 如果中间结果低于历史中位数，剪枝
            pruner = optuna.pruners.MedianPruner(
                n_startup_trials=5,      # 前5个trial不剪枝（积累数据）
                n_warmup_steps=2,        # 每个trial前2个step不剪枝（观察趋势）
                interval_steps=1         # 每个step都检查是否剪枝
            )

            study = optuna.create_study(
                study_name=study_name,
                storage=storage,
                direction='maximize',
                sampler=sampler,
                pruner=pruner,
                load_if_exists=False
            )
            remaining_trials = n_trials

        # 静默模式
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        # 创建智能回调
        callbacks = []

        # 无改进早停回调
        if self.use_optimal_stopping:
            optimizer_self = self

            class EarlyStoppingCallback:
                def __call__(self, study, trial):
                    # 只处理完成的trial（跳过失败的，但包含剪枝的）
                    if trial.state == optuna.trial.TrialState.FAIL:
                        return

                    # 剪枝的trial视为无改进
                    if trial.state == optuna.trial.TrialState.PRUNED:
                        optimizer_self._no_improvement_count += 1
                        # 检查是否达到patience
                        if optimizer_self._no_improvement_count >= optimizer_self.patience:
                            tqdm.write(f"\n" + "="*60)  # type: ignore[attr-defined]
                            tqdm.write(f"早停触发！连续{optimizer_self.patience}次trial无改进（含剪枝）")  # type: ignore[attr-defined]
                            tqdm.write(f"最佳得分: {optimizer_self._best_score:.4f}")  # type: ignore[attr-defined]
                            tqdm.write("="*60)  # type: ignore[attr-defined]
                            study.stop()
                        return

                    # 检查是否有改进（只针对COMPLETE的trial）
                    if trial.value > optimizer_self._best_score:
                        # 有改进：更新最佳得分，重置计数器
                        improvement = trial.value - optimizer_self._best_score
                        optimizer_self._best_score = trial.value
                        optimizer_self._no_improvement_count = 0
                        tqdm.write(f"\n✓ 找到更优解: {trial.value:.4f} (改进 +{improvement:.4f})")  # type: ignore[attr-defined]
                        tqdm.write(f"  无改进计数器重置: 0/{optimizer_self.patience}")  # type: ignore[attr-defined]
                    else:
                        # 无改进：增加计数器
                        optimizer_self._no_improvement_count += 1
                        tqdm.write(f"  无改进 ({optimizer_self._no_improvement_count}/{optimizer_self.patience}): 当前={trial.value:.4f}, 最佳={optimizer_self._best_score:.4f}")  # type: ignore[attr-defined]

                        # 检查是否达到patience
                        if optimizer_self._no_improvement_count >= optimizer_self.patience:
                            tqdm.write(f"\n" + "="*60)  # type: ignore[attr-defined]
                            tqdm.write(f"早停触发！连续{optimizer_self.patience}次trial无改进")  # type: ignore[attr-defined]
                            tqdm.write(f"最佳得分: {optimizer_self._best_score:.4f}")  # type: ignore[attr-defined]
                            tqdm.write("="*60)  # type: ignore[attr-defined]
                            study.stop()

            callbacks.append(EarlyStoppingCallback())

        # 执行优化（单线程）
        print(f"\n开始智能优化，将运行最多 {remaining_trials} 个试验...")
        print(f"参数空间大小: {self.space_size} 种组合\n")

        # 使用手动进度条实现累积显示
        completed_before = n_trials - remaining_trials
        with tqdm(total=n_trials, initial=completed_before, desc="总优化进度") as pbar:
            def update_progress(study, trial):
                pbar.update(1)

            # 将进度条更新回调加入callbacks
            progress_callbacks = callbacks + [update_progress]

            study.optimize(
                self.objective,
                n_trials=remaining_trials,
                n_jobs=1,
                callbacks=progress_callbacks,
                show_progress_bar=False  # 禁用optuna内置进度条
            )

        # 保存结果
        self.save_optimization_results(study)

        return study

    def validate_on_holdout(self, best_params: Dict[str, Any], holdout_start: str, holdout_end: str) -> Dict[str, float]:
        """在留存集上验证最佳参数

        Args:
            best_params: 最佳参数
            holdout_start: 留存集开始日期
            holdout_end: 留存集结束日期

        Returns:
            Dict[str, float]: 留存集指标
        """
        print(f"\n样本外验证: {holdout_start} 至 {holdout_end}")
        score, metrics = self.run_backtest_with_params(best_params, holdout_start, holdout_end)
        print(f"样本外得分: {score:.4f}")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")
        return metrics

    def save_optimization_results(self, study: optuna.Study):
        """保存优化结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # type: ignore[misc]

        # 保存最佳参数
        best_params_file = self.results_dir / f"best_params_{timestamp}.json"
        with open(best_params_file, 'w', encoding='utf-8') as f:
            json.dump(study.best_params, f, indent=2, ensure_ascii=False)

        # 保存详细结果
        trials_df = study.trials_dataframe()
        trials_file = self.results_dir / f"trials_{timestamp}.csv"
        trials_df.to_csv(trials_file, index=False, encoding='utf-8')

        # 保存study对象
        study_file = self.results_dir / f"study_{timestamp}.pkl"
        with open(study_file, 'wb') as f:
            pickle.dump(study, f)

        # 生成可视化
        self._generate_plots(study, timestamp)

        # 输出性能评分报告（类似机器学习）
        self._print_performance_report(study)

        print(f"\n结果保存到: {self.results_dir}")

    def _print_performance_report(self, study: optuna.Study):
        """输出性能评分报告（类似机器学习格式）"""
        print("\n" + "=" * 70)
        print("优化性能报告")
        print("=" * 70)

        # 基本信息
        completed_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        pruned_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])
        failed_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.FAIL])

        print(f"\n【优化统计】")
        print(f"  总试验次数: {len(study.trials)}")
        print(f"  完成试验数: {completed_trials}")
        print(f"  剪枝试验数: {pruned_trials} (提前终止低效参数方向)")
        print(f"  失败试验数: {failed_trials}")

        # 检查是否有成功完成的trial
        if completed_trials == 0:
            print("\n警告: 没有成功完成的试验，无法生成最佳参数报告")
            print("建议检查:")
            print("  - 参数空间设置是否合理")
            print("  - 策略代码是否存在错误")
            print("  - 回测时间窗口是否合适")
            return

        print(f"  最佳试验ID: {study.best_trial.number}")

        if len(study.trials) > 0:
            efficiency = (completed_trials + pruned_trials) / len(study.trials) * 100
            prune_ratio = pruned_trials / len(study.trials) * 100
            print(f"  优化效率:   {efficiency:.1f}% (完成+剪枝)")
            print(f"  剪枝率:     {prune_ratio:.1f}% (节省算力)")

        # 最佳参数
        print(f"\n【最佳参数】")
        for param, value in study.best_params.items():
            if isinstance(value, float):
                print(f"  {param:20s}: {value:.4f}")
            else:
                print(f"  {param:20s}: {value}")

        # 性能得分
        print(f"\n【性能得分】")
        print(f"  综合得分: {study.best_value:.4f}")

        if self.use_walk_forward and study.best_trial.user_attrs:
            # Walk-Forward详细统计
            train_score = study.best_trial.user_attrs.get('avg_train_score', 0)
            test_score = study.best_trial.user_attrs.get('avg_test_score', 0)
            test_std = study.best_trial.user_attrs.get('test_score_std', 0)
            gap = study.best_trial.user_attrs.get('train_test_gap', 0)

            print(f"\n  训练期得分:      {train_score:8.4f}")
            print(f"  测试期得分:      {test_score:8.4f}")
            print(f"  测试期标准差:    {test_std:8.4f}")
            print(f"  训练/测试差距:   {gap:8.4f}")

            # 过拟合判断
            overfitting_ratio = abs(gap) / max(abs(train_score), 0.0001)
            print(f"  过拟合比率:      {overfitting_ratio:8.2%}")

            if overfitting_ratio < 0.05:
                status = "✓ 良好"
            elif overfitting_ratio < 0.15:
                status = "⚠ 轻微过拟合"
            else:
                status = "✗ 过拟合风险"
            print(f"  泛化能力:        {status}")

        # 详细指标（如果有）
        if study.best_trial.user_attrs:
            # 提取所有量化指标
            metrics = {k: v for k, v in study.best_trial.user_attrs.items()
                      if k not in ['avg_train_score', 'avg_test_score', 'test_score_std', 'train_test_gap']}

            if metrics:
                print(f"\n【回测指标】")
                for metric, value in sorted(metrics.items()):
                    if isinstance(value, (int, float)):
                        # 特殊格式化
                        if 'ratio' in metric.lower() or 'rate' in metric.lower():
                            print(f"  {metric:20s}: {value:8.4f}")
                        elif 'return' in metric.lower() or 'drawdown' in metric.lower():
                            print(f"  {metric:20s}: {value:8.2%}")
                        else:
                            print(f"  {metric:20s}: {value:8.4f}")

        print("=" * 70)

    def _generate_plots(self, study: optuna.Study, timestamp: str):
        """生成可视化图表"""
        try:
            import optuna.visualization as vis
            plots_dir = self.results_dir / "plots"
            plots_dir.mkdir(exist_ok=True)

            plots = [
                ('optimization_history', vis.plot_optimization_history),
                ('param_importances', vis.plot_param_importances),
                ('parallel_coordinate', vis.plot_parallel_coordinate),
                ('slice', vis.plot_slice),
            ]

            for name, plot_func in plots:
                try:
                    fig = plot_func(study)
                    fig.write_html(str(plots_dir / f"{name}_{timestamp}.html"))
                    print(f"  生成{name}图")
                except Exception as e:
                    print(f"  跳过{name}图: {e}")

            print(f"  可视化图表保存到: {plots_dir}")

        except ImportError:
            print("  警告: 未安装plotly，跳过可视化")


def create_optimized_strategy(
    best_params_file: str,
    original_strategy_path: str,
    output_path: str,
    custom_mapping: Optional[Dict[str, str]] = None
):
    """基于最佳参数创建优化后的策略文件"""
    # 读取最佳参数
    with open(best_params_file, 'r', encoding='utf-8') as f:
        best_params = json.load(f)

    # 读取原始策略
    with open(original_strategy_path, 'r', encoding='utf-8') as f:
        original_code = f.read()

    # 使用统一的参数替换函数
    modified_code = apply_parameter_replacement(original_code, best_params, custom_mapping)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(modified_code)

    print(f"优化后的策略已保存到: {output_path}")


# ==================== 简化的顶层API ====================
def optimize_strategy(
    parameter_space: type,
    optimization_period: Optional[Tuple[str, str]] = None,
    holdout_period: Optional[Tuple[str, str]] = None,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
    scoring_strategy: Optional[Type[ScoringStrategy]] = None,
    walk_forward_config: Optional[Dict[str, int]] = None,
    use_optimal_stopping: bool = DEFAULT_USE_OPTIMAL_STOPPING,
    patience: Optional[int] = None,
    regularization_weight: float = DEFAULT_REGULARIZATION_WEIGHT,
    stability_weight: float = DEFAULT_STABILITY_WEIGHT,
    custom_mapping: Optional[Dict[str, str]] = None,
    resume: bool = True,
    verbose: bool = False
):
    """一站式策略参数优化入口函数

    Args:
        parameter_space: 参数空间类（继承ParameterSpace）
        optimization_period: 优化时间段 (start_date, end_date)，默认("2019-01-01", "2024-12-31")
        holdout_period: 泛化测试时间段 (start_date, end_date)，默认("2025-01-01", "2025-10-25")
        initial_capital: 初始资金，默认100000.0
        scoring_strategy: 评分策略类，默认ScoringStrategy
        walk_forward_config: Walk-Forward配置 {'train_months': 12, 'test_months': 3, 'step_months': 6}
        use_optimal_stopping: 是否启用早停，默认True
        patience: 无改进容忍次数，None时自动设为参数空间的1/4
        regularization_weight: 正则化权重，默认0.1
        stability_weight: 稳定性惩罚权重，默认0.5
        custom_mapping: 自定义参数映射
        resume: 是否断点续传，默认True
        verbose: 是否输出详细调试信息，默认False

    Example:
        class MACrossParams(ParameterSpace):
            ma_short = [5, 10, 12]
            ma_long = [20, 30, 60]

            @staticmethod
            def validate(params):
                # 检测不合法参数，抛出异常让optuna标记为FAIL
                if params['ma_short'] >= params['ma_long']:
                    raise ValueError("ma_short必须小于ma_long")
                return params

        optimize_strategy(
            parameter_space=MACrossParams,
            optimization_period=("2019-01-01", "2024-12-31"),
            holdout_period=("2025-01-01", "2025-10-25")
        )
    """
    import inspect

    # 自动推断strategy_path（从调用文件路径推断）
    caller_frame = inspect.stack()[1]
    caller_filepath = Path(caller_frame.filename)

    # 假设调用者在 strategies/{name}/optimization/optimize_params.py
    strategy_path = caller_filepath.parent.parent / "backtest.py"
    if not strategy_path.exists():
        raise FileNotFoundError(
            f"无法自动推断策略路径，期望位置: {strategy_path}\n"
            f"请确保目录结构为: strategies/{{name}}/optimization/optimize_params.py"
        )

    # 默认参数
    if optimization_period is None:
        optimization_period = ("2019-01-01", "2024-12-31")
    if holdout_period is None:
        holdout_period = ("2025-01-01", "2025-10-25")
    if scoring_strategy is None:
        scoring_instance = ScoringStrategy()
    else:
        scoring_instance = scoring_strategy()
    if walk_forward_config is None:
        walk_forward_config = {
            'train_months': 12,
            'test_months': 3,
            'step_months': 6
        }

    start_date, end_date = optimization_period
    holdout_start, holdout_end = holdout_period

    # 创建参数空间实例
    param_space = parameter_space()

    # 动态计算patience（如果未指定）
    space_size = parameter_space.calculate_space_size()
    if patience is None:
        patience = int(space_size / 4)

    # 输出配置信息
    print("=" * 70)
    print(f"{strategy_path.parent.name} 策略 - 防过拟合参数优化 (早停机制)")
    print("=" * 70)
    print(f"\n【时间划分】")
    print(f"  优化期: {start_date} ~ {end_date}")
    print(f"  泛化测试集: {holdout_start} ~ {holdout_end}")
    print(f"  Walk-Forward: {walk_forward_config['train_months']}月训练 + {walk_forward_config['test_months']}月测试, 步长{walk_forward_config['step_months']}月")
    print(f"\n【参数空间】")
    print(f"  总组合数: {space_size} 种")
    print("\n【优化策略】")
    print("  ✓ Walk-Forward Analysis - 滚动窗口验证，使用测试期得分")
    print("  ✓ TPE贝叶斯优化 - 考虑参数间相关性")
    print("  ✓ MedianPruner中间剪枝 - 快速淘汰低效参数方向")
    print("  ✓ 稳定性约束 - 惩罚测试期得分波动大的参数")
    print("  ✓ 正则化惩罚 - 自动推导参数极值边界")
    if use_optimal_stopping:
        print(f"  ✓ 早停机制 - 连续{patience}次trial无改进则停止（空间的1/4向上取整）\n")
    else:
        print()

    # 创建优化器
    optimizer = StrategyOptimizer(
        strategy_path=str(strategy_path),
        parameter_space=param_space,
        scoring_strategy=scoring_instance,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        custom_mapping=custom_mapping,
        use_walk_forward=True,
        train_months=walk_forward_config['train_months'],
        test_months=walk_forward_config['test_months'],
        step_months=walk_forward_config['step_months'],
        use_optimal_stopping=use_optimal_stopping,
        patience=patience,
        regularization_weight=regularization_weight,
        stability_weight=stability_weight,
        verbose=verbose
    )

    # 执行优化
    study = optimizer.optimize(resume=resume)

    # 泛化测试
    print("\n" + "=" * 70)
    print(f"泛化测试 - 使用完全未参与优化的{holdout_start[:4]}年数据")
    print("=" * 70)
    _ = optimizer.validate_on_holdout(
        best_params=study.best_params,
        holdout_start=holdout_start,
        holdout_end=holdout_end
    )

    # 创建优化后的策略
    latest_best_params = max(
        optimizer.results_dir.glob("best_params_*.json"),
        key=lambda x: x.stat().st_mtime
    )

    optimized_strategy_path = optimizer.optimization_dir / "optimized_strategy.py"
    create_optimized_strategy(
        best_params_file=str(latest_best_params),
        original_strategy_path=str(strategy_path),
        output_path=str(optimized_strategy_path),
        custom_mapping=custom_mapping
    )

    print("\n" + "=" * 70)
    print("优化完成！")
    print("=" * 70)
    print(f"结果目录: {optimizer.results_dir}")
    print(f"优化策略: {optimized_strategy_path}")
    print(f"数据库: {optimizer.results_dir / 'optuna_study.db'}")
    print("\n提示:")
    print("  - 查看 plots/ 目录获取可视化分析")
    print("  - 对比训练/测试差距判断是否过拟合")
    print("  - 样本外验证指标应接近测试期平均水平")

    return study
