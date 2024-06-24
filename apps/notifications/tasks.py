from celery import shared_task

from common.decorators import singleton_task
from notifications.models import Notification
from globals.models import Project


@shared_task
@singleton_task(timeout=32)
def notify():
    proj = Project.objects.get(pk=1)
    if proj.notification_failed_times > 32:
        return

    for notification in Notification.objects.filter(notified=False)[:4]:
        notification_res = False

        try:
            notification_res = notification.notify()
        finally:
            if not notification_res:
                proj.notification_failed_times += 1
                proj.save()
