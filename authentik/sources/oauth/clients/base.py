"""OAuth Clients"""
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from django.http import HttpRequest
from requests import Session
from requests.exceptions import RequestException
from requests.models import Response
from structlog import get_logger

from authentik import __version__
from authentik.sources.oauth.models import OAuthSource

LOGGER = get_logger()


class BaseOAuthClient:
    """Base OAuth Client"""

    session: Session

    source: OAuthSource
    request: HttpRequest

    callback: Optional[str]

    def __init__(
        self, source: OAuthSource, request: HttpRequest, callback: Optional[str] = None
    ):
        self.source = source
        self.session = Session()
        self.request = request
        self.callback = callback
        self.session.headers.update({"User-Agent": f"authentik {__version__}"})

    def get_access_token(self, **request_kwargs) -> Optional[Dict[str, Any]]:
        "Fetch access token from callback request."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_profile_info(self, token: Dict[str, str]) -> Optional[Dict[str, Any]]:
        "Fetch user profile information."
        try:
            response = self.do_request("get", self.source.profile_url, token=token)
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user profile", exc=exc)
            return None
        else:
            return response.json()

    def get_redirect_args(self) -> Dict[str, str]:
        "Get request parameters for redirect url."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_redirect_url(self, parameters=None):
        "Build authentication redirect url."
        args = self.get_redirect_args()
        additional = parameters or {}
        args.update(additional)
        params = urlencode(args)
        LOGGER.info("redirect args", **args)
        return f"{self.source.authorization_url}?{params}"

    def parse_raw_token(self, raw_token: str) -> Dict[str, Any]:
        "Parse token and secret from raw token response."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def do_request(self, method: str, url: str, **kwargs) -> Response:
        """Wrapper around self.session.request, which can add special headers"""
        return self.session.request(method, url, **kwargs)

    @property
    def session_key(self) -> str:
        """Return Session Key"""
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover
