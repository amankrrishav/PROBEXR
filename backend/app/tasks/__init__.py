"""
Background task queue — lightweight asyncio-based task runner.

For production scale-out, replace with Celery/Dramatiq by:
  1. Install: pip install celery[redis]
  2. Configure broker: CELERY_BROKER_URL = redis://...
  3. Move task functions here and decorate with @celery_app.task
  4. Run workers: celery -A app.tasks worker --loglevel=info

Current implementation uses asyncio.create_task() for fire-and-forget
background work (email sending, etc.) which is sufficient for
single-process deployments.
"""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)

# Registry of background tasks for monitoring
_active_tasks: set[asyncio.Task[Any]] = set()


def fire_and_forget(coro: Coroutine[Any, Any, Any], *, name: str = "background") -> None:
    """Schedule a coroutine as a background task.

    The task runs concurrently without blocking the request handler.
    Errors are logged but never propagated to the caller.
    """
    task = asyncio.create_task(coro, name=name)
    _active_tasks.add(task)

    def _on_done(t: asyncio.Task[Any]) -> None:
        _active_tasks.discard(t)
        if t.cancelled():
            logger.info("Background task '%s' was cancelled", name)
        elif exc := t.exception():
            logger.error("Background task '%s' failed: %s", name, exc, exc_info=exc)
        else:
            logger.debug("Background task '%s' completed", name)

    task.add_done_callback(_on_done)


def active_task_count() -> int:
    """Return the number of currently running background tasks."""
    return len(_active_tasks)
