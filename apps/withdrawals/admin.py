from django.contrib import admin

from common.admin import ReadOnlyModelAdmin
from withdrawals.models import Withdrawal


# Register your models here.


@admin.register(Withdrawal)
class WithdrawalAdmin(ReadOnlyModelAdmin):
    list_display = (
        "no",
        "player",
        "to",
        "network",
        "token",
        "value",
    )

    search_fields = (
        "no",
        "player__uid",
    )
    list_filter = ("token",)

    def network(self, obj):
        return obj.platform_tx.network.name

    network.short_description = "网络"
