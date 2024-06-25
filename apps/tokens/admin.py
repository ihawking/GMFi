from django.contrib import admin
from unfold.admin import TabularInline

from common.admin import ReadOnlyModelAdmin, NoDeleteModelAdmin
from tokens.models import Token, TokenAddress, TokenTransfer, AccountTokenBalance


# Register your models here.
class TokenAddressInline(TabularInline):
    model = TokenAddress
    extra = 0


@admin.register(Token)
class TokenAdmin(NoDeleteModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    inlines = (TokenAddressInline,)
    list_display = (
        "symbol",
        "type",
    )


@admin.register(TokenTransfer)
class TokenTransferAdmin(ReadOnlyModelAdmin):
    list_display = (
        "transaction",
        "from_address",
        "to_address",
        "value",
    )
    search_fields = ("transaction__hash",)


@admin.register(AccountTokenBalance)
class AccountTokenBalanceAdmin(ReadOnlyModelAdmin):
    list_display = (
        "account",
        "network",
        "token",
        "value",
    )
    search_fields = ("account__address",)
