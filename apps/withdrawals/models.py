from django.db import models
from django.utils.translation import gettext_lazy as _

from tokens.models import PlayerTokenValue
from common.fields import ChecksumAddressField


class Withdrawal(PlayerTokenValue):
    no = models.CharField(_("编号"), max_length=64, unique=True)
    to = ChecksumAddressField(verbose_name=_("收币地址"))
    platform_tx = models.OneToOneField("chains.PlatformTransaction", on_delete=models.PROTECT, verbose_name=_("交易"))

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    @property
    def status(self):
        if not self.platform_tx.transacted_at:
            return "待执行"
        elif self.platform_tx.transaction and self.platform_tx.transaction.block.confirmed:
            return "已完成"
        else:
            return "待确认"

    @property
    def notification_content(self):
        return {
            "action": "withdrawal",
            "data": {
                "no": self.no,
                "uid": self.player.uid,
                "symbol": self.token.symbol,
                "value": float(self.value),
            },
        }

    class Meta:
        verbose_name = _("提币")
        verbose_name_plural = _("提币")
