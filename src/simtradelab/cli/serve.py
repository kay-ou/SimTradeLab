from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="SimTradeLab API Server")
    parser.add_argument("command", nargs="?", default="serve",
                        choices=["serve"], help="子命令")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true",
                        help="开发模式自动重载")
    parser.add_argument("--data-path", default=None, help="数据目录路径")
    parser.add_argument("--strategies-path", default=None, help="策略目录路径")
    args = parser.parse_args()

    if args.data_path:
        os.environ['SIMTRADELAB_DATA_PATH'] = str(Path(args.data_path).resolve())
    if args.strategies_path:
        os.environ['SIMTRADELAB_STRATEGIES_PATH'] = str(Path(args.strategies_path).resolve())

    try:
        import uvicorn
    except ImportError:
        raise SystemExit(
            "缺少 server 依赖，请运行: pip install simtradelab[server]"
        )

    print("SimTradeLab Server starting on {}:{}".format(args.host, args.port))
    uvicorn.run(
        "simtradelab.server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
