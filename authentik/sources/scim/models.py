"""SCIM Source"""

from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer
from django.templatetags.static import static

from authentik.core.models import Group, Source, Token, User
from authentik.lib.models import SerializerModel


class SCIMSource(Source):
    """System for Cross-domain Identity Management Source, allows for
    cross-system user provisioning"""

    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, default=None)

    @property
    def service_account_identifier(self) -> str:
        if not self.pk:
            self.pk = uuid4()
        return f"ak-source-scim-{self.pk}"

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        return "ak-source-scim-form"

    @property
    def icon_url(self) -> str:
        return static("authentik/sources/scim.png")

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.scim.api.sources import SCIMSourceSerializer

        return SCIMSourceSerializer

    def __str__(self) -> str:
        return f"SCIM Source {self.name}"

    class Meta:

        verbose_name = _("SCIM Source")
        verbose_name_plural = _("SCIM Sources")


class SCIMSourceUser(SerializerModel):
    """Mapping of a user and source to a SCIM user ID"""

    id = models.TextField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(SCIMSource, on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.scim.api.users import SCIMSourceUserSerializer

        return SCIMSourceUserSerializer

    class Meta:
        unique_together = (("id", "user", "source"),)

    def __str__(self) -> str:
        return f"SCIM User {self.user_id} to {self.source_id}"


class SCIMSourceGroup(SerializerModel):
    """Mapping of a group and source to a SCIM user ID"""

    id = models.TextField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    source = models.ForeignKey(SCIMSource, on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.scim.api.groups import SCIMSourceGroupSerializer

        return SCIMSourceGroupSerializer

    class Meta:
        unique_together = (("id", "group", "source"),)

    def __str__(self) -> str:
        return f"SCIM Group {self.group_id} to {self.source_id}"
