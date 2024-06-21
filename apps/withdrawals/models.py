from django.db import models
from django.utils.translation import gettext_lazy as _

from tokens.models import PlayerTokenValue


class Withdrawal(PlayerTokenValue):
    no = models.CharField(_("账单号"), max_length=64, unique=True)
    platform_tx = models.OneToOneField("chains.PlatformTransaction", on_delete=models.CASCADE, verbose_name=_("交易队列"))

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    @property
    def notification_content(self):
        return {
            "action": "withdrawal",
            "data": {
                "no": self.no,
                "uid": self.player.uid,
                "symbol": self.token.symbol,
                "value": self.value,
            },
        }

    class Meta:
        verbose_name = _("提币")
        verbose_name_plural = _("提币")
