import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def strategies_dir(tmp_path):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "backtest.py").write_text("def initialize(context): pass\n")
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "backtest.py").write_text("def initialize(context): pass\n")
    return tmp_path


@pytest.fixture
def app(strategies_dir, monkeypatch):
    import simtradelab.server.routers.strategies as mod
    monkeypatch.setattr(mod, "STRATEGIES_PATH", strategies_dir)
    from simtradelab.server.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_list_strategies(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/strategies")
    assert resp.status_code == 200
    names = resp.json()
    assert "alpha" in names
    assert "beta" in names


@pytest.mark.asyncio
async def test_get_strategy_source(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/strategies/alpha")
    assert resp.status_code == 200
    assert "initialize" in resp.json()["source"]


@pytest.mark.asyncio
async def test_get_nonexistent_strategy_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/strategies/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_strategy_source(app):
    new_source = "def initialize(context): context.x = 1\n"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put("/strategies/alpha", json={"name": "alpha", "source": new_source})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_strategy(app, strategies_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/strategies/new_strat", json={"name": "new_strat"})
    assert resp.status_code == 201
    assert (strategies_dir / "new_strat" / "backtest.py").exists()


@pytest.mark.asyncio
async def test_delete_strategy(app, strategies_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.delete("/strategies/beta")
    assert resp.status_code == 200
    assert not (strategies_dir / "beta").exists()
