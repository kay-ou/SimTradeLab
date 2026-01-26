# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
数据包解包和合并工具
"""

from __future__ import annotations
import json
import brotli
import tarfile
from pathlib import Path
from tqdm import tqdm
import hashlib


class DataUnpacker:
    """数据解包器"""

    def __init__(self, data_dir):
        """初始化解包器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)

    def unpack_all(self, download_dir, verify=True):
        """解包所有下载的tar.gz文件

        Args:
            download_dir: 下载目录路径
            verify: 是否验证校验和
        """
        download_dir = Path(download_dir)

        print("=" * 70)
        print("SimTradeLab 数据解包工具")
        print("=" * 70)

        # 加载清单
        manifest_file = download_dir / 'manifest.json'
        if not manifest_file.exists():
            print("错误：找不到manifest.json文件")
            return

        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        print("数据版本: {}".format(manifest['version']))
        print("导出日期: {}".format(manifest['export_date']))
        print("=" * 70)

        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 解压所有包
        for pkg_info in tqdm(manifest['packages'], desc="解包"):
            pkg_path = download_dir / pkg_info['name']

            if not pkg_path.exists():
                print("\n警告：文件不存在 {}".format(pkg_info['name']))
                continue

            # 解压
            with tarfile.open(pkg_path, 'r:gz') as tar:
                tar.extractall(path=self.data_dir)

        # 保存版本信息
        version_info = {
            'version': manifest['version'],
            'export_date': manifest['export_date'],
            'install_date': str(pd.Timestamp.now())
        }

        version_file = self.data_dir / 'version.json'
        with open(version_file, 'w') as f:
            json.dump(version_info, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 70)
        print("解包完成！数据目录: {}".format(self.data_dir))
        print("=" * 70)


class DataMerger:
    """增量数据合并器"""

    def __init__(self, data_dir, compression_quality=6, num_workers=1):
        """初始化合并器

        Args:
            data_dir: 数据目录路径
            compression_quality: Brotli压缩质量（1-11）
            num_workers: 并行进程数
        """
        self.data_dir = Path(data_dir)
        self.stocks_dir = self.data_dir / 'stocks'
        self.exrights_dir = self.data_dir / 'exrights'
        self.compression_quality = compression_quality
        self.num_workers = num_workers

    def merge_incremental(self, incremental_file):
        """合并增量数据到现有文件

        Args:
            incremental_file: 增量数据文件路径
        """
        incremental_file = Path(incremental_file)

        print("=" * 70)
        print("SimTradeLab 增量数据合并")
        print("=" * 70)
        print("增量文件: {}".format(incremental_file.name))
        print("=" * 70)

        # 解压增量包
        with open(incremental_file, 'rb') as f:
            compressed = f.read()
            decompressed = brotli.decompress(compressed)
            incremental_data = json.loads(decompressed.decode('utf-8'))

        print("\n合并 {} 只股票数据...".format(len(incremental_data)))

        # 合并数据
        if self.num_workers > 1:
            # 多进程并行（可选实现）
            print("警告：多进程模式未实现，使用单进程")
            self._merge_single_process(incremental_data)
        else:
            self._merge_single_process(incremental_data)

        print("\n" + "=" * 70)
        print("合并完成！")
        print("=" * 70)

    def _merge_single_process(self, incremental_data):
        """单进程合并"""
        # 判断是价格数据还是除权数据
        first_key = next(iter(incremental_data))
        first_value = incremental_data[first_key]

        if isinstance(first_value, dict) and 'exrights_events' in first_value:
            # 除权数据
            target_dir = self.exrights_dir
            is_exrights = True
        else:
            # 价格数据
            target_dir = self.stocks_dir
            is_exrights = False

        for stock, new_data in tqdm(incremental_data.items(), desc="合并"):
            stock_file = target_dir / "{}.br".format(stock)

            if not stock_file.exists():
                print("\n警告：股票 {} 不存在，跳过".format(stock))
                continue

            # 读取现有数据
            with open(stock_file, 'rb') as f:
                compressed = f.read()
                decompressed = brotli.decompress(compressed)
                stock_data = json.loads(decompressed.decode('utf-8'))

            if is_exrights:
                # 更新除权数据（完全替换）
                stock_data['exrights_events'] = new_data['exrights_events']
                stock_data['adj_factors'] = new_data['adj_factors']
                stock_data['dividends'] = new_data['dividends']
            else:
                # 合并价格记录（去重）
                existing_dates = {r['date'] for r in stock_data['data']}
                if new_data['date'] not in existing_dates:
                    stock_data['data'].append(new_data)
                    stock_data['data'].sort(key=lambda x: x['date'])

            # 重新压缩保存
            json_str = json.dumps(stock_data, ensure_ascii=False, separators=(',', ':'))
            compressed = brotli.compress(json_str.encode('utf-8'),
                                        quality=self.compression_quality)
            stock_file.write_bytes(compressed)


# CLI命令行工具
def unpack_command(download_dir, data_dir=None):
    """解包命令

    Args:
        download_dir: 下载目录路径
        data_dir: 数据目录路径，默认为./data
    """
    if data_dir is None:
        from simtradelab.utils.paths import DATA_PATH
        data_dir = DATA_PATH

    unpacker = DataUnpacker(data_dir)
    unpacker.unpack_all(download_dir)


def merge_command(incremental_file, data_dir=None, compression_quality=6, num_workers=1):
    """合并增量数据命令

    Args:
        incremental_file: 增量数据文件路径
        data_dir: 数据目录路径
        compression_quality: 压缩质量
        num_workers: 并行进程数
    """
    if data_dir is None:
        from simtradelab.utils.paths import DATA_PATH
        data_dir = DATA_PATH

    merger = DataMerger(data_dir, compression_quality, num_workers)
    merger.merge_incremental(incremental_file)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法：")
        print("  python data_tools.py unpack <download_dir>")
        print("  python data_tools.py merge <incremental_file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'unpack':
        if len(sys.argv) < 3:
            print("错误：需要指定下载目录")
            sys.exit(1)
        unpack_command(sys.argv[2])

    elif command == 'merge':
        if len(sys.argv) < 3:
            print("错误：需要指定增量文件")
            sys.exit(1)
        merge_command(sys.argv[2])

    else:
        print("未知命令: {}".format(command))
        sys.exit(1)
