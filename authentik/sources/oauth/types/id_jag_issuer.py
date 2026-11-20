"""Issuer of identity assertions (ID-JAGs), trusted without signing users in through it"""

from django.templatetags.static import static

from authentik.sources.oauth.types.registry import SourceType, registry

# Appended to the issuer identifier to find its metadata (OpenID Connect Discovery §4)
WELL_KNOWN_SUFFIX = "/.well-known/openid-configuration"


@registry.register()
class IdJagIssuerType(SourceType):
    """An issuer of identity assertions (ID-JAGs), such as Claude, that publishes only its
    issuer identifier and signing keys. Users don't sign in through it, so it has no client
    or login URLs, and its opaque `sub` means ID-JAG users are always matched by email."""

    verbose_name = "Identity Assertion Issuer"
    name = "idjagissuer"

    requires_client_secret = False
    assertion_only = True

    def icon_url(self) -> str:
        return static("authentik/sources/openidconnect/light.svg")
