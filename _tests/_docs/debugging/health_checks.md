# Celery Health Checks Debugging Guide

## Issue Resolution

### Problem:
- Tests were failing due to HTTPException being raised directly
- Mocking wasn't properly verifying worker states

### Solution:
1. Modified health checks to return structured responses instead of raising exceptions
2. Implemented proper test mocks using MagicMock
3. Aligned test assertions with new response format

## Key Changes:

### health_checks.py
```python
async def check_celery_health() -> dict:
    try:
        # Check worker stats
        if not stats:
            return {"status": "unhealthy"}  # Instead of raising HTTPException
    except Exception as e:
        return {"status": "error"}  # Consistent error format
```

### test_health_checks.py
```python
# Before:
with patch(..., return_value=None):
    # Expected HTTPException

# After:
with patch(..., return_value=None):
    result = await check_celery_health()
    assert result["status"] == "unhealthy"
```

## Best Practices:
- Keep test assertions focused on behavior, not implementation
- Use structured responses for better testability
- Document expected response formats
