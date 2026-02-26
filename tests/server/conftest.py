import pytest


@pytest.fixture(autouse=True)
def reset_task_manager():
    """每个测试前清空 task_manager 状态，避免测试间污染。"""
    from simtradelab.server.routers.backtest import task_manager
    task_manager._tasks.clear()
    yield
    task_manager._tasks.clear()
