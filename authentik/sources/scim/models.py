"""SCIM Source"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Source, Token

USER_ATTRIBUTE_SCIM_ID = "goauthentik.io/sources/scim/id"
USER_ATTRIBUTE_SCIM_ADDRESS = "goauthentik.io/sources/scim/address"
USER_ATTRIBUTE_SCIM_ENTERPRISE = "goauthentik.io/sources/scim/enterprise"


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
