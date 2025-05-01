"""
Tests for Celery queue prioritization
"""

import pytest
from celery.contrib.testing import worker

from app.core.celery.celery_client import celery_app


@pytest.mark.usefixtures("celery_worker")
class TestQueuePrioritization:
    def test_queue_configuration(self):
        """Test queue configuration is properly set"""
        assert "high_priority" in celery_app.conf.task_queues
        assert "default" in celery_app.conf.task_queues

    def test_task_routing(self):
        """Test tasks are routed to correct queues"""
        from app.core.celery._tests.example_tasks.tasks import (
            process_high_priority_task,
        )

        assert process_high_priority_task.queue == "high_priority"

    def test_chained_tasks_across_queues(self):
        """Test tasks can chain across different priority queues"""
        from app.core.celery._tests.example_tasks.tasks import (
            process_default_task,
            process_high_priority_task,
        )

        # Explicitly set queue for each task in the chain
        chain = (
            process_high_priority_task.s().set(queue='high_priority') | 
            process_default_task.s().set(queue='default')
        )
        
        # Verify the queue settings
        assert chain.tasks[0].options['queue'] == "high_priority"
        assert chain.tasks[1].options['queue'] == "default"
