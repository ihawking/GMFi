from django.contrib import admin

from common.admin import ReadOnlyModelAdmin
from deposits.models import Deposit
from unfold.decorators import display

# Register your models here.


@admin.register(Deposit)
class DepositAdmin(ReadOnlyModelAdmin):
    list_display = ("player", "chain", "token", "value", "display_status")
    search_fields = ("player__uid", "transaction__hash")
    list_filter = ("token",)

    def chain(self, obj):
        return obj.transaction.block.chain

    chain.short_description = "公链"

    @display(
        description="状态",
        label={
            "确认中": "info",
            "已确认": "success",
        },
    )
    def display_status(self, instance: Deposit):
        return instance.status
