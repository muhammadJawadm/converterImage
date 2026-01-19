"""
Celery Application Configuration
Celery app instance for distributed task processing with Redis
"""
from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "file_converter",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Celery Configuration
celery_app.conf.update(
    # Task execution settings
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    
    # Result backend settings
    result_expires=settings.CELERY_RESULT_EXPIRES,
    result_persistent=True,
    
    # Serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    
    # Task routing - Multiple queues for different conversion types
    task_routes={
        "app.tasks.conversion_tasks.convert_pdf_to_word": {"queue": "pdf_queue"},
        "app.tasks.conversion_tasks.convert_word_to_pdf": {"queue": "office_queue"},
        "app.tasks.conversion_tasks.convert_excel_to_pdf": {"queue": "office_queue"},
        "app.tasks.conversion_tasks.convert_image_to_pdf": {"queue": "image_queue"},
        "app.tasks.conversion_tasks.convert_pdf_to_image": {"queue": "pdf_queue"},
        "app.tasks.conversion_tasks.convert_file_task": {"queue": "default"},
    },
    
    # Default queue
    task_default_queue="default",
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Enable task events for Flower monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Late acknowledgement - task acked after completion
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_default_retry_delay=60,
)

# Auto-discover tasks from tasks module
celery_app.autodiscover_tasks(['app.tasks'])

# Explicitly import tasks to ensure they're registered
from app.tasks import conversion_tasks  # noqa: F401

# Task annotations for specific configurations
celery_app.conf.task_annotations = {
    '*': {'rate_limit': '100/m'},  # Max 100 tasks per minute per task type
}


# Useful for debugging
if __name__ == "__main__":
    celery_app.start()
