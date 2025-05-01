"""
Tests for Celery health monitoring functionality
"""
pytest_plugins = ('pytest_asyncio',)

from unittest.mock import patch, MagicMock

import pytest
from app.core.celery.celery_client import celery_app
from app.core.celery.health_checks import check_celery_health

@pytest.mark.asyncio
class TestHealthChecks:
    @patch("app.core.redis.rate_limit.service_rate_limit", return_value=True)
    async def test_health_check_success(self, mock_rate_limit):
        """Test health check returns healthy status."""
        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = {"worker1": {"status": "active"}}
        
        with patch.object(celery_app.control, "inspect", return_value=mock_inspect):
            result = await check_celery_health()
            assert result["status"] == "healthy"

    @patch("app.core.redis.rate_limit.service_rate_limit", return_value=True)
    async def test_health_check_failure(self, mock_rate_limit):
        """Test health check returns unhealthy status when no workers."""
        mock_inspect = MagicMock()
        mock_inspect.stats.return_value = None
        
        with patch.object(celery_app.control, "inspect", return_value=mock_inspect):
            result = await check_celery_health()
            assert result["status"] == "unhealthy"

    @patch("app.core.redis.rate_limit.service_rate_limit", return_value=True)
    async def test_health_check_exception(self, mock_rate_limit):
        """Test health check handles exceptions."""
        mock_inspect = MagicMock()
        mock_inspect.stats.side_effect = Exception("Connection error")
        
        with patch.object(celery_app.control, "inspect", return_value=mock_inspect):
            result = await check_celery_health()
            assert result["status"] == "error"
