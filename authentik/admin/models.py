"""authentik admin models"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class VersionHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField()
    version = models.TextField()
    build = models.TextField()

    class Meta:
        managed = False
        db_table = "authentik_version_history"
        ordering = ("-timestamp",)
        verbose_name = _("Version history")
        verbose_name_plural = _("Version history")
        default_permissions = []

    def __str__(self):
        return f"{self.version}.{self.build} ({self.timestamp})"
