"""
Celery health monitoring and diagnostics.

Features:
- Health check endpoints
- Worker status monitoring
- Queue depth monitoring
- Task failure tracking
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from prometheus_client import Gauge

from app.core.celery.celery_client import celery_app  # Using centralized client
from app.core.redis.rate_limit import service_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)

# Prometheus metrics
CELERY_WORKERS = Gauge("celery_active_workers", "Number of active Celery workers")
CELERY_TASKS = Gauge("celery_pending_tasks", "Number of pending tasks in queue")


async def check_celery_health() -> Dict[str, Any]:
    """
    Rate-limited Celery health check using service rate limiter
    """
    if not await service_rate_limit(
        key="celery_health", limit=1, window=5, endpoint="celery_health"
    ):
        raise HTTPException(
            status_code=429, detail="Celery health checks limited to 1 per 5 seconds"
        )

    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats() or {}

        return {
            "status": "healthy" if stats else "degraded",
            "active_workers": len(stats),
            "queues": celery_app.conf.task_queues,
            "metrics": {
                "task_count": sum(len(queue) for queue in inspect.active().values()),
                "latency": inspect.ping(),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Celery health check failed: {str(e)}"
        )


@router.get("/health/celery")
async def celery_health():
    """Check Celery worker health and queue status"""
    try:
        result = await check_celery_health()
        active_workers = result["active_workers"]
        CELERY_WORKERS.set(active_workers)

        if active_workers == 0:
            raise HTTPException(status_code=503, detail="No active Celery workers")

        return result
    except Exception as e:
        logger.error(f"Celery health check error: {str(e)}")
        raise HTTPException(
            status_code=503, detail=f"Celery connection error: {str(e)}"
        )
