"""GitLab OAuth Views"""
from typing import Any

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class GitLabOAuthRedirect(OAuthRedirect):
    """GitLab OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["read_user", "openid", "profile", "email"],
        }


class GitLabOAuthCallback(OAuthCallback):
    """GitLab OAuth2 Callback"""

    client_class: UserprofileHeaderAuthClient

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("username"),
            "email": info.get("email"),
            "name": f"{info.get('name')}",
        }


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
    profile_url = "https://gitlab.com/api/v4/user"
