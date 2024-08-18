"""Okta OAuth Views"""

from typing import Any

from authentik.common.oauth.constants import SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect


class OktaOAuthRedirect(OAuthRedirect):
    """Okta OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": [SCOPE_OPENID, SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL],
        }


@registry.register()
class OktaType(SourceType):
    """Okta Type definition"""

    callback_view = OpenIDConnectOAuth2Callback
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
