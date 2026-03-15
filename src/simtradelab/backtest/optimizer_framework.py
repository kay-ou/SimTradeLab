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

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig
from simtradelab.i18n import t


class _NoFileLock:
    """No-op file lock — safe when n_jobs=1 and only one optimizer runs at a time.

    Must be at module level (not a local class) so it can be pickled by Optuna's
    JournalStorage internals.
    """
    def acquire(self) -> bool:
        return True

    def release(self) -> None:
        pass


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
            dict[str, Any]: 参数字典
        """
        choices = cls.get_parameter_choices()
        return {
            param: trial.suggest_categorical(param, choices_list)
            for param, choices_list in choices.items()
        }

    @classmethod
    def get_extreme_params(cls) -> dict[str, tuple[Any, Any]]:
        """自动推导极端参数范围（框架实现，子类无需覆盖）

        设计理念：
        - 只对参数空间较大（>=5个候选值）的参数启用正则化
        - 小空间（<5个值）的离散候选应公平竞争，不应惩罚边界值
        - 避免人为限制参数搜索空间

        Returns:
            dict[str, tuple]: {param_name: (min_value, max_value)}
        """
        choices = cls.get_parameter_choices()
        extreme_params = {}
        for param, choices_list in choices.items():
            # 只对参数候选值>=5的参数启用正则化
            if len(choices_list) >= 5:
                extreme_params[param] = (min(choices_list), max(choices_list))
        return extreme_params

    @staticmethod
    def validate(params: dict[str, Any]) -> dict[str, Any]:
        """验证参数（可选，子类可覆盖）

        默认实现：不做任何验证，直接返回原参数

        如果需要验证，有两种方式：
        1. 返回修改后的参数（会导致optuna报错，不推荐）
        2. 检测到不合法参数时抛出ValueError，让optuna标记为FAIL

        Args:
            params: 参数字典

        Returns:
            dict[str, Any]: 验证后的参数字典

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

def resolve_variable_name(param_name: str, custom_mapping: Optional[dict[str, str]] = None) -> str:
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
    params: dict[str, Any],
    custom_mapping: Optional[dict[str, str]] = None
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
    def calculate_score(metrics: dict[str, float]) -> float:
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
                def calculate_score(metrics: dict[str, float]) -> float:
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
    def get_tracked_metrics() -> list[str]:
        """获取需要跟踪的指标列表（可选）

        Returns:
            list[str]: 指标名称列表
        """
        return [
            'total_return', 'annual_return', 'sharpe_ratio',
            'max_drawdown', 'information_ratio', 'alpha',
            'beta', 'win_rate', 'profit_loss_ratio'
        ]

    @staticmethod
    def calculate_regularization_penalty(params: dict[str, Any], extreme_params: Optional[dict[str, tuple[float, float]]] = None) -> float:
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
        custom_mapping: Optional[dict[str, str]] = None,
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
        self._cached_time_windows: Optional[list[tuple[str, str, str, str]]] = None
        if self.use_walk_forward:
            self._cached_time_windows = self._generate_time_windows()

        # 缓存原始策略代码（避免重复读取文件）
        self._cached_strategy_code: Optional[str] = None

        # 临时策略目录（跨 trial 复用，优化结束后统一清理）
        self._temp_strategy_dir: Optional[Path] = None
        self._temp_strategy_name: Optional[str] = None

    @property
    def original_strategy_code(self) -> str:
        """获取原始策略代码（懒加载+缓存）"""
        if self._cached_strategy_code is None:
            with open(self.strategy_path, 'r', encoding='utf-8') as f:
                self._cached_strategy_code = f.read()
        return self._cached_strategy_code

    def create_strategy_code(self, params: dict[str, Any]) -> str:
        """基于参数创建策略代码"""
        # 使用统一的参数替换函数（使用缓存的策略代码）
        return apply_parameter_replacement(self.original_strategy_code, params, self.custom_mapping)

    def run_backtest_with_params(self, params: dict[str, Any], start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[float, dict[str, Any]]:
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

    def _run_backtest_impl(self, params: dict[str, Any], start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[float, dict[str, Any]]:
        """实际执行回测的内部方法"""
        try:
            # 复用临时策略目录（首次创建后跨 trial 复用）
            if self._temp_strategy_dir is None:
                from simtradelab.utils.paths import STRATEGIES_PATH
                import uuid
                self._temp_strategy_name = f"temp_strategy_{uuid.uuid4().hex[:8]}"
                self._temp_strategy_dir = Path(STRATEGIES_PATH) / self._temp_strategy_name
                self._temp_strategy_dir.mkdir(parents=True, exist_ok=True)

            temp_strategy_path = self._temp_strategy_dir / "backtest.py"

            # 生成策略代码（覆盖写入）
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
                strategy_name=self._temp_strategy_name,
                start_date=start_date or self.start_date,
                end_date=end_date or self.end_date,
                initial_capital=self.initial_capital,
                enable_logging=False,
                enable_charts=False,
                optimization_mode=True
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
                print(t("opt.bt_failed", error=e), flush=True)
            return -999.0, {}

    def _generate_time_windows(self) -> list[tuple[str, str, str, str]]:
        """生成Walk-Forward时间窗口

        Returns:
            list[tuple]: [(train_start, train_end, test_start, test_end), ...]
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

        # 使用 JournalStorage（纯文件存储，不依赖 Alembic/SQLite）
        # 使用 no-op lock：优化器单线程运行 (n_jobs=1)，同时只有一个优化任务，
        # 不存在并发访问，无需文件锁。使用 JournalFileOpenLock 会导致第二次运行
        # 时因前一次的锁对象未被 GC 而陷入 while not acquire(): sleep(0.1) 死循环。
        from optuna.storages.journal import JournalFileBackend

        journal_path = self.results_dir / "optuna_journal.log"
        storage = optuna.storages.JournalStorage(
            JournalFileBackend(str(journal_path), lock_obj=_NoFileLock())  # type: ignore[arg-type]
        )

        # 固定的 study 名称，用于断点续传
        study_name = f"{self.strategy_path.parent.name}_optimization"

        # 尝试加载或创建 study
        existing_studies = optuna.get_all_study_names(storage=storage)
        if resume and study_name in existing_studies:
            study = optuna.load_study(study_name=study_name, storage=storage)
            # 统计有效试验数（完成+剪枝）
            completed_trials = len([t for t in study.trials
                                   if t.state in [optuna.trial.TrialState.COMPLETE,
                                                 optuna.trial.TrialState.PRUNED]])
            print(t("opt.resume_found", count=completed_trials))
            print(t("opt.resume_continue", count=n_trials))

            # 恢复早停状态（仅当有已完成试验时）
            if self.use_optimal_stopping and completed_trials > 0:
                try:
                    self._best_score = study.best_value
                    best_trial_number = study.best_trial.number
                    self._no_improvement_count = len([
                        t for t in study.trials
                        if t.number > best_trial_number
                        and t.state == optuna.trial.TrialState.COMPLETE
                        and t.value is not None
                        and t.value <= self._best_score
                    ])
                    print(t("opt.resume_state", score="{:.4f}".format(self._best_score), count=self._no_improvement_count, patience=self.patience))
                except (ValueError, KeyError):
                    pass  # 无有效最优试验，从头开始早停计数

            # 计算还需要运行多少次
            remaining_trials = max(0, n_trials - completed_trials)
            if remaining_trials == 0:
                print(t("opt.all_done", count=n_trials))
                return study
        else:
            # 创建新的 study
            print(t("opt.new_study", name=study_name))

            sampler = optuna.samplers.TPESampler(
                seed=42,
                n_startup_trials=10,  # 前10次随机探索
                multivariate=True,     # 考虑参数间相关性
                warn_independent_sampling=False
            )
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
                load_if_exists=True
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
                            print(f"\n" + "="*60, flush=True)
                            print(t("opt.early_stop_pruned", patience=optimizer_self.patience), flush=True)
                            print(t("opt.best_score", score="{:.4f}".format(optimizer_self._best_score)), flush=True)
                            print("="*60, flush=True)
                            study.stop()
                        return

                    # 检查是否有改进（只针对COMPLETE的trial）
                    if trial.value > optimizer_self._best_score:
                        # 有改进：更新最佳得分，重置计数器
                        improvement = trial.value - optimizer_self._best_score
                        optimizer_self._best_score = trial.value
                        optimizer_self._no_improvement_count = 0
                        print(t("opt.better_found", value="{:.4f}".format(trial.value), improvement="{:.4f}".format(improvement)), flush=True)
                        print(t("opt.counter_reset", patience=optimizer_self.patience), flush=True)
                    else:
                        # 无改进：增加计数器
                        optimizer_self._no_improvement_count += 1
                        print(t("opt.no_improvement", count=optimizer_self._no_improvement_count, patience=optimizer_self.patience, current="{:.4f}".format(trial.value), best="{:.4f}".format(optimizer_self._best_score)), flush=True)

                        # 检查是否达到patience
                        if optimizer_self._no_improvement_count >= optimizer_self.patience:
                            print(f"\n" + "="*60, flush=True)
                            print(t("opt.early_stop", patience=optimizer_self.patience), flush=True)
                            print(t("opt.best_score", score="{:.4f}".format(optimizer_self._best_score)), flush=True)
                            print("="*60, flush=True)
                            study.stop()

            callbacks.append(EarlyStoppingCallback())

        # 执行优化（单线程）
        print(t("opt.starting", count=remaining_trials))
        print(t("opt.space_size", size=self.space_size))

        completed_before = n_trials - remaining_trials
        _done = [completed_before]  # mutable int for closure

        # Emit initial progress so the UI can show total immediately
        print(f"__PROGRESS__:{_done[0]}/{n_trials}", flush=True)

        def update_progress(_study, _trial):
            _done[0] += 1
            print(f"__PROGRESS__:{_done[0]}/{n_trials}", flush=True)

        study.optimize(
            self.objective,
            n_trials=remaining_trials,
            n_jobs=1,
            callbacks=callbacks + [update_progress],
            show_progress_bar=False,
        )

        # 保存结果
        self.save_optimization_results(study)

        # 清理临时策略目录
        self._cleanup_temp_strategy()

        return study

    def _cleanup_temp_strategy(self):
        """清理临时策略目录"""
        if self._temp_strategy_dir and self._temp_strategy_dir.exists():
            import shutil
            try:
                shutil.rmtree(self._temp_strategy_dir)
            except Exception:
                pass
            self._temp_strategy_dir = None
            self._temp_strategy_name = None

    def validate_on_holdout(self, best_params: dict[str, Any], holdout_start: str, holdout_end: str) -> dict[str, float]:
        """在留存集上验证最佳参数

        Args:
            best_params: 最佳参数
            holdout_start: 留存集开始日期
            holdout_end: 留存集结束日期

        Returns:
            dict[str, float]: 留存集指标
        """
        print(t("opt.holdout_title", start=holdout_start, end=holdout_end))
        score, metrics = self.run_backtest_with_params(best_params, holdout_start, holdout_end)
        print(t("opt.holdout_score", score="{:.4f}".format(score)))
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

        # 不保存 study.pkl（optuna_journal.log 已含断点续传所需数据，pkl 为冗余）

        # 输出性能评分报告
        self._print_performance_report(study)

    def _print_performance_report(self, study: optuna.Study):
        """输出性能评分报告"""
        completed_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        pruned_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED])
        failed_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.FAIL])

        print(t("opt.stats_title"))
        print(t("opt.stats_total", count=len(study.trials)))
        print(t("opt.stats_completed", count=completed_trials))
        print(t("opt.stats_pruned", count=pruned_trials))
        print(t("opt.stats_failed", count=failed_trials))

        if completed_trials == 0:
            print(t("opt.no_completed"))
            return

        print(t("opt.best_trial_id", id=study.best_trial.number))

        print(t("opt.best_params_title"))
        for param, value in study.best_params.items():
            if isinstance(value, float):
                print(f"  {param}: {value:.4f}")
            else:
                print(f"  {param}: {value}")

        print(t("opt.perf_title"))
        print(t("opt.combined_score", score="{:.4f}".format(study.best_value)))

        if self.use_walk_forward and study.best_trial.user_attrs:
            train_score = study.best_trial.user_attrs.get('avg_train_score', 0)
            test_score = study.best_trial.user_attrs.get('avg_test_score', 0)
            test_std = study.best_trial.user_attrs.get('test_score_std', 0)
            gap = study.best_trial.user_attrs.get('train_test_gap', 0)
            overfitting_ratio = abs(gap) / max(abs(train_score), 0.0001)

            print(t("opt.train_score", score="{:.4f}".format(train_score)))
            print(t("opt.test_score", score="{:.4f}".format(test_score)))
            print(t("opt.test_std", value="{:.4f}".format(test_std)))
            print(t("opt.train_test_gap", value="{:.4f}".format(gap)))
            print(t("opt.overfit_ratio", value="{:.2%}".format(overfitting_ratio)))


def create_optimized_strategy(
    best_params_file: str,
    original_strategy_path: str,
    output_path: str,
    custom_mapping: Optional[dict[str, str]] = None
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

    print(t("opt.strategy_saved", path=output_path))


# ==================== 简化的顶层API ====================
def optimize_strategy(
    parameter_space: type,
    optimization_period: Optional[tuple[str, str]] = None,
    holdout_period: Optional[tuple[str, str]] = None,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
    scoring_strategy: Optional[Type[ScoringStrategy]] = None,
    walk_forward_config: Optional[dict[str, int]] = None,
    use_optimal_stopping: bool = DEFAULT_USE_OPTIMAL_STOPPING,
    patience: Optional[int] = None,
    regularization_weight: float = DEFAULT_REGULARIZATION_WEIGHT,
    stability_weight: float = DEFAULT_STABILITY_WEIGHT,
    custom_mapping: Optional[dict[str, str]] = None,
    resume: bool = True,
    verbose: bool = False,
    _script_path: Optional[str] = None,
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
    if _script_path is not None:
        script_filepath = Path(_script_path)
    else:
        import inspect
        caller_frame = inspect.stack()[1]
        script_filepath = Path(caller_frame.filename)

    # 假设脚本在 strategies/{name}/optimization/optimize_params.py
    strategy_path = script_filepath.parent.parent / "backtest.py"
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
        opt_start = datetime.strptime(optimization_period[0], "%Y-%m-%d")
        opt_end = datetime.strptime(optimization_period[1], "%Y-%m-%d")
        hld_start = datetime.strptime(holdout_period[0], "%Y-%m-%d")
        hld_end = datetime.strptime(holdout_period[1], "%Y-%m-%d")

        opt_months = max(1, (opt_end.year - opt_start.year) * 12 + opt_end.month - opt_start.month)
        hld_months = max(1, (hld_end.year - hld_start.year) * 12 + hld_end.month - hld_start.month)

        # test = 留存期长度，train = 优化期的 1/3~1/2，step = test
        test_months = max(1, hld_months)
        train_months = max(test_months + 1, opt_months // 3)
        step_months = max(1, test_months)

        walk_forward_config = {
            'train_months': train_months,
            'test_months': test_months,
            'step_months': step_months,
        }

    start_date, end_date = optimization_period
    holdout_start, holdout_end = holdout_period

    # 创建参数空间实例
    param_space = parameter_space()

    # 动态计算patience（如果未指定）
    space_size = parameter_space.calculate_space_size()
    if patience is None:
        patience = int(space_size / 4)

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
    print(t("opt.holdout_test", year=holdout_start[:4]))
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

    return study
