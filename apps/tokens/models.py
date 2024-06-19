from django.db import models
from django.utils.translation import gettext_lazy as _

from common.fields import ChecksumAddressField


# Create your models here.


class Token(models.Model):
    symbol = models.CharField(_("代号"), max_length=32, help_text=_("例如：USDT、UNI"), unique=True)
    decimals = models.PositiveSmallIntegerField(_("精度"), default=18)
    networks = models.ManyToManyField("chains.Network", through="tokens.TokenAddress", related_name="tokens")
    valid = models.BooleanField(_("启用"), default=True)
    price_in_usdt = models.DecimalField(_("价格（USD）"), blank=True, null=True, decimal_places=8, max_digits=32)

    def support_this_network(self, network) -> bool:
        if network.currency == self:
            return True

        if TokenAddress.objects.filter(network=network, token=self).exists():
            return True

        return False

    def address(self, network):
        try:
            return TokenAddress.objects.get(token=self, network=network).address
        except TokenAddress.DoesNotExist:
            return None

    def __str__(self):
        return self.symbol

    class Meta:
        verbose_name = _("代币")
        verbose_name_plural = _("代币")


class TokenAddress(models.Model):
    token = models.ForeignKey("tokens.Token", on_delete=models.CASCADE)
    network = models.ForeignKey("chains.Network", on_delete=models.CASCADE, verbose_name=_("所在的网络"))
    address = ChecksumAddressField(_("代币地址"))

    class Meta:
        unique_together = ("token", "network")

        verbose_name = _("代币地址")
        verbose_name_plural = _("代币地址")


class TokenTransfer(models.Model):
    transaction = models.OneToOneField(
        "chains.Transaction", on_delete=models.CASCADE, related_name="token_transfer", unique=True
    )
    token = models.ForeignKey("tokens.Token", on_delete=models.CASCADE)
    from_address = ChecksumAddressField(_("From"))
    to_address = ChecksumAddressField(_("To"))
    value = models.DecimalField(max_digits=36, decimal_places=0, default=0)

    class Meta:
        verbose_name = _("转移")
        verbose_name_plural = _("转移")


class UserTokenValue(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, verbose_name=_("用户"))
    token = models.ForeignKey("tokens.Token", on_delete=models.CASCADE, verbose_name=_("代币"))
    value = models.DecimalField(_("数量"), max_digits=32, decimal_places=8)

    class Meta:
        abstract = True


class AccountTokenBalance(models.Model):
    account = models.ForeignKey("chains.Account", on_delete=models.CASCADE)
    network = models.ForeignKey("chains.Network", on_delete=models.CASCADE)
    token = models.ForeignKey("tokens.Token", on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=36, decimal_places=0, default=0)

    class Meta:
        unique_together = (
            "account",
            "network",
            "token",
        )
        verbose_name = _("余额")
        verbose_name_plural = _("余额")
