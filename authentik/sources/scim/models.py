"""SCIM Source"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Group, Source, Token, User


class SCIMSource(Source):
    """System for Cross-domain Identity Management Source, allows for
    cross-system user provisioning"""

    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, default=None)

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        return "ak-source-scim-form"

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.scim.api import SCIMSourceSerializer

        return SCIMSourceSerializer

    def __str__(self) -> str:
        return f"SCIM Source {self.name}"

    class Meta:

        verbose_name = _("SCIM Source")
        verbose_name_plural = _("SCIM Sources")


class SCIMSourceUser(models.Model):
    """Mapping of a user and source to a SCIM user ID"""

    id = models.TextField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(SCIMSource, on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    class Meta:
        unique_together = (("id", "user", "source"),)

    def __str__(self) -> str:
        return f"SCIM User {self.user.username} to {self.source.name}"


class SCIMSourceGroup(models.Model):
    """Mapping of a group and source to a SCIM user ID"""

    id = models.TextField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    source = models.ForeignKey(SCIMSource, on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    class Meta:
        unique_together = (("id", "group", "source"),)

    def __str__(self) -> str:
        return f"SCIM Group {self.group.name} to {self.source.name}"
