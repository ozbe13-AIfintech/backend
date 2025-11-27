from celery import Celery

celery = Celery(
    "ai_fintech", broker="redis://redis:6379/0", backend="redis://redis:6379/0"
)


@celery.task
def test_task():
    return "Celery is working!"
