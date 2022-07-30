"""GitHub OAuth Views"""
from typing import Any

from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class GitHubOAuthRedirect(OAuthRedirect):
    """GitHub OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["read:user", "user:email"],
        }


class GitHubOAuth2Callback(OAuthCallback):
    """GitHub OAuth2 Callback"""

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("login"),
            "email": info.get("email"),
            "name": info.get("name"),
        }


@MANAGER.type()
class GitHubType(SourceType):
    """GitHub Type definition"""

    callback_view = GitHubOAuth2Callback
    redirect_view = GitHubOAuthRedirect
    name = "GitHub"
    slug = "github"

    urls_customizable = True

    authorization_url = "https://github.com/login/oauth/authorize"
    access_token_url = "https://github.com/login/oauth/access_token"  # nosec
    profile_url = "https://api.github.com/user"
