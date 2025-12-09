"""SimTradeLab - 开源策略回测框架"""

# 从 pyproject.toml 动态读取版本号（单一数据源）
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 的兼容性
    from importlib_metadata import version, PackageNotFoundError  # type: ignore

try:
    __version__ = version("simtradelab")
except PackageNotFoundError:
    # 包未安装时的后备版本（开发环境）
    __version__ = "0.0.0.dev"

__all__ = ["__version__"]
