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
        "chain",
        "token",
        "value",
    )

    search_fields = (
        "no",
        "player__uid",
    )
    list_filter = ("token",)

    def chain(self, obj):
        return obj.platform_tx.chain.name

    chain.short_description = "网络"
