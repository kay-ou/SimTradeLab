# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
数据包解包工具
"""

from __future__ import annotations
import json
import tarfile
from pathlib import Path
from tqdm import tqdm


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
        import pandas as pd
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


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法：")
        print("  python data_tools.py unpack <download_dir>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'unpack':
        if len(sys.argv) < 3:
            print("错误：需要指定下载目录")
            sys.exit(1)
        unpack_command(sys.argv[2])
    else:
        print("未知命令: {}".format(command))
        sys.exit(1)
