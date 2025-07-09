#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for SimTradeLab

This file serves as a fallback for environments where Poetry is not available.
The primary build system is defined in pyproject.toml using Poetry.
"""

import os
import sys
from pathlib import Path

try:
    from setuptools import find_packages, setup
except ImportError:
    print("Error: setuptools is required to install SimTradeLab")
    print("Please install setuptools first: pip install setuptools")
    sys.exit(1)

# Determine the directory containing this setup.py file
here = Path(__file__).parent.absolute()


# Read version from __init__.py
def get_version():
    init_file = here / "src" / "simtradelab" / "__init__.py"
    if init_file.exists():
        with open(init_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"


# Read the README file
def get_long_description():
    readme_file = here / "README.md"
    if readme_file.exists():
        with open(readme_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Core dependencies (keep in sync with pyproject.toml)
INSTALL_REQUIRES = [
    "pandas>=2.3.0,<3.0.0",
    "numpy>=2.0.0,<3.0.0",
    "matplotlib>=3.10.3,<4.0.0",
    "PyYAML>=6.0",
    "setuptools>=65.0",
    "wheel>=0.37.0",
]

# Optional dependencies
EXTRAS_REQUIRE = {
    "data": [
        "akshare>=1.17.16",
        "tushare>=1.2.89",
    ],
    "dev": [
        "pytest>=8.2.1",
        "pytest-cov>=5.0.0",
        "pytest-mock>=3.12.0",
        "pytest-xdist>=3.6.0",
        "psutil>=6.0.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
        "pre-commit>=3.0.0",
        "bandit>=1.7.0",
    ],
    "web": [
        "fastapi>=0.68.0",
        "uvicorn[standard]>=0.15.0",
        "python-multipart>=0.0.5",
        "jinja2>=3.0.0",
        "aiofiles>=0.7.0",
    ],
}

# Platform-specific handling for Windows
if sys.platform == "win32":
    # Add Windows-specific requirements if needed
    pass

setup(
    name="simtradelab",
    version=get_version(),
    description="开源策略回测框架，灵感来自PTrade的事件驱动模型，提供轻量、清晰、可插拔的策略验证环境",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Kay",
    author_email="kayou@duck.com",
    url="https://github.com/kay-ou/SimTradeLab",
    license="MIT",
    # Package discovery
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Include data files
    include_package_data=True,
    package_data={
        "simtradelab": ["*.yaml", "*.yml"],
        "": ["*.md", "*.txt", "*.csv"],
    },
    # Dependencies
    python_requires=">=3.10.0",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    # Entry points
    entry_points={
        "console_scripts": [
            "simtradelab=simtradelab.cli:main",
        ],
    },
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "trading",
        "backtesting",
        "quantitative",
        "finance",
        "strategy",
        "akshare",
        "tushare",
    ],
    # Additional metadata
    project_urls={
        "Homepage": "https://github.com/kay-ou/SimTradeLab",
        "Repository": "https://github.com/kay-ou/SimTradeLab",
        "Documentation": "https://github.com/kay-ou/SimTradeLab/blob/main/README.md",
        "Bug Reports": "https://github.com/kay-ou/SimTradeLab/issues",
    },
    # Build options
    zip_safe=False,
)
