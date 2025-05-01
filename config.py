"""
Production Celery configuration with monitoring and queue prioritization support.
"""

from app.core.config import settings
from datetime import timedelta

# Core Settings
CELERY_BROKER_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

# Queue Configuration
CELERY_DEFAULT_QUEUE = 'default'
CELERY_HIGH_PRIORITY_QUEUE = 'high_priority'
CELERY_DEAD_LETTER_QUEUE = 'dead_letters'

# Worker Settings
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Fair dispatch
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Prevent memory leaks

# Task Settings
CELERY_TASK_SOFT_TIME_LIMIT = 30  # seconds
CELERY_TASK_HARD_TIME_LIMIT = 60  # seconds
CELERY_TASK_ACKS_LATE = True  # Prevent lost tasks
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True  # For monitoring

# Retry Policy
CELERY_MAX_RETRIES = 3
CELERY_RETRY_DELAY = timedelta(minutes=1).total_seconds()
CELERY_RETRY_BACKOFF = True
CELERY_RETRY_JITTER = True

# Monitoring
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False  # Better logging

# Health Check
CELERY_HEARTBEAT_INTERVAL = 10  # seconds
CELERY_HEARTBEAT_TIMEOUT = 30  # seconds
