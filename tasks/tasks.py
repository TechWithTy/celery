"""
Celery tasks for lead_ignite_backend
"""
import time
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery.decorators import celery_task
from app.core.telemetry.decorators import (
    measure_performance,
    trace_function,
    track_errors,
)


# Existing production tasks
@celery_task(queue='high_priority')
@trace_function()
@track_errors
@measure_performance(threshold_ms=250)
def process_high_priority_task(*args, **kwargs):
    """Example high priority task"""
    return {"status": "success", "queue": "high_priority"}

@celery_task(queue='default')
@trace_function()
@track_errors
@measure_performance(threshold_ms=250)
def process_default_task(*args, **kwargs):
    """Example default priority task"""
    return {"status": "success", "queue": "default"}

# Test tasks for task management testing
@celery_task(name="app.core.celery.tasks.example_task")
@trace_function()
@track_errors
@measure_performance(threshold_ms=250)
def example_task(*args, **kwargs) -> dict[str, Any]:
    """Basic example task that returns inputs"""
    return {
        "status": "SUCCESS",
        "args": args,
        "kwargs": kwargs
    }

@celery_task(name="app.core.celery.tasks.failing_task")
@trace_function()
@track_errors
@measure_performance(threshold_ms=250)
def failing_task(*args, **kwargs) -> None:
    """Task that always fails for testing error handling"""
    raise ValueError("Intentional task failure")

@celery_task(name="app.core.celery.tasks.retry_task", max_retries=3, priority=5)
@trace_function()
@track_errors
@measure_performance(threshold_ms=250)
def retry_task(*args, **kwargs) -> dict[str, Any]:
    """Task that retries before succeeding"""
    from celery import current_task
    try:
        if not kwargs.get('force_success', False):
            raise ValueError("Retry required")
    except ValueError as exc:
        current_task.retry(exc=exc)
    return {"status": "SUCCESS_AFTER_RETRY"}

@celery_task(name="app.core.celery.tasks.long_running_task", time_limit=1, soft_time_limit=0.5)
@trace_function()
@track_errors
@measure_performance(threshold_ms=250)
def long_running_task(*args, **kwargs) -> None:
    """Task that intentionally exceeds time limits"""
    from celery import current_task
    # Test control flag - when True, bypass timeout behavior
    if kwargs.get('_test_mode', False):
        return
    # In eager mode (testing), simulate timeout after short delay
    if getattr(current_task.request, 'is_eager', False):
        time.sleep(0.1)
        raise SoftTimeLimitExceeded('Simulated timeout for testing')
    # Normal execution path for worker mode
    start = time.time()
    while time.time() - start < 2:
        time.sleep(0.1)
