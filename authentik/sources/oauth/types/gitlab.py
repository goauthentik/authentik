"""
GitLab OAuth Views

See https://docs.gitlab.com/ee/integration/oauth_provider.html
and https://docs.gitlab.com/ee/integration/openid_connect_provider.html
"""

from typing import Any

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class GitLabOAuthRedirect(OAuthRedirect):
    """GitLab OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):
        return {
            "scope": ["read_user", "openid", "profile", "email"],
        }


class GitLabOAuthCallback(OAuthCallback):
    """GitLab OAuth2 Callback"""


@registry.register()
class GitLabType(SourceType):
    """GitLab Type definition"""

    callback_view = GitLabOAuthCallback
    redirect_view = GitLabOAuthRedirect
    verbose_name = "GitLab"
    name = "gitlab"

    urls_customizable = True

    authorization_url = "https://gitlab.com/oauth/authorize"
    access_token_url = "https://gitlab.com/oauth/token"  # nosec
    profile_url = "https://gitlab.com/oauth/userinfo"
    oidc_well_known_url = "https://gitlab.com/.well-known/openid-configuration"
    oidc_jwks_url = "https://gitlab.com/oauth/discovery/keys"

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("preferred_username"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
