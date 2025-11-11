#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据切片脚本 - 从完整数据中提取指定日期范围的数据

用途：从 /home/kay/dev/ptrade/data/ptrade_data.h5 切片出指定日期范围的数据
包含：股票数据、除权数据、基准数据、元数据、股票元信息等所有必要数据
"""

import pandas as pd
import sys
import os
import warnings
from tables import NaturalNameWarning

warnings.filterwarnings("ignore", category=NaturalNameWarning)


def slice_hdf5_data(
    source_path: str,
    target_path: str,
    start_date: str = '20250101',
    end_date: str = '20251031'
):
    """从完整HDF5文件切片指定日期范围的数据

    Args:
        source_path: 源数据路径（完整数据）
        target_path: 目标路径（切片后数据）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    print("=" * 70)
    print(f"数据切片: {start_date} ~ {end_date}")
    print("=" * 70)

    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    # 打开源数据
    print(f"\n读取源数据: {source_path}")
    source_store = pd.HDFStore(source_path, 'r')

    # 创建目标存储（最高压缩）
    print(f"创建目标文件: {target_path}")
    if os.path.exists(target_path):
        backup = target_path + '.backup'
        print(f"  备份已存在文件到: {backup}")
        os.rename(target_path, backup)

    # 使用zstd压缩（比blosc更高压缩率）
    target_store = pd.HDFStore(
        target_path, 'w',
        complevel=9,
        complib='blosc:zstd'  # zstd压缩算法
    )

    try:
        # 1. 复制 metadata（元数据，不需要切片）
        print("\n[1/6] 复制元数据...")
        if '/metadata' in source_store:
            try:
                metadata = source_store['/metadata']
                # metadata可能包含混合类型，使用fixed格式
                target_store.put('/metadata', metadata, format='fixed')
                print(f"  ✓ metadata: {len(metadata)} 条记录")
            except Exception as e:
                print(f"  警告: metadata复制失败: {e}")

        # 2. 复制 stock_metadata（股票元信息，不需要切片）
        print("\n[2/6] 复制股票元信息...")
        if '/stock_metadata' in source_store:
            try:
                stock_metadata = source_store['/stock_metadata']
                target_store.put('/stock_metadata', stock_metadata, format='fixed')
                print(f"  ✓ stock_metadata: {len(stock_metadata)} 只股票")
            except Exception as e:
                print(f"  警告: stock_metadata复制失败: {e}")

        # 3. 切片 benchmark（基准数据）
        print("\n[3/6] 切片基准数据...")
        if '/benchmark' in source_store:
            try:
                benchmark = source_store['/benchmark']
                # 基准数据按日期切片
                sliced_benchmark = benchmark[(benchmark.index >= start_dt) & (benchmark.index <= end_dt)]
                target_store.put('/benchmark', sliced_benchmark, format='fixed')
                print(f"  ✓ benchmark: {len(sliced_benchmark)} 天 (原 {len(benchmark)} 天)")
            except Exception as e:
                print(f"  警告: benchmark切片失败: {e}")

        # 4. 切片 stock_data（股票价格数据）
        print("\n[4/6] 切片股票价格数据...")
        stock_keys = [k for k in source_store.keys() if k.startswith('/stock_data/')]
        print(f"  找到 {len(stock_keys)} 只股票")

        saved_count = 0
        for i, key in enumerate(stock_keys):
            if (i + 1) % 500 == 0:
                print(f"  处理中: {i + 1}/{len(stock_keys)}, 已保存 {saved_count} 只...")

            try:
                df = source_store[key]
                # 按日期切片
                sliced_df = df[(df.index >= start_dt) & (df.index <= end_dt)]

                # 只保存有数据的股票
                if len(sliced_df) > 0:
                    # 使用fixed格式避免序列化问题（不支持混合类型检查）
                    target_store.put(key, sliced_df, format='fixed')
                    saved_count += 1
            except Exception as e:
                print(f"  警告: 跳过 {key}: {e}")
                continue

        print(f"  ✓ 保存 {saved_count} 只股票价格数据")

        # 5. 切片 exrights（除权数据，只保留日期范围内的除权事件）
        print("\n[5/6] 切片除权数据...")
        exrights_keys = [k for k in source_store.keys() if k.startswith('/exrights/')]
        print(f"  找到 {len(exrights_keys)} 只股票的除权数据")

        saved_exrights = 0
        for i, key in enumerate(exrights_keys):
            if (i + 1) % 500 == 0:
                print(f"  处理中: {i + 1}/{len(exrights_keys)}, 已保存 {saved_exrights} 只...")

            try:
                df = source_store[key]
                if len(df) > 0:
                    # 切片除权数据，只保留日期范围内的记录
                    start_int = int(start_date)
                    end_int = int(end_date)
                    sliced_df = df[(df.index >= start_int) & (df.index <= end_int)]

                    if len(sliced_df) > 0:
                        target_store.put(key, sliced_df, format='fixed')
                        saved_exrights += 1
            except Exception as e:
                print(f"  警告: 跳过 {key}: {e}")
                continue

        print(f"  ✓ 保存 {saved_exrights} 只股票除权数据")

        # 6. 切片 trade_days（交易日历）
        print("\n[6/6] 切片交易日历...")
        if '/trade_days' in source_store:
            try:
                trade_days = source_store['/trade_days']
                sliced_trade_days = trade_days[(trade_days.index >= start_dt) & (trade_days.index <= end_dt)]
                target_store.put('/trade_days', sliced_trade_days, format='fixed')
                print(f"  ✓ trade_days: {len(sliced_trade_days)} 天 (原 {len(trade_days)} 天)")
            except Exception as e:
                print(f"  警告: trade_days切片失败: {e}")

        print("\n" + "=" * 70)
        print("✓ 数据切片完成！")
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

        # 文件大小
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
    # 默认路径
    source = '/home/kay/dev/ptrade/data/ptrade_data.h5'
    target = '/home/kay/dev/SimTradeLab/data/ptrade_data.h5'

    # 支持命令行参数
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

    # 确认执行
    response = input("确认执行切片? (y/N): ")
    if response.lower() != 'y':
        print("已取消")
        sys.exit(0)

    slice_hdf5_data(source, target, start_date, end_date)
