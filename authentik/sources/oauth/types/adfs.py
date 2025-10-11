
"""ADFS OAuth Views"""

from typing import Any
from jwt import decode

from authentik.sources.oauth.models import AuthorizationCodeAuthMethod
from authentik.sources.oauth.types.oidc import OpenIDConnectClient, OpenIDConnectOAuth2Callback, OpenIDConnectOAuthRedirect, OpenIDConnectType
from authentik.sources.oauth.types.registry import SourceType, registry


class AdfsConnectClient(OpenIDConnectClient):
    
    def get_profile_info(self, token):
        id_token = token.get("id_token")
        if id_token is None:
            return None
        return decode(id_token, options={"verify_signature": False})

class AdfsOAuth2Callback(OpenIDConnectOAuth2Callback):
    """ADFS OAuth2 Callback"""

    client_class = AdfsConnectClient

    def get_user_id(self, info):
        return super().get_user_id(info) or info.get("upn")

@registry.register()
class AdfsConnectType(SourceType):
    """Adfs Type definition"""

    callback_view = AdfsOAuth2Callback
    verbose_name = "ADFS Connect"
    name = "adfs"

    urls_customizable = True
    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    redirect_view = OpenIDConnectOAuthRedirect

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("displayName"),
            "email": info.get("email"),
            "name": info.get("email"),
            "groups": info.get("group", []),
        }
