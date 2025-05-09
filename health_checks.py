"""
Celery health monitoring functionality
"""
from typing , Any

from app.core.celery.celery_client import celery_app

async def check_celery_health() -> dict[str, Any]:
    """
    Check Celery worker health status
    Returns:
        dict: Health status with keys: status, workers, error (if applicable)
    """
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return {
                "status": "unhealthy",
                "error": "No active workers found"
            }
            
        return {
            "status": "healthy",
            "workers": len(stats),
            "details": {"workers": list(stats.keys())}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
