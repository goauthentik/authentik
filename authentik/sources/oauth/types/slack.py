"""Slack OAuth Views"""

from typing import Any

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class SlackOAuthClient(OAuth2Client):
    """Slack OAuth2 Client that handles Slack's nested token response.

    Slack's oauth.v2.access returns tokens in a nested structure:
    {
        "ok": true,
        "access_token": "xoxb-...",  # bot token
        "refresh_token": "xoxe-1-...",  # bot refresh token (if rotation enabled)
        "authed_user": {
            "id": "U1234",
            "scope": "...",
            "access_token": "xoxp-...",  # user token
            "refresh_token": "xoxe-1-...",  # user refresh token (if rotation enabled)
            "token_type": "user",
            "expires_in": 43200
        }
    }

    For user scopes (like admin for SCIM), we need the authed_user token.
    """

    def get_access_token(self, **request_kwargs) -> dict[str, Any] | None:
        """Fetch access token and normalize Slack's nested response."""
        token = super().get_access_token(**request_kwargs)
        if token is None or "error" in token:
            return token

        # If we have authed_user with access_token, use that (user token)
        # This is needed for user scopes like 'admin' for SCIM
        if "authed_user" in token and "access_token" in token.get("authed_user", {}):
            authed_user = token["authed_user"]
            # Flatten the authed_user token to top level for compatibility
            token["access_token"] = authed_user["access_token"]
            # Always use "Bearer" for Authorization header - Slack returns "user"
            # as token_type but their API still expects "Bearer" in the header
            token["token_type"] = "Bearer"
            # Preserve refresh_token and expires_in for token rotation
            if "refresh_token" in authed_user:
                token["refresh_token"] = authed_user["refresh_token"]
            if "expires_in" in authed_user:
                token["expires_in"] = authed_user["expires_in"]
            # Preserve the user ID for profile lookup
            if "id" not in token:
                token["id"] = authed_user.get("id")
        elif "token_type" not in token:
            # Bot token - ensure token_type is set
            token["token_type"] = "Bearer"

        return token


class SlackOAuthRedirect(OAuthRedirect):
    """Slack OAuth2 Redirect

    Slack uses two separate scope parameters:
    - scope: Bot token scopes (xoxb- tokens)
    - user_scope: User token scopes (xoxp- tokens)

    For user authentication and SCIM (which needs 'admin' scope),
    we need scopes in user_scope, not scope.
    """

    def get_additional_parameters(self, source):
        # Start with base user scopes for authentication
        user_scopes = ["openid", "email", "profile"]

        # Add any additional scopes from the source config to user_scope
        # (not to scope, which is for bot tokens)
        if source.additional_scopes:
            additional = source.additional_scopes
            if additional.startswith("*"):
                additional = additional[1:]
            user_scopes.extend(additional.split())

        return {
            "scope": [],  # Bot scopes - empty for user auth
            "user_scope": user_scopes,
        }

    def get_redirect_url(self, **kwargs) -> str:
        """Build redirect URL with Slack-specific scope handling.

        Slack uses two separate scope parameters:
        - scope: Bot token scopes (xoxb- tokens)
        - user_scope: User token scopes (xoxp- tokens)

        The base class adds additional_scopes to 'scope', but Slack needs them
        in 'user_scope'. We override completely to handle this properly.
        """
        from django.http import Http404

        from authentik.sources.oauth.models import OAuthSource

        slug = kwargs.get("source_slug", "")
        try:
            source: OAuthSource = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.") from None
        if not source.enabled:
            raise Http404(f"source {slug} is not enabled.")

        client = self.get_client(source, callback=self.get_callback_url(source))
        # get_additional_parameters handles all scopes for Slack (both scope and user_scope)
        params = self.get_additional_parameters(source)
        params.update(self._try_login_hint_extract())
        return client.get_redirect_url(params)


class SlackOAuth2Callback(OAuthCallback):
    """Slack OAuth2 Callback"""

    client_class = SlackOAuthClient

    def get_user_id(self, info: dict[str, Any]) -> str | None:
        """Return unique identifier from Slack profile info."""
        # Slack uses 'sub' for OIDC or 'id'/'user_id' for standard OAuth
        return info.get("sub") or info.get("id") or info.get("user_id")


@registry.register()
class SlackType(SourceType):
    """Slack Type definition"""

    callback_view = SlackOAuth2Callback
    redirect_view = SlackOAuthRedirect
    verbose_name = "Slack"
    name = "slack"

    authorization_url = "https://slack.com/oauth/v2/authorize"
    access_token_url = "https://slack.com/api/oauth.v2.access"  # nosec
    profile_url = "https://slack.com/api/openid.connect.userInfo"
    oidc_well_known_url = "https://slack.com/.well-known/openid-configuration"
    oidc_jwks_url = "https://slack.com/openid/connect/keys"

    def get_base_user_properties(self, source, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("email", "").split("@")[0] or info.get("name"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
