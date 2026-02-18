from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="SimTradeLab API Server")
    parser.add_argument("command", nargs="?", default="serve",
                        choices=["serve"], help="子命令")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true",
                        help="开发模式自动重载")
    args = parser.parse_args()

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
