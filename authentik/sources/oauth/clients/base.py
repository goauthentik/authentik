"""OAuth Clients"""

from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse

from django.http import HttpRequest
from requests import Session
from requests.exceptions import RequestException
from requests.models import Response
from structlog.stdlib import get_logger

from authentik.common.utils.http import get_http_session
from authentik.events.models import Event, EventAction
from authentik.sources.oauth.models import OAuthSource


class BaseOAuthClient:
    """Base OAuth Client"""

    session: Session

    source: OAuthSource
    request: HttpRequest

    callback: str | None

    def __init__(self, source: OAuthSource, request: HttpRequest, callback: str | None = None):
        self.source = source
        self.session = get_http_session()
        self.request = request
        self.callback = callback
        self.logger = get_logger().bind(source=source.slug)

    def get_access_token(self, **request_kwargs) -> dict[str, Any] | None:
        """Fetch access token from callback request."""
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_profile_info(self, token: dict[str, str]) -> dict[str, Any] | None:
        """Fetch user profile information."""
        profile_url = self.source.source_type.profile_url or ""
        if self.source.source_type.urls_customizable and self.source.profile_url:
            profile_url = self.source.profile_url
        response = self.do_request("get", profile_url, token=token)
        try:
            response.raise_for_status()
        except RequestException as exc:
            self.logger.warning(
                "Unable to fetch user profile",
                exc=exc,
                response=exc.response.text if exc.response else str(exc),
            )
            return None
        return response.json()

    def get_redirect_args(self) -> dict[str, str]:
        """Get request parameters for redirect url."""
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_redirect_url(self, parameters=None):
        """Build authentication redirect url."""
        authorization_url = self.source.source_type.authorization_url or ""
        if self.source.source_type.urls_customizable and self.source.authorization_url:
            authorization_url = self.source.authorization_url
        if authorization_url == "":
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                source=self.source,
                message="Source has an empty authorization URL.",
            ).save()
        parsed_url = urlparse(authorization_url)
        parsed_args = parse_qs(parsed_url.query)
        args = self.get_redirect_args()
        args.update(parameters or {})
        args.update(parsed_args)
        # Special handling for scope, since it's set as array
        # to make additional scopes easier
        args["scope"] = " ".join(sorted(set(args["scope"])))
        params = urlencode(args, quote_via=quote, doseq=True)
        self.logger.info("redirect args", **args)
        return urlunparse(parsed_url._replace(query=params))

    def parse_raw_token(self, raw_token: str) -> dict[str, Any]:
        """Parse token and secret from raw token response."""
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def do_request(self, method: str, url: str, **kwargs) -> Response:
        """Wrapper around self.session.request, which can add special headers"""
        return self.session.request(method, url, **kwargs)

    @property
    def session_key(self) -> str:
        """Return Session Key"""
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover
