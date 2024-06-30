from django.contrib import admin
from django import forms
from unfold.admin import TabularInline
from unfold.decorators import display

from common.admin import ReadOnlyModelAdmin, ModelAdmin
from tokens.models import Token, TokenAddress, TokenTransfer, AccountTokenBalance


# Register your models here.
class TokenAddressInline(TabularInline):
    model = TokenAddress
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_currency:
            return "chain", "address"
        return ()

    def has_add_permission(self, request, obj=None):
        if obj and obj.is_currency:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_currency:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Token)
class TokenAdmin(ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_currency:
            return "symbol", "decimals"
        else:
            return ()

    inlines = (TokenAddressInline,)
    list_display = (
        "symbol",
        "display_type",
        "decimals",
    )

    @display(
        description="类型",
        label={
            "原生代币": "primary",
            "ERC20": "info",
        },
    )
    def display_type(self, instance: Token):
        return instance.get_type_display()


@admin.register(TokenTransfer)
class TokenTransferAdmin(ReadOnlyModelAdmin):
    list_display = (
        "chain",
        "token",
        "from_address",
        "to_address",
        "value_display",
    )
    search_fields = ("transaction__hash",)


@admin.register(AccountTokenBalance)
class AccountTokenBalanceAdmin(ReadOnlyModelAdmin):
    list_display = (
        "account",
        "chain",
        "token",
        "value_display",
    )
    search_fields = ("account__address",)
