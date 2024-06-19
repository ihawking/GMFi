import os

import celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GMFi.settings")

app = celery.Celery("GMFi")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "notify": {
        "task": "notifications.tasks.notify",
        "schedule": 1,
    },
    "gather_invoices": {
        "task": "invoices.tasks.gather_invoices",
        "schedule": 1,
    },
    "transact_platform_transactions": {
        "task": "chains.tasks.transact_platform_transactions",
        "schedule": 1,
    },
    "backend_cleanup": {
        "task": "celery.backend_cleanup",
        "schedule": crontab(hour="4", minute="0", day_of_week="1"),
    },
}
