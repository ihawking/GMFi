from decimal import Decimal
from typing import cast

from django.db import models
from django.db import transaction as db_transaction
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from web3.types import HexStr

from chains.utils import create2
from common.fields import ChecksumAddressField
from django.utils import timezone

# Create your models here.


class Invoice(models.Model):
    no = models.CharField(_("系统账单号"), unique=True, max_length=32, db_index=True)
    out_no = models.CharField(_("商户账单号"), unique=True, max_length=32, db_index=True)
    subject = models.CharField(_("标题"), max_length=32)
    detail = models.JSONField(_("详情"), default=dict)
    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT, verbose_name=_("代币"))
    chain = models.ForeignKey("chains.Chain", on_delete=models.PROTECT, verbose_name=_("网络"))
    value = models.DecimalField(_("应付数量"), max_digits=32, decimal_places=8)
    expired_time = models.DateTimeField(_("支付截止时间"))
    redirect_url = models.URLField(_("支付成功后重定向地址"), null=True, blank=True)

    salt = models.CharField(_("盐"), max_length=66, unique=True)
    init_code = models.TextField(_("合约初始化代码"))
    pay_address = ChecksumAddressField(_("账单支付地址"))
    collection_address = ChecksumAddressField(_("资金归集地址"))

    paid = models.BooleanField(_("支付完成"), default=False)
    actual_value = models.DecimalField(_("实际支付数量"), max_digits=32, decimal_places=8, default=0)

    transaction_queue = models.OneToOneField(
        "chains.TransactionQueue", on_delete=models.PROTECT, verbose_name=_("归集交易"), null=True, blank=True
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    @property
    def status(self):
        if not self.paid:
            if timezone.now() > self.expired_time:
                return "已失效"
            else:
                return "待支付"
        else:
            if self.payment_set.filter(transaction__block__confirmed=False).exists():
                return "确认中"
            else:
                return "已完成"

    @property
    def notification_content(self):
        content = {
            "action": "invoice",
            "data": {
                "no": self.no,
                "out_no": self.out_no,
                "chain": self.chain.name,
                "token": self.token_symbol,
                "value": float(self.value),
                "actual_value": float(self.actual_value),
            },
        }
        return content

    @property
    def token_symbol(self):
        return self.token.symbol

    @property
    def token_address(self):
        return self.token.address(self.chain)

    @property
    def gathered(self):
        return self.transaction_queue.transaction.block.confirmed

    @property
    def remaining_value(self) -> Decimal:
        # 待支付的数量
        return min(self.value - self.actual_value, Decimal("0"))

    @property
    def chain_id(self):
        return self.chain.chain_id

    def gather(self):
        account = self.chain.project.system_account

        account.get_lock()
        with db_transaction.atomic():
            from chains.models import TransactionQueue

            self.transaction_queue = TransactionQueue.objects.create(
                account=account,
                chain=self.chain,
                to=create2.factory_address,
                nonce=account.nonce(self.chain),
                data=create2.get_transaction_data(
                    salt=cast(HexStr, self.salt), init_code=cast(HexStr, self.init_code)
                ),
            )
            self.save()
        account.release_lock()

    def __str__(self):
        return f"{self.no}"

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("账单")
        verbose_name_plural = _("账单")


class Payment(models.Model):
    transaction = models.OneToOneField("chains.Transaction", on_delete=models.CASCADE, verbose_name=_("交易"))
    invoice = models.ForeignKey("invoices.Invoice", on_delete=models.CASCADE, verbose_name=_("账单"))
    value = models.DecimalField(_("支付数量"), max_digits=36, decimal_places=0)

    @property
    def confirm_process(self):
        return self.transaction.confirm_process

    @property
    def tx_hash(self):
        return self.transaction.hash

    @property
    def value_display(self):
        return Decimal(self.value / 10**self.invoice.token.decimals)

    class Meta:
        ordering = ("transaction",)
        verbose_name = _("支付记录")
        verbose_name_plural = _("支付记录")


@receiver(post_save, sender=Payment)
def create_payment(sender, instance: Payment, created, **kwargs):
    if created:
        invoice = instance.invoice
        invoice.actual_value = F("actual_value") + instance.value_display
        invoice.save()

        invoice.refresh_from_db()
        if invoice.actual_value >= invoice.value:
            invoice.paid = True
            invoice.save()


@receiver(post_delete, sender=Payment)
def delete_payment(sender, instance: Payment, **kwargs):
    invoice = instance.invoice
    invoice.actual_value = F("actual_value") - instance.value_display
    invoice.save()

    invoice.refresh_from_db()
    if invoice.actual_value < invoice.value:
        invoice.paid = False
        invoice.save()
