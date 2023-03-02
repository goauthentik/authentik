"""SCIM Provider models"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Group, PropertyMapping, Provider, User


class SCIMProvider(Provider):
    """TODO"""

    url = models.TextField(help_text=_("Base URL to SCIM requests, usually ends in /v2"))
    token = models.TextField(help_text=_("Authentication token"))

    @property
    def component(self) -> str:
        return "ak-provider-scim-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.scim.api.providers import SCIMProviderSerializer

        return SCIMProviderSerializer

    def __str__(self):
        return f"SCIM Provider {self.name}"

    class Meta:
        verbose_name = _("SCIM Provider")
        verbose_name_plural = _("SCIM Providers")


class SCIMMapping(PropertyMapping):
    """TODO"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-scim-form"

    @property
    def serializer(self) -> type[Serializer]:
        return super().serializer

    def __str__(self):
        return f"SCIM Mapping {self.name}"

    class Meta:
        verbose_name = _("SCIM Mapping")
        verbose_name_plural = _("SCIM Mappings")


class SCIMUser(models.Model):
    """Mapping of a user and provider to a SCIM user ID"""

    id = models.TextField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(SCIMProvider, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("id", "user", "provider"),)


class SCIMGroup(models.Model):
    """Mapping of a group and provider to a SCIM user ID"""

    id = models.TextField(primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    provider = models.ForeignKey(SCIMProvider, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("id", "group", "provider"),)
