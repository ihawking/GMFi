from django.contrib import admin

from common.admin import ReadOnlyModelAdmin
from withdrawals.models import Withdrawal


# Register your models here.


@admin.register(Withdrawal)
class WithdrawalAdmin(ReadOnlyModelAdmin):
    list_display = (
        "user",
        "token",
        "value",
        "no",
    )
