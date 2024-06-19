from django.db import models
from django.utils.translation import gettext_lazy as _

from chains.models import Transaction, Account
from tokens.models import UserTokenValue


# Create your models here.


class Deposit(UserTokenValue):
    transaction = models.OneToOneField("chains.Transaction", on_delete=models.CASCADE, verbose_name=_("交易"))

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def parse_transaction(cls, transaction: Transaction):
        token_transfer = transaction.token_transfer
        deposit_account = Account.objects.get(address=token_transfer.to_address, user__isnull=False)
        Deposit.objects.create(
            transaction=transaction,
            user=deposit_account.user,
            token=token_transfer.token,
            value=token_transfer.value / 10 ** token_transfer.token.decimals,
        )

    @property
    def notification_content(self):
        return {
            "action": "deposit",
            "data": {"username": self.user.username, "symbol": self.token.symbol, "value": self.value},
        }

    class Meta:
        verbose_name = _("充币")
        verbose_name_plural = _("充币")
