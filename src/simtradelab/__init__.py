# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""SimTradeLab - 开源策略回测框架

"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("simtradelab")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = ["__version__"]
