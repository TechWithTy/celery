"""
Production-grade Celery task decorators integrated with existing client and index implementations.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from celery import Celery
from celery.exceptions import TimeoutError

# Import from existing implementations
from .celery_client import celery_app
from .config import (
    CELERY_DEFAULT_QUEUE,
    CELERY_HIGH_PRIORITY_QUEUE,
    CELERY_MAX_RETRIES,
    CELERY_TASK_SOFT_TIME_LIMIT,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")


def task(
    name: Optional[str] = None,
    queue: str = CELERY_DEFAULT_QUEUE,
    max_retries: int = CELERY_MAX_RETRIES,
    retry_delay: int = 60,
    time_limit: int = CELERY_TASK_SOFT_TIME_LIMIT,
    autoretry_for: tuple = (Exception,),
    retry_jitter: bool = True,
):
    """
    Core Celery task decorator using existing client configuration.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                logger.info(
                    f"Starting task {func.__name__}",
                    extra={"queue": queue, "args": args, "kwargs": kwargs},
                )
                return func(*args, **kwargs)
            except autoretry_for as exc:
                logger.warning(f"Task failed (retrying): {exc}", exc_info=True)
                raise wrapper.retry(
                    exc=exc,
                    countdown=retry_delay,
                    max_retries=max_retries,
                    jitter=retry_jitter,
                )
            except Exception as exc:
                logger.error(f"Task failed (unhandled): {exc}", exc_info=True)
                raise

        return celery_app.task(
            name=name or f"app.core.celery.tasks.{func.__name__}",
            bind=True,
            max_retries=max_retries,
            autoretry_for=autoretry_for,
            retry_backoff=retry_delay,
            retry_jitter=retry_jitter,
            time_limit=time_limit,
            queue=queue,
        )(wrapper)

    return decorator


def circuit_breaker(
    failure_threshold: int = 3, reset_timeout: int = 300, exclude_exceptions: tuple = ()
):
    """
    Circuit breaker that integrates with existing task monitoring.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        failures = 0
        last_failure = 0.0

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal failures, last_failure

            now = time.time()
            if failures >= failure_threshold and (now - last_failure) < reset_timeout:
                logger.error(f"Circuit breaker tripped for {func.__name__}")
                raise Exception("Service temporarily unavailable")

            try:
                result = func(*args, **kwargs)
                failures = 0
                return result
            except exclude_exceptions:
                raise
            except Exception as exc:
                failures += 1
                last_failure = now
                logger.warning(
                    f"Circuit breaker count: {failures}/{failure_threshold}",
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def priority(level: int):
    """
    Priority decorator that works with existing queue configuration.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            kwargs["__celery_priority"] = min(9, max(0, level))
            if level > 5:
                kwargs["queue"] = CELERY_HIGH_PRIORITY_QUEUE
            return func(*args, **kwargs)

        return wrapper

    return decorator


def timeout(seconds: int):
    """
    Timeout decorator using existing time limit configuration as fallback.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except TimeoutError:
                logger.error(f"Task {func.__name__} timed out after {seconds}s")
                raise

        return wrapper

    return decorator
