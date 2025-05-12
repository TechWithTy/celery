"""
Test configuration for Celery health checks
"""
import os
import sys
from pathlib import Path

import pytest
from celery import Celery
from celery.contrib.testing import worker
from redis import Redis
from redis.exceptions import RedisError

from app.core.celery.celery_client import celery_app
from app.core.config import settings

# Configure test Redis connection using production settings
os.environ["REDIS_HOST"] = settings.redis.REDIS_HOST
os.environ["REDIS_PORT"] = str(settings.redis.REDIS_PORT)
os.environ["REDIS_PASSWORD"] = settings.redis.REDIS_PASSWORD
os.environ["CELERY_BROKER_URL"] = f"redis://:{settings.redis.REDIS_PASSWORD}@{settings.redis.REDIS_HOST}:{settings.redis.REDIS_PORT}/0"
os.environ["CELERY_RESULT_BACKEND"] = f"redis://:{settings.redis.REDIS_PASSWORD}@{settings.redis.REDIS_HOST}:{settings.redis.REDIS_PORT}/1"

@pytest.fixture(scope="module")
def celery_config():
    """Test Celery configuration"""
    return {
        'broker_url': f"redis://:{os.getenv('REDIS_PASSWORD')}@localhost:6379/2",
        'result_backend': f"redis://:{os.getenv('REDIS_PASSWORD')}@localhost:6379/3",
        'task_default_queue': 'default',
        'task_queues': {
            'high_priority': {
                'exchange': 'high_priority',
                'routing_key': 'high_priority'
            },
            'default': {
                'exchange': 'default',
                'routing_key': 'default'
            }
        },
        'task_routes': {
            'app.core.celery.tasks.tasks.*': {'queue': 'default'}
        },
        'imports': ['app.core.celery.tasks.tasks'],
        'task_always_eager': True,
        'task_eager_propagates': True
    }

@pytest.fixture(scope="module")
def celery_app(celery_config):
    """Create isolated test Celery app"""
    app = Celery('test_app')
    app.config_from_object(celery_config)
    return app

@pytest.fixture(scope="module")
def celery_worker(celery_app):
    """Start worker with our test app"""
    # Skip actual worker in eager mode
    yield
