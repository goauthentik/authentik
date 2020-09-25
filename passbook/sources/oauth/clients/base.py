"""OAuth Clients"""
from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import urlencode

from django.http import HttpRequest
from requests import Session
from requests.exceptions import RequestException
from structlog import get_logger

from passbook import __version__

LOGGER = get_logger()
if TYPE_CHECKING:
    from passbook.sources.oauth.models import OAuthSource


class BaseOAuthClient:
    """Base OAuth Client"""

    session: Session
    source: "OAuthSource"

    def __init__(self, source: "OAuthSource", token=""):  # nosec
        self.source = source
        self.token = token
        self.session = Session()
        self.session.headers.update({"User-Agent": "passbook %s" % __version__})

    def get_access_token(
        self, request: HttpRequest, callback=None
    ) -> Optional[Dict[str, Any]]:
        "Fetch access token from callback request."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_profile_info(self, token: Dict[str, str]) -> Optional[Dict[str, Any]]:
        "Fetch user profile information."
        try:
            headers = {
                "Authorization": f"{token['token_type']} {token['access_token']}"
            }
            response = self.session.request(
                "get", self.source.profile_url, headers=headers,
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user profile", exc=exc)
            return None
        else:
            return response.json()

    def get_redirect_args(self, request, callback) -> Dict[str, str]:
        "Get request parameters for redirect url."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_redirect_url(self, request: HttpRequest, callback: str, parameters=None):
        "Build authentication redirect url."
        args = self.get_redirect_args(request, callback=callback)
        additional = parameters or {}
        args.update(additional)
        params = urlencode(args)
        LOGGER.info("redirect args", **args)
        return "{0}?{1}".format(self.source.authorization_url, params)

    def parse_raw_token(self, raw_token):
        "Parse token and secret from raw token response."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    @property
    def session_key(self):
        """Return Session Key"""
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover
