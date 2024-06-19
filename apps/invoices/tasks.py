from celery import shared_task
from django.utils import timezone

from common.decorators import singleton_task
from invoices.models import Invoice


@shared_task
@singleton_task(timeout=16)
def gather_invoices():
    now = timezone.now()

    for invoice in Invoice.objects.filter(platform_tx__isnull=True, paid=True, expired_time__lt=now)[:4]:
        invoice.gather()
