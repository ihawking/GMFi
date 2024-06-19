import requests  # type: ignore
from django.db import models
from django.utils import timezone

from common.utils.crypto import create_hmac_sign


# Create your models here.


class Notification(models.Model):
    transaction = models.ForeignKey("chains.Transaction", on_delete=models.CASCADE, null=True)

    content = models.JSONField()

    notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(blank=True, null=True)

    def notify(self):
        proj = self.transaction.related_proj
        headers = {"GMFi-Signature": create_hmac_sign(message_dict=self.content, key=proj.hmac_key)}

        resp = requests.post(proj.webhook, data=self.content, headers=headers, timeout=8)

        if resp.status_code == 200 and resp.text == "success":
            self.notified = True
            self.notified_at = timezone.now()
            self.save()
            return True
        else:
            return False

    class Meta:
        ordering = ("created_at",)
