#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一数据切片入口

执行所有数据切片任务：
1. ptrade_data.h5（股票数据、除权、基准、元数据）
2. ptrade_fundamentals.h5（估值、基本面）
"""

import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from slice_data import slice_hdf5_data
from slice_fundamentals import slice_fundamentals_data


def main():
    """执行完整数据切片"""

    # 配置 - 使用~表示用户目录
    source_dir = '~/dev/ptrade/data'
    target_dir = '~/dev/SimTradeLab/data'
    start_date = '20250101'
    end_date = '20251031'

    # 展开用户目录
    source_dir = os.path.expanduser(source_dir)
    target_dir = os.path.expanduser(target_dir)

    print("=" * 70)
    print("SimTradeLab 数据切片工具")
    print("=" * 70)
    print(f"\n配置:")
    print(f"  源目录: {source_dir}")
    print(f"  目标目录: {target_dir}")
    print(f"  日期范围: {start_date} ~ {end_date}")
    print(f"\n将处理:")
    print(f"  1. {os.path.join(source_dir, 'ptrade_data.h5')}")
    print(f"  2. {os.path.join(source_dir, 'ptrade_fundamentals.h5')}")
    print()

    # 确认
    response = input("确认执行所有切片任务? (y/N): ")
    if response.lower() != 'y':
        print("已取消")
        return

    print()

    # 切片1: 主数据文件
    try:
        source_data = os.path.join(source_dir, 'ptrade_data.h5')
        target_data = os.path.join(target_dir, 'ptrade_data.h5')

        if not os.path.exists(source_data):
            print(f"错误: 源文件不存在 {source_data}")
            return

        print("\n" + "=" * 70)
        print("任务 1/2: 切片股票数据")
        print("=" * 70)
        slice_hdf5_data(source_data, target_data, start_date, end_date)

    except Exception as e:
        print(f"\n错误: 股票数据切片失败 - {e}")
        return

    # 切片2: 基本面数据文件
    try:
        source_fundamentals = os.path.join(source_dir, 'ptrade_fundamentals.h5')
        target_fundamentals = os.path.join(target_dir, 'ptrade_fundamentals.h5')

        if not os.path.exists(source_fundamentals):
            print(f"警告: 基本面源文件不存在 {source_fundamentals}，跳过")
        else:
            print("\n" + "=" * 70)
            print("任务 2/2: 切片基本面数据")
            print("=" * 70)
            slice_fundamentals_data(source_fundamentals, target_fundamentals, start_date, end_date)

    except Exception as e:
        print(f"\n错误: 基本面数据切片失败 - {e}")
        return

    # 删除旧的缓存
    adj_cache = os.path.join(target_dir, 'ptrade_adj_pre.h5')
    if os.path.exists(adj_cache):
        print(f"\n清理旧缓存: {adj_cache}")
        os.remove(adj_cache)
        print("  ✓ 已删除旧的复权因子缓存（将在首次运行时自动重建）")

    print("\n" + "=" * 70)
    print("✓ 所有切片任务完成！")
    print("=" * 70)
    print("\n下次运行回测时，将自动加载新数据并生成复权缓存")


if __name__ == '__main__':
    main()
