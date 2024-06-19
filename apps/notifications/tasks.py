from celery import shared_task

from common.decorators import singleton_task
from notifications.models import Notification


@shared_task
@singleton_task(timeout=32)
def notify():
    for notification in Notification.objects.filter(
        notified=False, transaction__related_proj__notification_failed_times__lt=32
    )[:4]:
        notification_res = False

        try:
            notification_res = notification.notify()
        finally:
            if not notification_res:
                notification.transaction.related_proj.notification_failed_times += 1
                notification.transaction.related_proj.save()
