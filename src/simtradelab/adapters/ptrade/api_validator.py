# -*- coding: utf-8 -*-
"""
PTrade API 调用验证器

负责验证API调用的合法性，包括生命周期限制、参数验证等
"""

import functools
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .lifecycle_controller import (
    LifecycleController,
    PTradeLifecycleError,
    get_lifecycle_controller,
)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class APIValidationResult:
    """API验证结果"""

    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class APIValidator:
    """PTrade API调用验证器

    功能：
    1. 验证API调用的生命周期限制
    2. 验证API参数的合法性
    3. 提供API调用装饰器
    4. 记录验证结果和统计
    """

    def __init__(self, lifecycle_controller: Optional[LifecycleController] = None):
        """
        初始化API验证器

        Args:
            lifecycle_controller: 生命周期控制器实例
        """
        self._lifecycle_controller = lifecycle_controller or get_lifecycle_controller()
        self._logger = logging.getLogger(self.__class__.__name__)

        # 验证统计
        self._validation_count = 0
        self._validation_failures = 0
        self._api_usage_stats: Dict[str, int] = {}

    def validate_api_call(self, api_name: str, *args, **kwargs) -> APIValidationResult:
        """验证API调用的完整性

        Args:
            api_name: API函数名
            *args: API调用参数
            **kwargs: API调用关键字参数

        Returns:
            APIValidationResult: 验证结果
        """
        self._validation_count += 1
        result = APIValidationResult(is_valid=True)

        try:
            # 1. 验证生命周期限制
            lifecycle_result = self._validate_lifecycle(api_name)
            if not lifecycle_result.is_valid:
                result.is_valid = False
                result.error_message = lifecycle_result.error_message
                return result

            # 2. 验证参数合法性
            param_result = self._validate_parameters(api_name, *args, **kwargs)
            if not param_result.is_valid:
                result.is_valid = False
                result.error_message = param_result.error_message
                return result

            # 3. 收集警告信息
            result.warnings.extend(lifecycle_result.warnings)
            result.warnings.extend(param_result.warnings)

            # 4. 更新统计
            self._api_usage_stats[api_name] = self._api_usage_stats.get(api_name, 0) + 1

            return result

        except Exception as e:
            self._validation_failures += 1
            self._logger.error(f"API validation error for '{api_name}': {e}")
            return APIValidationResult(
                is_valid=False, error_message=f"Validation error: {str(e)}"
            )

    def _validate_lifecycle(self, api_name: str) -> APIValidationResult:
        """验证API的生命周期限制

        Args:
            api_name: API函数名

        Returns:
            APIValidationResult: 生命周期验证结果
        """
        try:
            # 使用生命周期控制器验证
            self._lifecycle_controller.validate_api_call(api_name)
            return APIValidationResult(is_valid=True)

        except PTradeLifecycleError as e:
            return APIValidationResult(is_valid=False, error_message=str(e))
        except Exception as e:
            # 如果生命周期验证出现其他错误，记录但不阻止调用
            warning_msg = f"Lifecycle validation warning for '{api_name}': {e}"
            self._logger.warning(warning_msg)
            return APIValidationResult(is_valid=True, warnings=[warning_msg])

    def _validate_parameters(
        self, api_name: str, *args, **kwargs
    ) -> APIValidationResult:
        """验证API参数的合法性

        Args:
            api_name: API函数名
            *args: API调用参数
            **kwargs: API调用关键字参数

        Returns:
            APIValidationResult: 参数验证结果
        """
        result = APIValidationResult(is_valid=True)

        # 特定API的参数验证规则
        validation_rules = {
            "set_commission": self._validate_commission_params,
            "set_slippage": self._validate_slippage_params,
            "set_volume_ratio": self._validate_volume_ratio_params,
            "order": self._validate_order_params,
            "order_target": self._validate_order_target_params,
            "set_universe": self._validate_universe_params,
            "get_history": self._validate_history_params,
            "get_price": self._validate_price_params,
        }

        validator = validation_rules.get(api_name)
        if validator:
            try:
                validator(*args, **kwargs)
            except ValueError as e:
                result.is_valid = False
                result.error_message = (
                    f"Parameter validation failed for '{api_name}': {str(e)}"
                )
            except Exception as e:
                warning_msg = f"Parameter validation warning for '{api_name}': {e}"
                result.warnings.append(warning_msg)

        return result

    def _validate_commission_params(self, commission: float, *args, **kwargs) -> None:
        """验证佣金费率参数"""
        if not isinstance(commission, (int, float)):
            raise ValueError("Commission must be a number")
        if commission < 0:
            raise ValueError("Commission cannot be negative")
        if commission > 1:
            raise ValueError("Commission rate should not exceed 100% (1.0)")

    def _validate_slippage_params(self, slippage: float, *args, **kwargs) -> None:
        """验证滑点参数"""
        if not isinstance(slippage, (int, float)):
            raise ValueError("Slippage must be a number")
        if slippage < 0:
            raise ValueError("Slippage cannot be negative")
        if slippage > 0.1:  # 10%
            raise ValueError("Slippage rate seems too high (>10%)")

    def _validate_volume_ratio_params(self, ratio: float, *args, **kwargs) -> None:
        """验证成交比例参数"""
        if not isinstance(ratio, (int, float)):
            raise ValueError("Volume ratio must be a number")
        if not (0 < ratio <= 1):
            raise ValueError("Volume ratio must be between 0 and 1")

    def _validate_order_params(
        self,
        security: str,
        amount: int,
        limit_price: Optional[float] = None,
        *args,
        **kwargs,
    ) -> None:
        """验证下单参数"""
        if not isinstance(security, str) or not security:
            raise ValueError("Security must be a non-empty string")

        if not isinstance(amount, int):
            raise ValueError("Amount must be an integer")

        if amount == 0:
            raise ValueError("Amount cannot be zero")

        if limit_price is not None:
            if not isinstance(limit_price, (int, float)):
                raise ValueError("Limit price must be a number")
            if limit_price <= 0:
                raise ValueError("Limit price must be positive")

    def _validate_order_target_params(
        self,
        security: str,
        target_amount: int,
        limit_price: Optional[float] = None,
        *args,
        **kwargs,
    ) -> None:
        """验证目标数量下单参数"""
        if not isinstance(security, str) or not security:
            raise ValueError("Security must be a non-empty string")

        if not isinstance(target_amount, int):
            raise ValueError("Target amount must be an integer")

        if target_amount < 0:
            raise ValueError("Target amount cannot be negative")

        if limit_price is not None:
            if not isinstance(limit_price, (int, float)):
                raise ValueError("Limit price must be a number")
            if limit_price <= 0:
                raise ValueError("Limit price must be positive")

    def _validate_universe_params(self, securities: List[str], *args, **kwargs) -> None:
        """验证股票池参数"""
        if not isinstance(securities, (list, tuple)):
            raise ValueError("Securities must be a list or tuple")

        if not securities:
            raise ValueError("Securities list cannot be empty")

        for security in securities:
            if not isinstance(security, str) or not security:
                raise ValueError("Each security must be a non-empty string")

    def _validate_history_params(
        self,
        count: int,
        frequency: str = "1d",
        field: Union[str, List[str]] = None,
        *args,
        **kwargs,
    ) -> None:
        """验证历史数据获取参数"""
        if not isinstance(count, int) or count <= 0:
            raise ValueError("Count must be a positive integer")

        if not isinstance(frequency, str):
            raise ValueError("Frequency must be a string")

        valid_frequencies = ["1d", "1h", "30m", "15m", "5m", "1m"]
        if frequency not in valid_frequencies:
            raise ValueError(f"Invalid frequency. Valid options: {valid_frequencies}")

    def _validate_price_params(
        self,
        security: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        """验证价格数据获取参数"""
        if isinstance(security, str):
            if not security:
                raise ValueError("Security must be a non-empty string")
        elif isinstance(security, (list, tuple)):
            if not security:
                raise ValueError("Security list cannot be empty")
            for sec in security:
                if not isinstance(sec, str) or not sec:
                    raise ValueError("Each security must be a non-empty string")
        else:
            raise ValueError("Security must be a string or list of strings")

    def get_validation_statistics(self) -> Dict[str, Any]:
        """获取验证统计信息

        Returns:
            Dict[str, Any]: 验证统计信息
        """
        success_rate = 1.0
        if self._validation_count > 0:
            success_rate = (
                self._validation_count - self._validation_failures
            ) / self._validation_count

        return {
            "total_validations": self._validation_count,
            "validation_failures": self._validation_failures,
            "success_rate": success_rate,
            "api_usage_stats": self._api_usage_stats.copy(),
            "most_used_apis": sorted(
                self._api_usage_stats.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    def reset_statistics(self) -> None:
        """重置验证统计信息"""
        self._validation_count = 0
        self._validation_failures = 0
        self._api_usage_stats.clear()


def api_validator(
    api_name: Optional[str] = None, validator: Optional[APIValidator] = None
):
    """API调用验证装饰器

    Args:
        api_name: API函数名，如果为None则使用被装饰函数名
        validator: 验证器实例，如果为None则使用默认验证器

    Returns:
        装饰器函数
    """

    def decorator(func: F) -> F:
        actual_api_name = api_name or func.__name__
        actual_validator = validator or APIValidator()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 验证API调用
            validation_result = actual_validator.validate_api_call(
                actual_api_name, *args, **kwargs
            )

            if not validation_result.is_valid:
                # 记录验证失败
                actual_validator._lifecycle_controller.record_api_call(
                    actual_api_name,
                    success=False,
                    args=args,
                    kwargs=kwargs,
                    error=validation_result.error_message,
                )
                raise PTradeLifecycleError(validation_result.error_message)

            # 如果有警告，记录到日志
            for warning in validation_result.warnings:
                logging.getLogger(func.__module__).warning(warning)

            try:
                # 执行原函数
                result = func(*args, **kwargs)

                # 记录成功调用
                actual_validator._lifecycle_controller.record_api_call(
                    actual_api_name, success=True, args=args, kwargs=kwargs
                )

                return result

            except Exception as e:
                # 记录执行失败
                actual_validator._lifecycle_controller.record_api_call(
                    actual_api_name,
                    success=False,
                    args=args,
                    kwargs=kwargs,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator


# 全局API验证器实例
_global_validator: Optional[APIValidator] = None


def get_api_validator() -> APIValidator:
    """获取全局API验证器实例"""
    global _global_validator
    if _global_validator is None:
        _global_validator = APIValidator()
    return _global_validator


def set_global_api_validator(validator: APIValidator) -> None:
    """设置全局API验证器实例"""
    global _global_validator
    _global_validator = validator


# 便捷装饰器
def ptrade_api(api_name: Optional[str] = None):
    """便捷的PTrade API验证装饰器"""
    return api_validator(api_name, get_api_validator())
