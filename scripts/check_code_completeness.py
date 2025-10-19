#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码完成度检查脚本（便捷入口）

使用方法:
  poetry run python scripts/check_code_completeness.py --help
  poetry run python scripts/check_code_completeness.py --path src/simtradelab --output-dir reports --format both

等价于:
  poetry run python -m simtradelab.codecheck [同样参数]
"""
from simtradelab.codecheck import main


if __name__ == "__main__":
    raise SystemExit(main())
