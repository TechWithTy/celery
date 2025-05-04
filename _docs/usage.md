# Celery Decorators & Index Usage Guide

This guide explains how to use the production-ready Celery decorators and task management utilities provided in this project.

---

## 1. Registering Tasks with `@celery_task`

Use the `@celery_task` decorator to register your Python function as a Celery task with all production defaults (timeouts, retries, queue, priority, etc.).

### Example
```python
from app.core.celery.decorators import celery_task, task_with_retry

@celery_task(name="myapp.tasks.example", queue="high_priority", max_retries=5)
@task_with_retry(max_retries=5)
def example_task(self, arg1, arg2):
    """A robust Celery task."""
    # Task logic here
    pass
```
- `name`: Full task name for Celery routing (recommended: module-style).
- `queue`: Target queue (e.g., `default`, `high_priority`).
- `max_retries`, `soft_time_limit`, `time_limit`, `priority`: All production-safe defaults.

### Automatic Retry
Use `@task_with_retry` to wrap your task with automatic retry and error logging. This ensures failed tasks are retried and errors are logged.

---

## 2. Creating Tasks Programmatically with `create_task`

For dynamic or programmatic task creation, use the `create_task` function from `index.py`.

### Example
```python
from app.core.celery.index import create_task

task_id = create_task(
    task_name="myapp.tasks.example",
    args=["foo", "bar"],
    kwargs={"baz": 123},
    queue="high_priority",
    priority=9
)
print(f"Enqueued Celery task with ID: {task_id}")
```
- Handles queue, priority, retry, and timeout settings.
- Returns the task ID for tracking.

---

## 3. Checking Task Status

Use the `get_task_status` utility from `index.py` to get detailed task status (state, result, traceback, etc.):

```python
from app.core.celery.index import get_task_status

status = get_task_status(task_id)
print(status)
```

---

## 4. Health Checks

Check worker health programmatically:
```python
from app.core.celery.health_checks import check_celery_health

health = await check_celery_health()
print(health)
```

---

## 5. Best Practices
- Always use JSON-serializable arguments and return values.
- Prefer atomic, idempotent tasks for reliability.
- Use queues and priorities to control throughput and latency.
- Monitor tasks and workers using logs and health checks.
- Use `@task_with_retry` for robust error handling and automatic retries.

---

For more details, see the code in `decorators.py`, `index.py`, and the Celery config files.
