from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.providers.saml.models import SAMLProvider


class WSFederationProvider(SAMLProvider):
    """WS-Federation for applications which support WS-Fed."""

    # Alias'd fields:
    # - acs_url -> reply_url
    # - audience -> realm / wtrealm

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
