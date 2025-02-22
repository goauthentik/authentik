"""Okta OAuth Views"""

from typing import Any

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect


class OktaOAuthRedirect(OAuthRedirect):
    """Okta OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["openid", "email", "profile"],
        }


class OktaOAuth2Callback(OpenIDConnectOAuth2Callback):
    """Okta OAuth2 Callback"""

    # Okta has the same quirk as azure and throws an error if the access token
    # is set via query parameter, so we reuse the azure client
    # see https://github.com/goauthentik/authentik/issues/1910
    client_class = UserprofileHeaderAuthClient


@registry.register()
class OktaType(SourceType):
    """Okta Type definition"""

    callback_view = OktaOAuth2Callback
    redirect_view = OktaOAuthRedirect
    verbose_name = "Okta"
    name = "okta"

    urls_customizable = True

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("nickname"),
            "email": info.get("email"),
            "name": info.get("name"),
            "groups": info.get("groups", []),
        }
