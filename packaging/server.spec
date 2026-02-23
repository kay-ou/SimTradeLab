# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# SPEC 是 PyInstaller 内置变量，包含 spec 文件的完整路径
SPEC_DIR = Path(SPEC).resolve().parent
ENTRY = str((SPEC_DIR / '..' / 'src' / 'simtradelab' / 'cli' / 'serve.py').resolve())
SRC_DIR = str((SPEC_DIR / '..' / 'src').resolve())

# 将 src/ 加入分析路径，让 collect_submodules 能找到 simtradelab
sys.path.insert(0, SRC_DIR)

# 验证 server 依赖已安装
try:
    import uvicorn  # noqa: F401
    import fastapi  # noqa: F401
except ImportError as e:
    raise SystemExit(
        "构建失败：server 依赖未安装，请先运行: poetry install --extras server\n" + str(e)
    )

simtradelab_hiddenimports = collect_submodules('simtradelab')
uvicorn_hiddenimports = collect_submodules('uvicorn')
anyio_hiddenimports = collect_submodules('anyio')
fastapi_hiddenimports = collect_submodules('fastapi')
starlette_hiddenimports = collect_submodules('starlette')

a = Analysis(
    [ENTRY],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[],
    hiddenimports=(
        simtradelab_hiddenimports
        + uvicorn_hiddenimports
        + anyio_hiddenimports
        + fastapi_hiddenimports
        + starlette_hiddenimports
        + [
            'pandas',
            'numpy',
            'pyarrow',
            'pyarrow.pandas_compat',
            'joblib',
            'cachetools',
            'pydantic',
            'pydantic_core',
            'matplotlib',
            'matplotlib.backends.backend_agg',
            'h11',
            'httptools',
        ]
    ),
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'test', 'unittest'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='simtradelab-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)
