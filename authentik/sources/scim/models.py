"""SCIM Source"""
from django.db import models
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Source, Token

USER_ATTRIBUTE_SCIM_ID = "goauthentik.io/sources/scim/id"
USER_ATTRIBUTE_SCIM_ADDRESS = "goauthentik.io/sources/scim/address"
USER_ATTRIBUTE_SCIM_ENTERPRISE = "goauthentik.io/sources/scim/enterprise"


class SCIMSource(Source):
    """SCIM Source"""

    token = models.ForeignKey(Token, on_delete=models.CASCADE)

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        return "ak-source-scim-form"

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.scim.api import SCIMSourceSerializer

        return SCIMSourceSerializer
