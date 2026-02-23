# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# simtradelab 包全量收集（uvicorn 字符串导入无法被静态分析检测到）
simtradelab_datas, simtradelab_binaries, simtradelab_hiddenimports = collect_all('simtradelab')

a = Analysis(
    [str(Path('../src/simtradelab/cli/serve.py').resolve())],
    pathex=[str(Path('../src').resolve())],
    binaries=simtradelab_binaries,
    datas=simtradelab_datas,
    hiddenimports=simtradelab_hiddenimports + [
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'anyio',
        'anyio._backends._asyncio',
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
    ],
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
