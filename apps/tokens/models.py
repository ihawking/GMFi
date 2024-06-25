from django.db import models
from django.utils.translation import gettext_lazy as _
from common.fields import ChecksumAddressField
from django.core.exceptions import PermissionDenied

# Create your models here.


class TokenType(models.TextChoices):
    Base = "Base", _("主币")
    ERC20 = "ERC20", _("ERC20")


class Token(models.Model):
    symbol = models.CharField(_("代号"), max_length=8, help_text=_("例如：USDT、UNI"), unique=True)
    decimals = models.PositiveSmallIntegerField(_("精度"), default=18)
    networks = models.ManyToManyField("chains.Network", through="tokens.TokenAddress", related_name="tokens")
    price_in_usdt = models.DecimalField(_("价格（USD）"), blank=True, null=True, decimal_places=8, max_digits=32)
    type = models.CharField(
        choices=TokenType.choices, default=TokenType.ERC20, max_length=8, editable=False, verbose_name=_("类型")
    )
    active = models.BooleanField(default=True, verbose_name="启用", help_text="是否启用本代币（仅对主币生效）")

    def support_this_network(self, network) -> bool:
        if network.currency == self:
            return self.active
        else:
            if TokenAddress.objects.filter(network=network, token=self, active=True).exists():
                return True

        return False

    def address(self, network):
        try:
            return TokenAddress.objects.get(token=self, network=network).address
        except TokenAddress.DoesNotExist:
            return None

    def delete(self, *args, **kwargs):
        raise PermissionDenied(_("为保护数据完整性，禁止删除."))

    def __str__(self):
        return f"{self.symbol}"

    class Meta:
        verbose_name = _("代币")
        verbose_name_plural = _("代币")


class TokenAddress(models.Model):
    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT)
    network = models.ForeignKey("chains.Network", on_delete=models.PROTECT, verbose_name=_("所在的网络"))
    address = ChecksumAddressField(_("代币地址"))

    active = models.BooleanField(default=True, verbose_name="启用", help_text="是否启用本代币（仅对ERC20生效）")

    class Meta:
        unique_together = ("token", "network")

        verbose_name = _("代币地址")
        verbose_name_plural = _("代币地址")


class TokenTransfer(models.Model):
    transaction = models.OneToOneField(
        "chains.Transaction", on_delete=models.CASCADE, related_name="token_transfer", unique=True
    )
    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT)
    from_address = ChecksumAddressField(_("From"))
    to_address = ChecksumAddressField(_("To"))
    value = models.DecimalField(max_digits=36, decimal_places=0, default=0)

    class Meta:
        verbose_name = _("转移")
        verbose_name_plural = _("转移")


class PlayerTokenValue(models.Model):
    player = models.ForeignKey("users.Player", on_delete=models.PROTECT, verbose_name=_("用户"))
    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT, verbose_name=_("代币"))
    value = models.DecimalField(_("数量"), max_digits=32, decimal_places=8)

    class Meta:
        abstract = True


class AccountTokenBalance(models.Model):
    account = models.ForeignKey("chains.Account", on_delete=models.PROTECT)
    network = models.ForeignKey("chains.Network", on_delete=models.PROTECT)
    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT)
    value = models.DecimalField(max_digits=36, decimal_places=0, default=0)

    class Meta:
        unique_together = (
            "account",
            "network",
            "token",
        )
        verbose_name = _("余额")
        verbose_name_plural = _("余额")
