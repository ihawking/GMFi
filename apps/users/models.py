from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


# Create your models here.


class Manager(AbstractUser):
    class Meta:
        verbose_name = _("管理员")
        verbose_name_plural = _("管理员")


@receiver(post_save, sender=Manager)
def manager_created(sender, instance, created, **kwargs):
    if created:
        if not instance.is_superuser and instance.is_staff and settings.GMFIPRO:
            from projects.models import OutProject

            OutProject.generate(owner=instance)


class User(models.Model):
    proj = models.ForeignKey("globals.Project", on_delete=models.CASCADE, default=1)

    username = models.CharField(max_length=42, db_index=True, verbose_name=_("用户"))
    deposit_account = models.OneToOneField("chains.Account", on_delete=models.PROTECT, verbose_name=_("充币地址"))

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        unique_together = ("username", "proj")
        verbose_name = _("用户")
        verbose_name_plural = verbose_name
