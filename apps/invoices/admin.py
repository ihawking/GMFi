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
        "network",
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
        "transaction",
        "value_display",
    )
    search_fields = ("invoice__no",)
