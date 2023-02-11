"""GitHub OAuth Views"""
from typing import Any

from requests.exceptions import RequestException

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class GitHubOAuthRedirect(OAuthRedirect):
    """GitHub OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["read:user", "user:email"],
        }


class GitHubOAuth2Client(OAuth2Client):
    """GitHub OAuth2 Client"""

    def get_github_emails(self, token: dict[str, str]) -> list[dict[str, Any]]:
        """Get Emails from the GitHub API"""
        profile_url = self.source.type.profile_url or ""
        if self.source.type.urls_customizable and self.source.profile_url:
            profile_url = self.source.profile_url
        profile_url += "/emails"
        response = self.do_request("get", profile_url, token=token)
        try:
            response.raise_for_status()
        except RequestException as exc:
            self.logger.warning("Unable to fetch github emails", exc=exc)
            return []
        return response.json()


class GitHubOAuth2Callback(OAuthCallback):
    """GitHub OAuth2 Callback"""

    client_class = GitHubOAuth2Client

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        chosen_email = info.get("email")
        if not chosen_email:
            # The GitHub Userprofile API only returns an email address if the profile
            # has a public email address set (despite us asking for user:email, this behaviour
            # doesn't change.). So we fetch all the user's email addresses
            client: GitHubOAuth2Client = self.get_client(self.source)
            emails = client.get_github_emails(self.token)
            for email in emails:
                if email.get("primary", False):
                    chosen_email = email.get("email", None)
        return {
            "username": info.get("login"),
            "email": chosen_email,
            "name": info.get("name"),
        }


@registry.register()
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
