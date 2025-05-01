"""
Celery tasks for lead_ignite_backend
"""

from celery.exceptions import SoftTimeLimitExceeded
from celery import shared_task
import time
from typing import Any


# Existing production tasks
@shared_task(bind=True, queue="high_priority")
def process_high_priority_task(self, *args, **kwargs):
    """Example high priority task"""
    return {"status": "success", "queue": "high_priority"}


@shared_task(bind=True, queue="default")
def process_default_task(self, *args, **kwargs):
    """Example default priority task"""
    return {"status": "success", "queue": "default"}


# Test tasks for task management testing
@shared_task(bind=True, name="app.core.celery.tasks.example_task")
def example_task(self, *args, **kwargs) -> dict[str, Any]:
    """Basic example task that returns inputs"""
    return {"status": "SUCCESS", "args": args, "kwargs": kwargs}


@shared_task(bind=True, name="app.core.celery.tasks.failing_task")
def failing_task(self, *args, **kwargs) -> None:
    """Task that always fails for testing error handling"""
    raise ValueError("Intentional task failure")


@shared_task(
    bind=True,
    name="app.core.celery.tasks.retry_task",
    max_retries=3,
    default_retry_delay=1,
)
def retry_task(self, *args, **kwargs) -> dict[str, Any]:
    """Task that retries before succeeding"""
    try:
        if not kwargs.get("force_success", False):
            raise ValueError("Retry required")
    except ValueError as exc:
        self.retry(exc=exc)

    return {"status": "SUCCESS_AFTER_RETRY"}


@shared_task(
    bind=True,
    name="app.core.celery.tasks.long_running_task",
    time_limit=1,
    soft_time_limit=0.5,
)
def long_running_task(self, *args, **kwargs) -> None:
    """Task that intentionally exceeds time limits"""
    # Test control flag - when True, bypass timeout behavior
    if kwargs.get("_test_mode", False):
        return

    # In eager mode (testing), simulate timeout after short delay
    if self.request.is_eager:
        time.sleep(0.1)
        raise SoftTimeLimitExceeded("Simulated timeout for testing")

    # Normal execution path for worker mode
    start = time.time()
    while time.time() - start < 2:
        time.sleep(0.1)
