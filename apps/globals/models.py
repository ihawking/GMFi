from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.fields import ChecksumAddressField


# Create your models here.
class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        assert self.pk == 1
        super().save(*args, **kwargs)


class Project(SingletonModel):
    ip_white_list = models.TextField(
        _("IP白名单"),
        null=True,
        help_text="只有符合白名单的 IP 才可以与本网关交互；<br/>支持 IP 地址或 IP 网段；<br/>可同时设置多个，中间用英文逗号','分割；<br/>",
    )
    webhook = models.URLField(
        _("Webhook回调地址"), max_length=256, null=True, help_text="用于本网关发送通知到项目后端；"
    )
    notification_failed_times = models.PositiveIntegerField(
        verbose_name=_("连续通知失败的次数"), default=0, help_text="超过32次则不再发送通知，直到手动置为零；"
    )

    pre_notify = models.BooleanField(_("开启预通知"), default=False)
    hmac_key = models.CharField(_("HMAC密钥"), max_length=256, help_text="用于本网关与项目后端的交互签名；")
    distribution_account = models.OneToOneField(
        "chains.Account",
        on_delete=models.PROTECT,
        verbose_name=_("系统账户"),
        help_text="提币时，系统通过此账户发送代币到用户地址；<br/>要保证此地址的 Gas 和各代币充盈，否则提币无法成功；",
        related_name="project",
    )
    collection_address = ChecksumAddressField(
        null=True,
        verbose_name=_("代币归集地址"),
        help_text="用户支付的代币，将归集到此地址；",
    )

    @property
    def distribution_address(self):
        return self.distribution_account.address

    def __str__(self):
        return "配置"

    class Meta:
        verbose_name = "项目配置"
        verbose_name_plural = "项目配置"


def status(request):
    project = Project.objects.get(pk=1)

    if not all([project.collection_address, project.webhook]):
        return "待设置"

    elif project.distribution_account.tx_callable_failed_times >= 32:
        return "系统账户余额不足"

    elif project.notification_failed_times > 32:
        return "通知接口异常"

    else:
        return ""
