"""
Celery client configuration for production environments.
"""
import logging
from typing import Any, dict, Optional

from celery import Celery
from celery.signals import after_task_publish, task_failure, task_success

from .config import (
    CELERY_BROKER_URL,
    CELERY_DEAD_LETTER_QUEUE,
    CELERY_DEFAULT_QUEUE,
    CELERY_HIGH_PRIORITY_QUEUE,
    CELERY_MAX_RETRIES,
    CELERY_RESULT_BACKEND,
    CELERY_TASK_HARD_TIME_LIMIT,
    CELERY_TASK_SOFT_TIME_LIMIT,
    CELERY_WORKER_CONCURRENCY,
    settings,
)

# Configure structured logging
logger = logging.getLogger(__name__)

# Get configuration from environment variables
broker_url = f"redis://{f':{settings.REDIS_PASSWORD}@' if settings.REDIS_PASSWORD else ''}{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
result_backend = f"redis://{f':{settings.REDIS_PASSWORD}@' if settings.REDIS_PASSWORD else ''}{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

celery_app = Celery(
    __name__,
    broker=broker_url,
    backend=result_backend,
    include=["app.core.celery.tasks"],
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10
)

# Production configuration
celery_app.conf.update(
    # Worker settings
    worker_concurrency=CELERY_WORKER_CONCURRENCY,
    worker_prefetch_multiplier=1,  # Fair task distribution
    
    # Task settings
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Time limits
    task_soft_time_limit=CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=CELERY_TASK_HARD_TIME_LIMIT,
    
    # Reliability
    task_acks_late=True,  # Tasks acknowledged after execution
    task_reject_on_worker_lost=True,  # Redeliver if worker fails
    task_track_started=True,  # Track when task starts
    
    # Retry policy
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=CELERY_MAX_RETRIES,
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Results
    result_extended=True,  # Include more task metadata
    result_expires=3600,  # Keep results for 1 hour
    
    # Security
    worker_send_task_events=True,
    task_send_sent_event=True
)

# Production queue configuration
celery_app.conf.task_queues = {
    CELERY_HIGH_PRIORITY_QUEUE: {
        'exchange': CELERY_HIGH_PRIORITY_QUEUE,
        'routing_key': CELERY_HIGH_PRIORITY_QUEUE,
        'queue_arguments': {'x-max-priority': 10}
    },
    CELERY_DEFAULT_QUEUE: {
        'exchange': CELERY_DEFAULT_QUEUE,
        'routing_key': CELERY_DEFAULT_QUEUE
    },
    CELERY_DEAD_LETTER_QUEUE: {
        'exchange': CELERY_DEAD_LETTER_QUEUE,
        'routing_key': CELERY_DEAD_LETTER_QUEUE,
        'queue_arguments': {
            'x-dead-letter-exchange': CELERY_DEFAULT_QUEUE,
            'x-message-ttl': 86400000  # 1 day in ms
        }
    }
}

# Signal handlers
@after_task_publish.connect
def task_sent_handler(sender=None, headers=None, body=None, **kwargs):
    """Log when a task is published to the queue."""
    logger.info(f"Task {headers['id']} sent to queue")

@task_failure.connect
def on_task_failure(task_id, exception, args, kwargs, traceback, einfo, **kw):
    logger.error(f"Task failed: {task_id}", exc_info=exception)

@task_success.connect
def on_task_success(result, **kwargs):
    logger.info(f"Task succeeded: {result.task_id}")

# Health check endpoint
def health_check() -> dict[str, Any]:
    """Return Celery worker health status"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats() or {}
        return {
            "status": "OK",
            "active_workers": len(stats),
            "queues": celery_app.control.broadcast('get_queues')
        }
    except Exception as e:
        logger.error("Health check failed", exc_info=e)
        return {"status": "UNHEALTHY", "error": str(e)}

# Health check task
@celery_app.task(bind=True, name='health_check')
def health_check_task(self) -> dict:
    """Health check task for monitoring."""
    return {
        'status': 'OK',
        'worker': self.request.hostname,
        'timestamp': self.request.timestamp
    }
