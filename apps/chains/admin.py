from django import forms
from django.contrib import admin
from web3 import Web3

from chains.models import Chain, Account, PlatformTransaction, Block, Transaction
from common.admin import ReadOnlyModelAdmin, ModelAdmin
from unfold.decorators import display

# Register your models here.


class ChainForm(forms.ModelForm):
    class Meta:
        model = Chain
        fields = "__all__"

    def clean_endpoint_uri(self):
        endpoint_uri = self.cleaned_data["endpoint_uri"]
        instance: Chain = self.instance
        chain_id = Web3(Web3.HTTPProvider(endpoint_uri)).eth.chain_id

        if (
            not instance.chain_id and Chain.objects.filter(pk=chain_id).exists()
        ):  # 如果是新建 Chain，需要验证是否与已存在的公链重复
            raise forms.ValidationError("公链重复")

        if (
            instance.chain_id and chain_id != instance.chain_id
        ):  # 验证表单中的 uri 指向的 chain id，是否和数据库中的数据匹配
            raise forms.ValidationError("RPC 地址与当前 Chain ID 不匹配")
        return endpoint_uri


@admin.register(Chain)
class ChainAdmin(ModelAdmin):
    form = ChainForm
    readonly_fields = ("name", "chain_id", "currency")
    list_display = ("display_header", "display_chain_id", "currency", "endpoint_uri", "active")
    list_editable = ("active",)

    @display(description="Chain ID", label=True)
    def display_chain_id(self, instance: Chain):
        return instance.chain_id

    @display(description="名称", header=True)
    def display_header(self, instance: Chain):
        return [
            instance.name,
            None,
            instance.chain_id,
            {
                "path": instance.icon,
                # "squared": True,
            },
        ]

    fieldsets = (
        (
            "节点",
            {"fields": ("endpoint_uri",)},
        ),
        ("公链信息", {"fields": ("name", "chain_id", "currency")}),
        (
            "配置",
            {"fields": ("block_confirmations_count", "active")},
        ),
    )


@admin.register(Block)
class BlockAdmin(ReadOnlyModelAdmin):
    list_filter = ("chain",)
    search_fields = ("hash", "number")
    list_display = ("id", "chain", "number", "hash", "confirmed")


@admin.register(Transaction)
class TransactionAdmin(ReadOnlyModelAdmin):
    ordering = ("-id",)
    list_filter = ("block__chain",)
    search_fields = (
        "hash",
        "block__number",
    )
    list_display = (
        "id",
        "hash",
        "block",
        "type",
    )


@admin.register(Account)
class AccountAdmin(ReadOnlyModelAdmin):
    list_display = ("address", "type")
    search_fields = ("address",)


@admin.register(PlatformTransaction)
class PlatformTransactionAdmin(ReadOnlyModelAdmin):
    ordering = ("-created_at",)
    list_display = ("account", "chain", "nonce", "transacted_at", "transaction")
    search_fields = ("hash", "account__address")
