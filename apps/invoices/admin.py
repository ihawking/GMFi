from django.contrib import admin

from common.admin import ReadOnlyModelAdmin
from invoices.models import Invoice, Payment


# Register your models here.


@admin.register(Invoice)
class InvoiceAdmin(ReadOnlyModelAdmin):
    list_display = (
        "no",
        "out_no",
        "token",
        "pay_address",
        "value",
        "actual_value",
        "paid",
    )
    search_fields = (
        "no",
        "out_no",
    )
    list_filter = (
        "chain",
        "token",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(Payment)
class PaymentAdmin(ReadOnlyModelAdmin):
    list_display = (
        "invoice",
        "token",
        "value_display",
        "transaction",
    )

    def token(self, obj):
        return obj.invoice.token

    token.short_description = "代币"

    def value_display(self, obj):
        return obj.value_display

    value_display.short_description = "支付数量"

    search_fields = ("invoice__no",)
