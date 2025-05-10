"""Google OAuth Views"""

from typing import Any

from authentik.common.oauth.constants import SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect


class GoogleOAuthRedirect(OAuthRedirect):
    """Google OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": [SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL],
        }


@registry.register()
class GoogleType(SourceType):
    """Google Type definition"""

    redirect_view = GoogleOAuthRedirect
    verbose_name = "Google"
    name = "google"

    authorization_url = "https://accounts.google.com/o/oauth2/auth"
    access_token_url = "https://oauth2.googleapis.com/token"  # nosec
    profile_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    oidc_well_known_url = "https://accounts.google.com/.well-known/openid-configuration"
    oidc_jwks_url = "https://www.googleapis.com/oauth2/v3/certs"

    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "email": info.get("email"),
            "name": info.get("name"),
        }
