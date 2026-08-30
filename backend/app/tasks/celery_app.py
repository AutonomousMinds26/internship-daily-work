import os
import logging
from typing import Any, Callable
from app.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery

    celery_app = Celery(
        "recruiter_ai_worker",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.recruitment_tasks"]
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        task_soft_time_limit=240,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_routes={
            "app.tasks.recruitment_tasks.process_resume_task": {"queue": "resumes"},
            "app.tasks.recruitment_tasks.bulk_screening_task": {"queue": "screening"},
            "app.tasks.recruitment_tasks.send_assessment_task": {"queue": "assessments"},
            "app.tasks.recruitment_tasks.send_notification_email_task": {"queue": "notifications"},
            "app.tasks.recruitment_tasks.run_background_verification_task": {"queue": "verifications"},
            "app.tasks.recruitment_tasks.aggregate_analytics_daily_task": {"queue": "analytics"},
        }
    )
except ImportError:
    logger.info("Celery library not installed in local environment. Using Fallback Task Runner.")

    class MockTaskWrapper:
        def __init__(self, func: Callable, bind: bool = False):
            self.func = func
            self.bind = bind

        def __call__(self, *args, **kwargs):
            if self.bind:
                return self.func(self, *args, **kwargs)
            return self.func(*args, **kwargs)

        def delay(self, *args, **kwargs):
            return self.__call__(*args, **kwargs)

        def retry(self, exc=None, **kwargs):
            if exc:
                raise exc
            return None

    class MockCelery:
        def __init__(self, *args, **kwargs):
            self.conf = {}

        def task(self, *args, **kwargs):
            bind = kwargs.get("bind", False)
            def decorator(f):
                return MockTaskWrapper(f, bind=bind)
            if len(args) == 1 and callable(args[0]):
                return MockTaskWrapper(args[0], bind=False)
            return decorator

    celery_app = MockCelery()


def dispatch_async_task(task_func, *args, **kwargs):
    """
    Safely dispatches a Celery task asynchronously.
    If Celery/Redis is unavailable or in mock/test mode, executes synchronously
    to guarantee zero disruption in local development or test suites.
    """
    if os.getenv("CELERY_ALWAYS_EAGER", "false").lower() in ("true", "1", "yes") or settings.USE_MOCK_APIS:
        try:
            return task_func.delay(*args, **kwargs)
        except Exception as e:
            logger.info(f"Broker not reachable ({str(e)}). Running task synchronously.")
            return task_func(*args, **kwargs)
    else:
        try:
            return task_func.delay(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Failed to enqueue async task ({str(e)}). Falling back to sync execution.")
            return task_func(*args, **kwargs)
