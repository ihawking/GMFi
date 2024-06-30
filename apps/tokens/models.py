from django.db import models
from django.utils.translation import gettext_lazy as _
from common.fields import ChecksumAddressField

# Create your models here.


class TokenType(models.TextChoices):
    Native = "Native", _("原生代币")
    ERC20 = "ERC20", _("ERC20")


class Token(models.Model):
    symbol = models.CharField(_("代号"), max_length=8, help_text=_("例如：USDT、UNI"), unique=True)
    decimals = models.PositiveSmallIntegerField(_("精度"), default=18)
    chains = models.ManyToManyField(
        "chains.Chain",
        through="tokens.TokenAddress",
        related_name="tokens",
        help_text="记录代币在每个公链上的地址，原生代币地址默认为0x0地址",
    )

    coingecko_id = models.CharField(
        max_length=32,
        verbose_name="Coingecko API ID",
        help_text=_(
            "用于自动从Coingecko获取代币USD价格<br/>可以从Coingecko代币详情页面找到此值<br/>如果想手动设置价格，或者代币未上架Coingecko，则留空<br/>"
        ),
        unique=True,
        blank=True,
        null=True,
    )
    price_in_usd = models.DecimalField(_("价格（USD）"), blank=True, null=True, decimal_places=8, max_digits=32)
    type = models.CharField(choices=TokenType.choices, default=TokenType.ERC20, max_length=16, editable=False)

    @property
    def is_currency(self):
        return self.type == TokenType.Native

    def support_this_chain(self, chain) -> bool:
        return TokenAddress.objects.filter(chain=chain, token=self, active=True).exists()

    def address(self, chain):
        try:
            return TokenAddress.objects.get(token=self, chain=chain).address
        except TokenAddress.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.symbol}"

    class Meta:
        verbose_name = _("代币")
        verbose_name_plural = _("代币")


class TokenAddress(models.Model):
    token = models.ForeignKey("tokens.Token", on_delete=models.CASCADE, verbose_name=_("代币"))
    chain = models.ForeignKey("chains.Chain", on_delete=models.CASCADE, verbose_name=_("公链"))
    address = ChecksumAddressField(_("代币地址"))

    active = models.BooleanField(
        default=True, verbose_name="启用", help_text="关闭将会停止此链上与本代币相关接口的调用"
    )

    def __str__(self):
        return f"{self.chain.name} - {self.token.symbol}"

    class Meta:
        unique_together = ("token", "chain")

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

    @property
    def chain(self):
        return self.transaction.block.chain

    @property
    def value_display(self):
        return f"{self.value / 10**self.token.decimals:.8f}"

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
    chain = models.ForeignKey("chains.Chain", on_delete=models.PROTECT)
    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT)
    value = models.DecimalField(max_digits=36, decimal_places=0, default=0)

    @property
    def value_display(self):
        return f"{self.value / 10**self.token.decimals:.8f}"

    class Meta:
        unique_together = (
            "account",
            "chain",
            "token",
        )
        verbose_name = _("余额")
        verbose_name_plural = _("余额")
