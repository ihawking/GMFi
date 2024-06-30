from django.contrib import admin

from common.admin import ReadOnlyModelAdmin
from deposits.models import Deposit


# Register your models here.


@admin.register(Deposit)
class DepositAdmin(ReadOnlyModelAdmin):
    list_display = ("player", "token", "value")
    search_fields = ("player__uid",)
    list_filter = ("token",)
