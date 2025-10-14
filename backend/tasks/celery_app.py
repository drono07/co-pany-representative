"""
Celery application configuration for website analysis platform
"""

from celery import Celery
from celery.schedules import crontab
import os
from datetime import timedelta

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "website_analysis",
    broker=REDIS_URL,
    backend=None,  # Disable result backend to avoid Redis issues
    include=["backend.tasks.celery_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "celery_tasks.run_website_analysis": {"queue": "analysis"},
        "celery_tasks.send_notification": {"queue": "notifications"},
        "celery_tasks.cleanup_old_data": {"queue": "maintenance"},
        "celery_tasks.run_content_analysis": {"queue": "analysis"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "run-scheduled-analyses": {
            "task": "celery_tasks.process_scheduled_analyses",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "cleanup-old-results": {
            "task": "celery_tasks.cleanup_old_data",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "health-check": {
            "task": "celery_tasks.health_check",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
        },
    },
)

# Task result backend settings
# Remove the problematic transport options for Redis
# celery_app.conf.result_backend_transport_options = {
#     "master_name": "mymaster",
# }

if __name__ == "__main__":
    celery_app.start()
