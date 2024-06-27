from django.contrib.auth.models import AbstractUser
from django.db import models

from django.utils.translation import gettext_lazy as _
from chains.models import Account
from django.dispatch import receiver
from django.db.models.signals import pre_save

# Create your models here.


class Manager(AbstractUser):
    class Meta:
        verbose_name = _("管理员")
        verbose_name_plural = _("管理员")


class Player(models.Model):
    uid = models.CharField(max_length=64, unique=True, db_index=True, verbose_name=_("玩家UID"))
    deposit_account = models.OneToOneField(
        "chains.Account", on_delete=models.PROTECT, verbose_name=_("充币地址"), blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uid

    class Meta:
        verbose_name = _("玩家")
        verbose_name_plural = verbose_name


@receiver(pre_save, sender=Player)
def add_deposit_account(sender, instance: Player, **kwargs):
    if not instance.deposit_account_id:
        instance.deposit_account_id = Account.generate().id
