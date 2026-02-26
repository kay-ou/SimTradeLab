import asyncio
import pytest
from simtradelab.server.core.task_manager import TaskManager
from simtradelab.server.schemas import RunBacktestRequest


@pytest.fixture
def manager():
    return TaskManager()


@pytest.fixture
def sample_request():
    return RunBacktestRequest(
        strategy_name="simple",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )


def test_create_task_returns_id(manager, sample_request):
    task_id = manager.create_task(sample_request)
    assert isinstance(task_id, str)
    assert len(task_id) == 8


def test_new_task_status_is_pending(manager, sample_request):
    task_id = manager.create_task(sample_request)
    task = manager.get_task(task_id)
    assert task.status == "pending"
    assert task.progress == 0.0
    assert task.result is None
    assert task.error is None


def test_get_nonexistent_task_raises(manager):
    with pytest.raises(KeyError):
        manager.get_task("nonexistent")


def test_mark_running(manager, sample_request):
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    task = manager.get_task(task_id)
    assert task.status == "running"
    assert task.started_at is not None


def test_mark_finished(manager, sample_request):
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    manager.mark_finished(task_id, result={"total_return": 0.1})
    task = manager.get_task(task_id)
    assert task.status == "finished"
    assert task.result == {"total_return": 0.1}
    assert task.finished_at is not None


def test_mark_failed(manager, sample_request):
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    manager.mark_failed(task_id, error="策略加载失败")
    task = manager.get_task(task_id)
    assert task.status == "failed"
    assert task.error == "策略加载失败"


def test_has_running_task(manager, sample_request):
    assert not manager.has_running_task()
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    assert manager.has_running_task()
