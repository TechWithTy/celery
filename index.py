"""
Production task management with prioritization and monitoring.
"""

import logging
from collections.abc import Callable
from typing import Any, Dict, List, Optional
from uuid import uuid4

from celery import result
from celery.exceptions import TimeoutError

from app.core.celery.celery_client import celery_app
from app.core.celery.config import (
    CELERY_DEFAULT_QUEUE,
    CELERY_HIGH_PRIORITY_QUEUE,
    CELERY_TASK_SOFT_TIME_LIMIT,
)

logger = logging.getLogger(__name__)

# Task state constants
PENDING = "PENDING"
STARTED = "STARTED"
PROGRESS = "PROGRESS"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
RETRYING = "RETRYING"

# Default timeout (seconds)
DEFAULT_TASK_TIMEOUT = 300


def create_task(
    task_name: str,
    args: Optional[List] = None,
    kwargs: Optional[Dict] = None,
    queue: str = CELERY_DEFAULT_QUEUE,
    priority: int = 5,
    **options
) -> str:
    """Create task with production-ready defaults"""
    options.update({
        'queue': queue,
        'priority': priority,
        'time_limit': CELERY_TASK_SOFT_TIME_LIMIT * 2,
        'soft_time_limit': CELERY_TASK_SOFT_TIME_LIMIT,
        'retry': True,
        'retry_policy': {
            'max_retries': 3,
            'interval_start': 1,
            'interval_step': 1,
            'interval_max': 5
        }
    })
    
    task = celery_app.send_task(task_name, args=args, kwargs=kwargs, **options)
    logger.info(f"Created task {task.id} in queue {queue} with priority {priority}")
    return task.id


def get_task_status(task_id: str) -> Dict[str, Any]:
    """Enhanced status check with monitoring"""
    try:
        task_result = result.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task_result.status,
            "queue": task_result.queue,
            "worker": task_result.worker,
            "date_done": task_result.date_done.isoformat() if task_result.date_done else None,
            "result": task_result.result if task_result.ready() else None,
            "traceback": task_result.traceback if task_result.failed() else None
        }
    except Exception as e:
        logger.error(f"Status check failed for {task_id}", exc_info=e)
        return {"error": str(e), "task_id": task_id}


def configure_task_retries(
    task_id: str, max_retries: int = 3, retry_delay: int = 60, retry_jitter: bool = True
) -> bool:
    """Configure retry policy for an existing task."""
    try:
        result.AsyncResult(task_id)
        if result.AsyncResult(task_id).state not in (COMPLETED, FAILED):
            # Update headers with new retry policy
            headers = getattr(result.AsyncResult(task_id), "headers", {})
            headers["retry_policy"] = {
                "max_retries": max_retries,
                "retry_delay": retry_delay,
                "retry_jitter": retry_jitter,
            }
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to configure retries for task {task_id}: {e}")
        return False


def get_queue_stats(queue: str = "default") -> Dict[str, Any]:
    """Get queue statistics including depth and worker availability."""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}

        return {
            "queue": queue,
            "active_tasks": sum(len(tasks) for tasks in active_tasks.values()),
            "scheduled_tasks": sum(len(tasks) for tasks in scheduled_tasks.values()),
            "reserved_tasks": sum(len(tasks) for tasks in reserved_tasks.values()),
            "workers": list(active_tasks.keys()),
        }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {"error": str(e)}
