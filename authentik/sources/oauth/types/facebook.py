"""Facebook OAuth Views"""

from typing import Any

from authentik.sources.oauth.models import AuthorizationCodeAuthMethod
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect


class FacebookOAuthRedirect(OAuthRedirect):
    """Facebook OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["email"],
        }


@registry.register()
class FacebookType(SourceType):
    """Facebook Type definition"""

    redirect_view = FacebookOAuthRedirect
    verbose_name = "Facebook"
    name = "facebook"

    authorization_url = "https://www.facebook.com/v7.0/dialog/oauth"
    access_token_url = "https://graph.facebook.com/v7.0/oauth/access_token"  # nosec
    profile_url = "https://graph.facebook.com/v7.0/me?fields=id,name,email"

    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("name"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
