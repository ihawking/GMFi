from django.contrib import admin

from common.admin import ModelAdmin
from notifications.models import Notification


# Register your models here.


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = (
        "notified",
        "created_at",
    )
