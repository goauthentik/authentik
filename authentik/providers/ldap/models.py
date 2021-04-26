"""LDAP Provider"""
from typing import Iterable, Optional, Type

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Provider
from authentik.flows.models import Flow
from authentik.outposts.models import OutpostModel


class LDAPProvider(OutpostModel, Provider):
    """Allow applications to authenticate against authentik's users using LDAP."""

    base_dn = models.TextField(
        default="DC=ldap,DC=goauthentik,DC=io",
        help_text=_("DN under which objects are accessible."),
    )

    bind_flow = models.ForeignKey(
        Flow,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_(
            "Flow which is used to bind users. When left empty, no users will be able to bind."
        ),
    )

    @property
    def launch_url(self) -> Optional[str]:
        """LDAP never has a launch URL"""
        return None

    @property
    def component(self) -> str:
        return "ak-provider-ldap-form"

    @property
    def serializer(self) -> Type[Serializer]:
        from authentik.providers.oauth2.api.provider import OAuth2ProviderSerializer

        return OAuth2ProviderSerializer

    def __str__(self):
        return f"LDAP Provider {self.name}"

    def get_required_objects(self) -> Iterable[models.Model]:
        return [self]

    class Meta:

        verbose_name = _("LDAP Provider")
        verbose_name_plural = _("LDAP Providers")
