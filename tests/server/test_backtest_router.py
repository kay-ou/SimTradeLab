import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from simtradelab.server.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_run_backtest_returns_task_id(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert isinstance(data["task_id"], str)


@pytest.mark.asyncio
async def test_get_status_after_run(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        run_resp = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
        task_id = run_resp.json()["task_id"]
        status_resp = await client.get("/backtest/{}/status".format(task_id))
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["task_id"] == task_id
    assert data["status"] in ("pending", "running", "finished", "failed")


@pytest.mark.asyncio
async def test_get_status_nonexistent_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/backtest/nonexistent/status")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_run_two_concurrent_backtests(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
        task_id = r1.json()["task_id"]
        from simtradelab.server.routers.backtest import task_manager
        task_manager.mark_running(task_id)
        r2 = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
    assert r2.status_code == 409
