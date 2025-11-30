# -*- coding: utf-8 -*-
"""
通用策略参数优化框架

使用方法：
1. 创建strategies/{strategy_name}/optimization/目录
2. 复制此文件到该目录，命名为optimize_params.py
3. 修改ParameterSpace类中的参数空间定义
4. 修改create_strategy_code中的参数映射
5. 运行: poetry run python strategies/{strategy_name}/optimization/optimize_params.py
"""

import optuna
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List
from abc import ABC, abstractmethod

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig


# ==================== 优化配置 ====================
DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2025-10-31"
DEFAULT_INITIAL_CAPITAL = 100000.0
DEFAULT_N_TRIALS = 50


# ==================== 参数空间基类 ====================
class BaseParameterSpace(ABC):
    """参数空间定义基类 - 需要子类实现"""

    @staticmethod
    @abstractmethod
    def suggest_parameters(trial: optuna.Trial) -> Dict[str, Any]:
        """建议参数值（必须由子类实现）

        Args:
            trial: Optuna trial对象

        Returns:
            Dict[str, Any]: 参数字典

        Example:
            return {
                'max_positions': trial.suggest_int('max_positions', 5, 15),
                'stop_loss': trial.suggest_float('stop_loss', -0.10, -0.02, step=0.01),
            }
        """
        pass

    @staticmethod
    def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """验证并修正参数（可选，子类可覆盖）

        Args:
            params: 参数字典

        Returns:
            Dict[str, Any]: 修正后的参数字典
        """
        return params


# ==================== 参数映射辅助函数 ====================

def resolve_variable_name(param_name: str, custom_mapping: Dict[str, str] = None) -> str:
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



# ==================== 评分策略基类 ====================
class BaseScoringStrategy(ABC):
    """评分策略基类"""

    @staticmethod
    @abstractmethod
    def calculate_score(metrics: Dict[str, float]) -> float:
        """计算综合得分

        Args:
            metrics: 回测指标字典

        Returns:
            float: 综合得分

        Example:
            return (
                metrics['annual_return'] * 0.4 +
                metrics['sharpe_ratio'] * 0.3 +
                (-metrics['max_drawdown']) * 0.3
            )
        """
        pass

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


# ==================== 策略优化器（通用） ====================
class StrategyOptimizer:
    """通用策略参数优化器"""

    def __init__(
        self,
        strategy_path: str,
        parameter_space: BaseParameterSpace,
        scoring_strategy: BaseScoringStrategy,
        start_date: str = DEFAULT_START_DATE,
        end_date: str = DEFAULT_END_DATE,
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
        custom_mapping: Dict[str, str] = None,
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
        """
        self.strategy_path = Path(strategy_path)
        self.parameter_space = parameter_space
        self.scoring_strategy = scoring_strategy
        self.custom_mapping = custom_mapping or {}
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        # 优化配置
        self.optimization_dir = self.strategy_path.parent / "optimization"
        self.results_dir = self.optimization_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def create_strategy_code(self, params: Dict[str, Any]) -> str:
        """基于参数创建策略代码"""
        import re

        # 读取原始策略代码
        with open(self.strategy_path, 'r', encoding='utf-8') as f:
            original_code = f.read()

        modified_code = original_code

        # 使用正则表达式替换参数值
        for param_name, param_value in params.items():
            # 使用 resolve_variable_name 函数自动解析变量名
            var_name = resolve_variable_name(param_name, self.custom_mapping)

            # 匹配 g.parameter = value 的模式
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

    def run_backtest_with_params(self, params: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """使用给定参数运行回测"""
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

            runner = BacktestRunner()
            config = BacktestConfig(
                strategy_name=temp_strategy_name,
                start_date=self.start_date,
                end_date=self.end_date,
                initial_capital=self.initial_capital,
                enable_logging=False,
                enable_charts=False
            )

            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                report = runner.run(config=config)

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

            return score, metrics

        except Exception as e:
            print(f"回测执行失败: {e}")
            return -999.0, {}
        finally:
            # 清理临时文件
            import shutil
            if temp_strategy_dir and temp_strategy_dir.exists():
                try:
                    shutil.rmtree(temp_strategy_dir)
                except:
                    pass

    def objective(self, trial: optuna.Trial) -> float:
        """Optuna优化目标函数"""
        # 生成参数
        params = self.parameter_space.suggest_parameters(trial)
        # 验证参数
        params = self.parameter_space.validate_parameters(params)

        # 运行回测
        score, metrics = self.run_backtest_with_params(params)

        # 记录指标
        for key, value in metrics.items():
            trial.set_user_attr(key, value)

        return score

    def optimize(self, n_trials: int = DEFAULT_N_TRIALS, resume: bool = True) -> optuna.Study:
        """执行参数优化
        
        Args:
            n_trials: 总共要运行的试验次数
            resume: 是否从上次中断处继续（默认 True）
            
        Returns:
            optuna.Study: 优化研究对象
        """
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
                completed_trials = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
                print(f"\n发现已有优化进度: {completed_trials} 个已完成试验")
                print(f"将继续优化至 {n_trials} 个试验...")
                
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
            study = optuna.create_study(
                study_name=study_name,
                storage=storage,
                direction='maximize',
                sampler=optuna.samplers.TPESampler(seed=42),
                pruner=optuna.pruners.MedianPruner(),
                load_if_exists=False  # 不加载已有的
            )
            remaining_trials = n_trials

        # 静默模式
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        # 执行优化（单线程）
        print(f"开始优化，将运行 {remaining_trials} 个新试验...\n")
        study.optimize(
            self.objective,
            n_trials=remaining_trials,
            n_jobs=1,
            show_progress_bar=True
        )

        # 保存结果
        self.save_optimization_results(study)

        return study

    def save_optimization_results(self, study: optuna.Study):
        """保存优化结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存最佳参数
        import json
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

        # 输出摘要
        print(f"\n优化完成!")
        print(f"最佳得分: {study.best_value:.4f}")
        print(f"最佳参数: {json.dumps(study.best_params, indent=2, ensure_ascii=False)}")
        print(f"结果保存到: {self.results_dir}")

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
    custom_mapping: Dict[str, str] = None
):
    """基于最佳参数创建优化后的策略文件"""
    import json
    import re

    # 读取最佳参数
    with open(best_params_file, 'r', encoding='utf-8') as f:
        best_params = json.load(f)

    # 读取原始策略
    with open(original_strategy_path, 'r', encoding='utf-8') as f:
        original_code = f.read()

    modified_code = original_code

    # 替换参数
    for param_name, param_value in best_params.items():
        # 使用 resolve_variable_name 函数获取变量名
        var_name = resolve_variable_name(param_name, custom_mapping)
        pattern = rf'(^\s*{re.escape(var_name)}\s*=\s*)[^#\n]+'

        if isinstance(param_value, str):
            replacement = f"\\g<1>'{param_value}'"
        elif isinstance(param_value, bool):
            replacement = f"\\g<1>{param_value}"
        else:
            replacement = f"\\g<1>{param_value}"

        modified_code = re.sub(pattern, replacement, modified_code, flags=re.MULTILINE)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(modified_code)

    print(f"优化后的策略已保存到: {output_path}")
