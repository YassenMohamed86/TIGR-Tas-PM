from celery import Celery
from app.worker.config import celery_config

celery_app = Celery("tigr_tas")

celery_app.conf.update(celery_config)

# Autodiscover tasks from the tasks package
celery_app.autodiscover_tasks(["app.worker.tasks"])
