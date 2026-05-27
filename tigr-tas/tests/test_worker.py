import pytest
from app.worker.tasks.base_tasks import health_check_task
from unittest.mock import MagicMock

def test_health_check_task():
    # We can invoke the task synchronously for testing
    task_mock = MagicMock()
    task_mock.request.id = "test-id"
    
    # bind=True tasks receive self as first arg. 
    # Calling it directly as a python function.
    result = health_check_task(task_mock)
    
    assert result["status"] == "ok"
    assert result["worker_id"] == "test-id"
