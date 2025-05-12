"""
Celery decorators for production task registration, retry, and monitoring.
Leverages celery_app from celery_client and production defaults from index.py.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

from celery import Task

from app.core.celery.client import celery_app
from app.core.celery.index import CELERY_DEFAULT_QUEUE, CELERY_TASK_SOFT_TIME_LIMIT
from app.core.celery.metrics import get_celery_task_count, get_celery_task_latency
from app.core.telemetry.client import TelemetryClient

logger = logging.getLogger(__name__)
telemetry = TelemetryClient(service_name="celery_tasks")


def celery_task(
    name: str | None,
    queue: str = CELERY_DEFAULT_QUEUE,
    soft_time_limit: int = CELERY_TASK_SOFT_TIME_LIMIT,
    time_limit: int | None = None,
    max_retries: int = 3,
    priority: int = 5,
    **options,
):
    """
    Decorator to register a function as a Celery task with production defaults.
    Usage:
        @celery_task(name="my.task", queue="high_priority")
        def my_task(...): ...
    """

    def decorator(func: Callable):
        task_name = name or func.__name__
        # Fallbacks for timeouts
        fallback_soft_time_limit = soft_time_limit if soft_time_limit is not None else 60
        fallback_time_limit = time_limit if time_limit is not None else fallback_soft_time_limit * 2
        base_options = {
            "name": task_name,
            "queue": queue,
            "soft_time_limit": fallback_soft_time_limit,
            "time_limit": fallback_time_limit,
            "max_retries": max_retries,
            "priority": priority,
            **options,
        }

        # Wrap the task function with telemetry and metrics
        @celery_app.task(**base_options)
        @wraps(func)
        def task_wrapper(self: Task, *args, **kwargs):
            with telemetry.span_celery_operation("execute", {"task_name": task_name}):
                start = time.time()
                try:
                    result = func(self, *args, **kwargs)
                    duration = time.time() - start
                    get_celery_task_latency().labels(task_name=task_name).observe(duration)
                    get_celery_task_count().labels(task_name=task_name, status="success").inc()
                    return result
                except Exception as exc:
                    duration = time.time() - start
                    get_celery_task_latency().labels(task_name=task_name).observe(duration)
                    get_celery_task_count().labels(task_name=task_name, status="failure").inc()
                    raise

        celery_task_obj = task_wrapper
        return celery_task_obj

    return decorator


def task_with_retry(max_retries: int = 3, default_retry_delay: int = 60):
    """
    Decorator to wrap a Celery task with automatic retry and error logging.
    Usage:
        @task_with_retry(max_retries=5)
        def my_task(...): ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self: Task, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                logger.error(f"Task {self.name} failed: {exc}")
                raise self.retry(
                    exc=exc, max_retries=max_retries, countdown=default_retry_delay
                )

        return wrapper

    return decorator
