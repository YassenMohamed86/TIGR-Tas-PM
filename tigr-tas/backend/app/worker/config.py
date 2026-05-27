from app.config.settings import get_settings

settings = get_settings()

celery_config = {
    "broker_url": str(settings.celery_broker_url),
    "result_backend": str(settings.celery_result_backend),
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_acks_late": True,
    "worker_prefetch_multiplier": 1,
    "task_time_limit": 3600,
    "task_soft_time_limit": 3300,
    "result_expires": 86400,
}
