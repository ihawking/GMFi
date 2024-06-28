from django.db import models
from django.utils.translation import gettext_lazy as _

from chains.models import Transaction, Account
from tokens.models import PlayerTokenValue


# Create your models here.


class Deposit(PlayerTokenValue):
    transaction = models.OneToOneField("chains.Transaction", on_delete=models.CASCADE, verbose_name=_("交易"))

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def parse_transaction(cls, transaction: Transaction):
        token_transfer = transaction.token_transfer
        deposit_account = Account.objects.get(address=token_transfer.to_address, player__isnull=False)
        Deposit.objects.create(
            transaction=transaction,
            player=deposit_account.player,
            token=token_transfer.token,
            value=token_transfer.value / 10**token_transfer.token.decimals,
        )

    @property
    def notification_content(self):
        return {
            "action": "deposit",
            "data": {"uid": self.player.uid, "symbol": self.token.symbol, "value": float(self.value)},
        }

    class Meta:
        verbose_name = _("充币")
        verbose_name_plural = _("充币")
