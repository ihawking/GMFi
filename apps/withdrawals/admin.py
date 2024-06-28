from django.contrib import admin

from common.admin import ReadOnlyModelAdmin
from withdrawals.models import Withdrawal

from unfold.decorators import display

# Register your models here.


@admin.register(Withdrawal)
class WithdrawalAdmin(ReadOnlyModelAdmin):
    list_display = (
        "no",
        "player",
        "to",
        "chain",
        "token",
        "value",
        "display_status",
        "created_at",
    )
    search_fields = (
        "no",
        "player__uid",
    )
    list_filter = ("token",)

    @display(
        description="状态",
        label={
            "待执行": "warning",
            "待确认": "info",
            "已完成": "success",
        },
    )
    def display_status(self, instance: Withdrawal):
        return instance.status

    def chain(self, obj):
        return obj.platform_tx.chain.name

    chain.short_description = "网络"
