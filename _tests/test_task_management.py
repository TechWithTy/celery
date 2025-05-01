import pytest
from billiard.exceptions import SoftTimeLimitExceeded
from celery import exceptions as celery_exceptions

from app.core.celery._tests.example_tasks.tasks import (
    example_task,
    failing_task,
    long_running_task,
    retry_task,
)


class TestTaskManagement:
    """Test suite for task management functionality"""

    def test_create_task(self, celery_app):
        """Test task creation"""
        result = example_task.delay()
        assert result.id is not None
        # In eager mode, task completes immediately
        assert result.status == "SUCCESS"

    def test_get_task_status(self, celery_app):
        """Test task status retrieval"""
        result = example_task.delay()
        assert result.status == "SUCCESS"
        assert result.get()["status"] == "SUCCESS"

    def test_failed_task_status(self, celery_app):
        """Test that failing_task raises expected ValueError"""
        # This test PASSES when it catches the expected ValueError
        with pytest.raises(ValueError, match="Intentional task failure"):
            failing_task.delay().get(propagate=True)

    def test_async_task_execution(self, celery_app):
        """Test async task execution"""
        result = example_task.delay(1, 2)
        assert result.status == "SUCCESS"
        response = result.get()
        assert list(response["args"]) == [1, 2]

    def test_task_retry_mechanism(self, celery_app):
        """Test task retry configuration"""
        # Test retry case
        with pytest.raises(celery_exceptions.Retry):
            retry_task.delay(force_success=False).get(propagate=True)

        # Test success case
        result = retry_task.delay(force_success=True)
        assert result.status == "SUCCESS"
        assert result.get()["status"] == "SUCCESS_AFTER_RETRY"

    def test_task_timeout_handling(self, celery_app):
        """Test timeout handling with proper eager mode support"""
        from celery.signals import task_success
        from app.core.celery.celery_client import on_task_success

        task_success.disconnect(on_task_success)

        try:
            # First verify normal test mode works
            result = long_running_task.delay(_test_mode=True)
            assert result.get() is None

            # Then test timeout behavior
            if celery_app.conf.task_always_eager:
                # In eager mode, expect immediate timeout
                with pytest.raises(SoftTimeLimitExceeded):
                    long_running_task.delay().get(propagate=True)
            else:
                # In worker mode, expect timeout after delay
                result = long_running_task.delay()
                with pytest.raises(
                    (SoftTimeLimitExceeded, celery_exceptions.TimeLimitExceeded)
                ):
                    result.get(propagate=True)
                assert result.status == "FAILURE"
        finally:
            task_success.connect(on_task_success)
