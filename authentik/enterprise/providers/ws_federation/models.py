from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.providers.saml.models import SAMLProvider


class WSFederationSAMLVersion(models.TextChoices):
    """SAML Assertion version issued by a WS-Federation provider"""

    SAML_1_1 = "1.1", _("SAML 1.1")
    SAML_2_0 = "2.0", _("SAML 2.0")


class WSFederationProvider(SAMLProvider):
    """WS-Federation for applications which support WS-Fed."""

    # Alias'd fields:
    # - acs_url -> reply_url
    # - audience -> realm / wtrealm

    saml_version = models.TextField(
        choices=WSFederationSAMLVersion.choices,
        default=WSFederationSAMLVersion.SAML_2_0,
        help_text=_(
            "SAML assertion version to issue in the security token. Microsoft Entra ID and "
            "classic ADFS-style relying parties typically require SAML 1.1."
        ),
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.ws_federation.api.providers import (
            WSFederationProviderSerializer,
        )

        return WSFederationProviderSerializer

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/wsfed.svg")

    @property
    def component(self) -> str:
        return "ak-provider-wsfed-form"

    def __str__(self):
        return f"WS-Federation Provider {self.name}"

    class Meta:
        verbose_name = _("WS-Federation Provider")
        verbose_name_plural = _("WS-Federation Providers")
