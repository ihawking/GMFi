import requests  # type: ignore
from django.db import models
from django.utils import timezone
from globals.models import Project

from common.utils.crypto import create_hmac_sign


# Create your models here.


class Notification(models.Model):
    transaction = models.ForeignKey("chains.Transaction", on_delete=models.CASCADE, null=True)

    content = models.JSONField()

    notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(blank=True, null=True)

    def notify(self):
        project = Project.objects.get(pk=1)
        headers = {"GMFi-Signature": create_hmac_sign(message_dict=self.content, key=project.hmac_key)}

        resp = requests.post(project.webhook, data=self.content, headers=headers, timeout=8)

        if resp.status_code == 200 and resp.text == "success":
            self.notified = True
            self.notified_at = timezone.now()
            self.save()
            return True
        else:
            return False

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "回调通知"
        verbose_name_plural = verbose_name
