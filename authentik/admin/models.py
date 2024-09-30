"""authentik admin models"""

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


class VersionHistory(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    version = models.TextField()
    build = models.TextField()

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = _("Version history")
        verbose_name_plural = _("Version history")

    @classmethod
    def create_new_entry(cls, version: str, build: str):
        with transaction.atomic():
            last_entry = cls.objects.all().first()
            if last_entry and last_entry.version == version and last_entry.build == build:
                return
            cls.objects.create(version=version, build=build)
