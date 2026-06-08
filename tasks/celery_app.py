from celery import Celery
import os

# Simplified for the Flask prototype
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery("tigr_tas", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    result_expires=86400,
    task_default_queue="default",
    task_routes={
        "tasks.scan_tasks.*": {"queue": "default"},
        "tasks.offtarget_tasks.*": {"queue": "long_running"},
        "tasks.oracle_tasks.*": {"queue": "high_priority"},
        "tasks.export_tasks.*": {"queue": "default"},
    },
    task_max_retries=3,
    task_default_retry_delay=60,
)
