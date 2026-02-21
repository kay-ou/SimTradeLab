# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""图表工具模块 — 水印、保存等公共函数"""

import matplotlib.pyplot as plt


def save_figure(fig, path, dpi=150, close=True, **kwargs):
    """添加 SimTradeLab 水印后保存图表。

    必须在 tight_layout() 之后调用。
    """
    fig.text(
        0.99, 0.99, 'SimTradeLab',
        fontsize=10, color='gray', alpha=0.15,
        ha='right', va='top',
        fontfamily='sans-serif', style='italic',
    )
    fig.savefig(path, dpi=dpi, **kwargs)
    if close:
        plt.close(fig)
