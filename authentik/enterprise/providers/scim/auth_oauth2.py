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

    def __init__(self, provider: SCIMProvider):
        self.provider = provider
        self.user = provider.auth_oauth_user
        self.logger = get_logger().bind()
        self.connection = self.get_connection()

    def retrieve_token(self):
        if not self.provider.auth_oauth:
            return None
        source: OAuthSource = self.provider.auth_oauth
        client = OAuth2Client(source, None)
        access_token_url = source.source_type.access_token_url or ""
        if source.source_type.urls_customizable and source.access_token_url:
            access_token_url = source.access_token_url
        data = client.get_access_token_args(None, None)
        data["grant_type"] = "password"
        data.update(self.provider.auth_oauth_params)
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
                self.logger.info("Failed to get new OAuth token", error=body["error"])
                raise SCIMOAuthException(response, body["error"])
            return body
        except RequestException as exc:
            raise SCIMOAuthException(exc.response, message="Failed to get OAuth token") from exc

    def get_connection(self):
        token = UserOAuthSourceConnection.objects.filter(
            source=self.provider.auth_oauth, user=self.user, expires__gt=now()
        ).first()
        if token and token.access_token:
            return token
        token = self.retrieve_token()
        access_token = token["access_token"]
        expires_in = int(token.get("expires_in", 0))
        token, _ = UserOAuthSourceConnection.objects.update_or_create(
            source=self.provider.auth_oauth,
            user=self.user,
            defaults={
                "access_token": access_token,
                "expires": now() + timedelta(seconds=expires_in),
            },
        )
        return token

    def __call__(self, request: Request) -> Request:
        if not self.connection.is_valid:
            self.logger.info("OAuth token expired, renewing token")
            self.connection = self.get_connection()
        request.headers["Authorization"] = f"Bearer {self.connection.access_token}"
        return request
