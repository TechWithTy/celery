# Celery Queue Prioritization Debugging Guide

## Debugging Methodology

### 1. Isolation Testing
- Create minimal reproducible test cases
- Verify Redis connection separately
- Test queue configuration independently

### 2. Logging Setup
```python
# Add to conftest.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### 3. Step-by-Step Verification
1. Task Registration
2. Queue Binding  
3. Worker Queue Assignment
4. Task Routing Validation

## Debugging History

### Attempted Solutions
1. **Auto-discovery Disabled**  
   - Set `imports = []` in Celery config  
   - Still saw recursion during worker startup

2. **Explicit Task Registration**  
   - Manually registered tasks via `app.register_task()`  
   - Fixed some but not all recursion cases

3. **Isolated Test App**  
   - Created separate Celery app instance for testing  
   - Resolved majority of recursion issues

### Root Cause Analysis
The primary issue stemmed from:
- Circular imports between task modules
- Shared state between test and production Celery apps
- Auto-discovery attempting to load tasks recursively

### Edge Cases Identified
1. **Redis Connection Pooling**  
   - Tests failing when running in parallel  
   - Solution: Use separate Redis DB numbers  

2. **Worker Startup Timing**  
   - Intermittent failures due to worker readiness  
   - Added `perform_ping_check=False` for reliability

3. **Task Serialization**  
   - Complex args causing test failures  
   - Standardized on JSON-serializable test data

## Common Issues & Solutions

### Recursion Errors
**Symptoms**:
- Maximum recursion depth exceeded
- Tests failing during worker startup

**Solutions**:
- Use explicit task registration
- Disable auto-discovery (`imports = []`)
- Create isolated test Celery app

### Queue Mismatches
**Debugging Tools**:
```python
# Check active queues
from celery.app.control import inspect
i = inspect()
print(i.active_queues())
```

## Monitoring & Verification

### Flower Dashboard
```bash
celery -A app.core.celery.celery_client flower --port=5555
```

### Redis CLI
```bash
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD
> MONITOR  # Watch real-time queue activity
> KEYS *   # List all queues
```

## Best Practices
- Use separate Redis databases for testing
- Document all queue configurations
- Implement health checks for queue workers
