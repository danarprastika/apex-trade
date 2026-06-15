from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.workers.send_notification")
def send_notification(notification_id: str):
    return {"notification_id": notification_id, "status": "stub"}
