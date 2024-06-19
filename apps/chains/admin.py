from django import forms
from django.contrib import admin
from web3 import Web3

from chains.models import Network, Account, PlatformTransaction, Block, Transaction
from common.admin import ReadOnlyModelAdmin, ModelAdmin


# Register your models here.


class NetworkForm(forms.ModelForm):
    class Meta:
        model = Network
        fields = "__all__"

    def clean_endpoint_uri(self):
        endpoint_uri = self.cleaned_data.get("endpoint_uri")
        instance: Network = self.instance

        if not Network.objects.filter(id=instance.id).exists():  # 如果是新建 Network，则不需要验证
            return endpoint_uri

        if (
            Web3(Web3.HTTPProvider(endpoint_uri)).eth.chain_id != instance.chain_id
        ):  # 验证表单中的 uri 指向的 chain id，是否和数据库中的数据匹配
            raise forms.ValidationError("RPC 地址与当前 Chain ID 不匹配")
        return endpoint_uri


@admin.register(Network)
class NetworkAdmin(ModelAdmin):
    form = NetworkForm
    readonly_fields = ("chain_id",)
    list_display = ("name", "chain_id", "endpoint_uri")


@admin.register(Block)
class BlockAdmin(ReadOnlyModelAdmin):
    list_filter = ("network",)
    search_fields = ("hash", "number")
    list_display = ("network", "number", "hash", "confirmed")


@admin.register(Transaction)
class TransactionAdmin(ReadOnlyModelAdmin):
    list_filter = ("block__network",)
    search_fields = (
        "hash",
        "block__number",
    )
    list_display = (
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
    list_display = ("account", "network", "nonce", "transacted_at", "transaction")
