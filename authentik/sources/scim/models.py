"""SCIM Source"""

from typing import Any

from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.common.models import SerializerModel, internal_model
from authentik.core.models import Group, PropertyMapping, Source, Token, User


class SCIMSource(Source):
    """System for Cross-domain Identity Management Source, allows for
    cross-system user provisioning"""

    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, default=None)

    @property
    def service_account_identifier(self) -> str:
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

    @property
    def property_mapping_type(self) -> type[PropertyMapping]:
        return SCIMSourcePropertyMapping

    def get_base_user_properties(self, data: dict[str, Any]) -> dict[str, Any | dict[str, Any]]:
        properties = {}

        def get_email(data: list[dict]) -> str:
            """Wrapper to get primary email or first email"""
            for email in data:
                if email.get("primary", False):
                    return email.get("value")
            if len(data) < 1:
                return ""
            return data[0].get("value")

        if "userName" in data:
            properties["username"] = data.get("userName")
        if "name" in data:
            properties["name"] = data.get("name", {}).get("formatted", data.get("displayName"))
        if "emails" in data:
            properties["email"] = get_email(data.get("emails"))
        if "active" in data:
            properties["is_active"] = data.get("active")

        return properties

    def get_base_group_properties(self, data: dict[str, Any]) -> dict[str, Any | dict[str, Any]]:
        properties = {}

        if "displayName" in data:
            properties["name"] = data.get("displayName")

        return properties

    def __str__(self) -> str:
        return f"SCIM Source {self.name}"

    class Meta:

        verbose_name = _("SCIM Source")
        verbose_name_plural = _("SCIM Sources")


class SCIMSourcePropertyMapping(PropertyMapping):
    """Map SCIM properties to User or Group object attributes"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-scim-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.scim.api.property_mappings import (
            SCIMSourcePropertyMappingSerializer,
        )

        return SCIMSourcePropertyMappingSerializer

    class Meta:
        verbose_name = _("SCIM Source Property Mapping")
        verbose_name_plural = _("SCIM Source Property Mappings")


@internal_model
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


@internal_model
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
