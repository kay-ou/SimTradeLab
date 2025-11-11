#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基本面数据切片脚本

从完整基本面数据中提取指定日期范围的数据
"""

import pandas as pd
import sys
import os
import warnings
from tables import NaturalNameWarning

warnings.filterwarnings("ignore", category=NaturalNameWarning)


def slice_fundamentals_data(
    source_path: str,
    target_path: str,
    start_date: str = '20250101',
    end_date: str = '20251031'
):
    """从完整基本面HDF5文件切片指定日期范围的数据

    Args:
        source_path: 源数据路径
        target_path: 目标路径
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    print("=" * 70)
    print(f"基本面数据切片: {start_date} ~ {end_date}")
    print("=" * 70)

    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    print(f"\n读取源数据: {source_path}")
    source_store = pd.HDFStore(source_path, 'r')

    print(f"创建目标文件: {target_path}")
    if os.path.exists(target_path):
        backup = target_path + '.backup'
        print(f"  备份已存在文件到: {backup}")
        os.rename(target_path, backup)

    # 使用zstd最高压缩
    target_store = pd.HDFStore(
        target_path, 'w',
        complevel=9,
        complib='blosc:zstd'
    )

    try:
        # 1. 切片 valuation（估值数据）
        print("\n[1/2] 切片估值数据...")
        valuation_keys = [k for k in source_store.keys() if k.startswith('/valuation/')]
        print(f"  找到 {len(valuation_keys)} 只股票")

        saved_count = 0
        for i, key in enumerate(valuation_keys):
            if (i + 1) % 500 == 0:
                print(f"  处理中: {i + 1}/{len(valuation_keys)}, 已保存 {saved_count} 只...")

            df = source_store[key]
            # 按日期切片
            sliced_df = df[(df.index >= start_dt) & (df.index <= end_dt)]

            if len(sliced_df) > 0:
                target_store.put(key, sliced_df, format='fixed')
                saved_count += 1

        print(f"  ✓ 保存 {saved_count} 只股票估值数据")

        # 2. 切片 fundamentals（基本面数据）
        print("\n[2/2] 切片基本面数据...")
        fundamentals_keys = [k for k in source_store.keys() if k.startswith('/fundamentals/')]
        print(f"  找到 {len(fundamentals_keys)} 只股票")

        saved_count = 0
        for i, key in enumerate(fundamentals_keys):
            if (i + 1) % 500 == 0:
                print(f"  处理中: {i + 1}/{len(fundamentals_keys)}, 已保存 {saved_count} 只...")

            df = source_store[key]
            # 按日期切片
            sliced_df = df[(df.index >= start_dt) & (df.index <= end_dt)]

            if len(sliced_df) > 0:
                target_store.put(key, sliced_df, format='fixed')
                saved_count += 1

        print(f"  ✓ 保存 {saved_count} 只股票基本面数据")

        print("\n" + "=" * 70)
        print("✓ 基本面数据切片完成！")
        print("=" * 70)

        # 统计信息
        print("\n目标文件统计:")
        target_keys = target_store.keys()
        categories = {}
        for key in target_keys:
            cat = key.split('/')[1] if len(key.split('/')) > 1 else 'root'
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items()):
            print(f"  /{cat}/: {count} 项")

        target_store.close()
        source_store.close()

        source_size = os.path.getsize(source_path) / (1024 ** 3)
        target_size = os.path.getsize(target_path) / (1024 ** 3)
        print(f"\n文件大小:")
        print(f"  源文件: {source_size:.2f} GB")
        print(f"  目标文件: {target_size:.2f} GB")
        print(f"  压缩率: {target_size / source_size * 100:.1f}%")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        source_store.close()
        target_store.close()
        raise


if __name__ == '__main__':
    source = '/home/kay/dev/ptrade/data/ptrade_fundamentals.h5'
    target = '/home/kay/dev/SimTradeLab/data/ptrade_fundamentals.h5'

    if len(sys.argv) > 1:
        source = sys.argv[1]
    if len(sys.argv) > 2:
        target = sys.argv[2]

    start_date = '20250101'
    end_date = '20251031'

    if len(sys.argv) > 3:
        start_date = sys.argv[3]
    if len(sys.argv) > 4:
        end_date = sys.argv[4]

    print(f"\n配置:")
    print(f"  源文件: {source}")
    print(f"  目标文件: {target}")
    print(f"  日期范围: {start_date} ~ {end_date}")
    print()

    if not os.path.exists(source):
        print(f"错误: 源文件不存在 {source}")
        sys.exit(1)

    response = input("确认执行切片? (y/N): ")
    if response.lower() != 'y':
        print("已取消")
        sys.exit(0)

    slice_fundamentals_data(source, target, start_date, end_date)
