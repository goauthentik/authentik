"""passbook audit models"""

from django.conf import settings
from django.db import models
from reversion import register

from passbook.lib.models import UUIDModel


@register()
class AuditEntry(UUIDModel):
    """An individual audit log entry"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    app = models.TextField()

    def save(self, *args, **kwargs):
        if self.pk:
            raise NotImplementedError("you may not edit an existing %s" % self._meta.model_name)
        super().save(*args, **kwargs)
