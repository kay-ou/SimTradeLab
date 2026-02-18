# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

a = Analysis(
    [str(Path('../src/simtradelab/cli/serve.py').resolve())],
    pathex=[str(Path('../src').resolve())],
    binaries=[],
    datas=[
        (str(Path('../data').resolve()), 'data'),
    ],
    hiddenimports=[
        'simtradelab.server.main',
        'simtradelab.server.routers.strategies',
        'simtradelab.server.routers.backtest',
        'simtradelab.server.core.task_manager',
        'simtradelab.server.core.log_streamer',
        'simtradelab.server.core.runner_thread',
        'simtradelab.server.schemas',
        'simtradelab.cli.serve',
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
