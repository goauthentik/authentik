"""OAuth 1 Clients"""
from typing import Any, Optional
from urllib.parse import parse_qsl

from requests.exceptions import RequestException
from requests.models import Response
from requests_oauthlib import OAuth1
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.base import BaseOAuthClient
from authentik.sources.oauth.exceptions import OAuthSourceException

LOGGER = get_logger()


class OAuthClient(BaseOAuthClient):
    """OAuth1 Client"""

    _default_headers = {
        "Accept": "application/json",
    }

    def get_access_token(self, **request_kwargs) -> Optional[dict[str, Any]]:
        """Fetch access token from callback request."""
        raw_token = self.request.session.get(self.session_key, None)
        verifier = self.request.GET.get("oauth_verifier", None)
        callback = self.request.build_absolute_uri(self.callback)
        if raw_token is not None and verifier is not None:
            token = self.parse_raw_token(raw_token)
            try:
                access_token_url = self.source.type.access_token_url or ""
                if self.source.type.urls_customizable and self.source.access_token_url:
                    access_token_url = self.source.access_token_url
                response = self.do_request(
                    "post",
                    access_token_url,
                    token=token,
                    headers=self._default_headers,
                    oauth_verifier=verifier,
                    oauth_callback=callback,
                )
                response.raise_for_status()
            except RequestException as exc:
                LOGGER.warning(
                    "Unable to fetch access token",
                    exc=exc,
                    response=exc.response.text if exc.response else str(exc),
                )
                return None
            return self.parse_raw_token(response.text)
        return None

    def get_request_token(self) -> str:
        """Fetch the OAuth request token. Only required for OAuth 1.0."""
        callback = self.request.build_absolute_uri(self.callback)
        try:
            request_token_url = self.source.type.request_token_url or ""
            if self.source.type.urls_customizable and self.source.request_token_url:
                request_token_url = self.source.request_token_url
            response = self.do_request(
                "post",
                request_token_url,
                headers=self._default_headers,
                oauth_callback=callback,
            )
            response.raise_for_status()
        except RequestException as exc:
            raise OAuthSourceException(
                exc.response.text if exc.response else str(exc),
            ) from exc
        return response.text

    def get_redirect_args(self) -> dict[str, Any]:
        """Get request parameters for redirect url."""
        callback = self.request.build_absolute_uri(self.callback)
        raw_token = self.get_request_token()
        token = self.parse_raw_token(raw_token)
        self.request.session[self.session_key] = raw_token
        return {
            "oauth_token": token["oauth_token"],
            "oauth_callback": callback,
        }

    def parse_raw_token(self, raw_token: str) -> dict[str, Any]:
        """Parse token and secret from raw token response."""
        return dict(parse_qsl(raw_token))

    def do_request(self, method: str, url: str, **kwargs) -> Response:
        """Build remote url request. Constructs necessary auth."""
        resource_owner_key = None
        resource_owner_secret = None
        if "token" in kwargs:
            user_token: dict[str, Any] = kwargs.pop("token")
            resource_owner_key = user_token["oauth_token"]
            resource_owner_secret = user_token["oauth_token_secret"]

        callback = kwargs.pop("oauth_callback", None)
        verifier = kwargs.pop("oauth_verifier", None)
        oauth = OAuth1(
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            client_key=self.source.consumer_key,
            client_secret=self.source.consumer_secret,
            verifier=verifier,
            callback_uri=callback,
        )
        kwargs["auth"] = oauth
        return super().do_request(method, url, **kwargs)

    @property
    def session_key(self) -> str:
        return f"oauth-client-{self.source.name}-request-token"
