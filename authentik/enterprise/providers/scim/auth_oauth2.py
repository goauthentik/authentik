from datetime import timedelta
from typing import TYPE_CHECKING

from django.utils.timezone import now
from requests import Request, RequestException
from structlog.stdlib import get_logger

from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection

if TYPE_CHECKING:
    from authentik.providers.scim.models import SCIMProvider


class SCIMOAuthException(SCIMRequestException):
    """Exceptions related to OAuth operations for SCIM requests"""


class SCIMOAuthAuth:

    def __init__(self, provider: "SCIMProvider"):
        self.provider = provider
        self.user = provider.auth_oauth_user
        self.logger = get_logger().bind()
        self.connection = self.get_connection()

    def refresh_token(self, connection: UserOAuthSourceConnection) -> dict:
        """Refresh an expired token using refresh_token grant.

        This is the proper OAuth 2.0 way to get a new access token when the
        current one expires. Requires a refresh_token to be stored.
        """
        if not connection.refresh_token:
            raise SCIMOAuthException(
                None,
                "No refresh token available. User must re-authenticate via OAuth source.",
            )

        source: OAuthSource = self.provider.auth_oauth
        client = OAuth2Client(source, None)
        access_token_url = source.source_type.access_token_url or ""
        if source.source_type.urls_customizable and source.access_token_url:
            access_token_url = source.access_token_url

        data = {
            "grant_type": "refresh_token",
            "refresh_token": connection.refresh_token,
            "client_id": source.consumer_key,
            "client_secret": source.consumer_secret,
        }

        try:
            response = client.do_request(
                "POST",
                access_token_url,
                auth=client.get_access_token_auth(),
                data=data,
                headers=client._default_headers,
            )
            response.raise_for_status()
            body = response.json()
            if "error" in body:
                self.logger.info("Failed to refresh OAuth token", error=body["error"])
                raise SCIMOAuthException(response, body["error"])
            return body
        except RequestException as exc:
            raise SCIMOAuthException(exc.response, message="Failed to refresh OAuth token") from exc

    def get_connection(self) -> UserOAuthSourceConnection:
        """Get a valid OAuth connection, refreshing if necessary."""
        # First, try to get an existing valid (non-expired) token
        connection = UserOAuthSourceConnection.objects.filter(
            source=self.provider.auth_oauth, user=self.user, expires__gt=now()
        ).first()
        if connection and connection.access_token:
            return connection

        # Token expired or doesn't exist - try to find one with a refresh_token
        connection = UserOAuthSourceConnection.objects.filter(
            source=self.provider.auth_oauth, user=self.user
        ).first()

        if not connection:
            raise SCIMOAuthException(
                None,
                "No OAuth connection found. User must authenticate via OAuth source first.",
            )

        if not connection.refresh_token:
            # No refresh token - for providers like Slack with long-lived tokens,
            # the token might still be valid even if our expires field says otherwise
            if connection.access_token:
                self.logger.warning(
                    "Token expired but no refresh_token available. "
                    "Attempting to use existing token (may fail)."
                )
                return connection
            raise SCIMOAuthException(
                None,
                "OAuth token expired and no refresh token available. "
                "User must re-authenticate via OAuth source.",
            )

        # Refresh the token
        self.logger.info("Refreshing expired OAuth token")
        token_response = self.refresh_token(connection)

        # Update the connection with new tokens
        connection.access_token = token_response["access_token"]
        # Some providers return a new refresh_token with each refresh
        if "refresh_token" in token_response:
            connection.refresh_token = token_response["refresh_token"]
        expires_in = int(token_response.get("expires_in", 0))
        connection.expires = now() + timedelta(seconds=expires_in) if expires_in else now()
        connection.save()

        return connection

    def __call__(self, request: Request) -> Request:
        if not self.connection.is_valid:
            self.logger.info("OAuth token expired, renewing token")
            self.connection = self.get_connection()
        request.headers["Authorization"] = f"Bearer {self.connection.access_token}"
        return request
