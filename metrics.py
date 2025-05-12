"""
Celery-specific Prometheus metrics for tracking task execution, success, failure, and latency.
"""
from prometheus_client import Counter, Histogram
from app.core.prometheus.metrics import get_metric_registry

# Singleton pattern for metrics
_celery_task_count = None
_celery_task_latency = None
_celery_task_success = None
_celery_task_failure = None


def get_celery_task_count():
    global _celery_task_count
    if _celery_task_count is None:
        _celery_task_count = Counter(
            'celery_task_count_total',
            'Total number of Celery tasks executed',
            registry=get_metric_registry()
        )
    return _celery_task_count


def get_celery_task_latency():
    global _celery_task_latency
    if _celery_task_latency is None:
        _celery_task_latency = Histogram(
            'celery_task_latency_seconds',
            'Celery task execution latency in seconds',
            registry=get_metric_registry()
        )
    return _celery_task_latency


def get_celery_task_success():
    global _celery_task_success
    if _celery_task_success is None:
        _celery_task_success = Counter(
            'celery_task_success_total',
            'Total number of successful Celery tasks',
            registry=get_metric_registry()
        )
    return _celery_task_success


def get_celery_task_failure():
    global _celery_task_failure
    if _celery_task_failure is None:
        _celery_task_failure = Counter(
            'celery_task_failure_total',
            'Total number of failed Celery tasks',
            registry=get_metric_registry()
        )
    return _celery_task_failure
