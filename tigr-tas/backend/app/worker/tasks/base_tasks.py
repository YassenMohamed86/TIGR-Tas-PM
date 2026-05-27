from app.worker.celery_app import celery_app

@celery_app.task(bind=True, name="health_check")
def health_check_task(self) -> dict:
    return {"status": "ok", "worker_id": self.request.id}
