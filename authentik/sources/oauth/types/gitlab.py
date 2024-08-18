"""
GitLab OAuth Views

See https://docs.gitlab.com/ee/integration/oauth_provider.html
and https://docs.gitlab.com/ee/integration/openid_connect_provider.html
"""

from typing import Any

from authentik.common.oauth.constants import SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod, OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect


class GitLabOAuthRedirect(OAuthRedirect):
    """GitLab OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):
        return {
            "scope": ["read_user", SCOPE_OPENID, SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL],
        }


@registry.register()
class GitLabType(SourceType):
    """GitLab Type definition"""

    redirect_view = GitLabOAuthRedirect
    verbose_name = "GitLab"
    name = "gitlab"

    urls_customizable = True

    authorization_url = "https://gitlab.com/oauth/authorize"
    access_token_url = "https://gitlab.com/oauth/token"  # nosec
    profile_url = "https://gitlab.com/oauth/userinfo"
    oidc_well_known_url = "https://gitlab.com/.well-known/openid-configuration"
    oidc_jwks_url = "https://gitlab.com/oauth/discovery/keys"

    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("preferred_username"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
