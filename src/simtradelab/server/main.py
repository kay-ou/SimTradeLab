from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simtradelab.server.routers import strategies, backtest, settings, optimizer, history, editor


def create_app() -> FastAPI:
    app = FastAPI(title="SimTradeLab Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(strategies.router)
    app.include_router(backtest.router)
    app.include_router(settings.router)
    app.include_router(optimizer.router)
    app.include_router(history.router)
    app.include_router(editor.router)
    return app


app = create_app()
