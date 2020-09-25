"""OAuth Clients"""
import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple
from urllib.parse import parse_qs

from django.http import HttpRequest
from django.utils.crypto import constant_time_compare, get_random_string
from requests.exceptions import RequestException
from requests.models import Response
from structlog import get_logger

from passbook import __version__
from passbook.sources.oauth.clients.base import BaseOAuthClient

LOGGER = get_logger()
if TYPE_CHECKING:
    from passbook.sources.oauth.models import OAuthSource


class OAuth2Client(BaseOAuthClient):
    """OAuth2 Client"""

    _default_headers = {
        "Accept": "application/json",
    }

    def check_application_state(self) -> bool:
        "Check optional state parameter."
        stored = self.request.session.get(self.session_key, None)
        returned = self.request.GET.get("state", None)
        check = False
        if stored is not None:
            if returned is not None:
                check = constant_time_compare(stored, returned)
            else:
                LOGGER.warning("No state parameter returned by the source.")
        else:
            LOGGER.warning("No state stored in the session.")
        return check

    def get_application_state(self) -> str:
        "Generate state optional parameter."
        return get_random_string(32)

    def get_access_token(self, **request_kwargs) -> Optional[Dict[str, Any]]:
        "Fetch access token from callback request."
        callback = self.request.build_absolute_uri(self.callback or self.request.path)
        if not self.check_application_state():
            LOGGER.warning("Application state check failed.")
            return None
        if "code" in self.request.GET:
            args = {
                "client_id": self.source.consumer_key,
                "redirect_uri": callback,
                "client_secret": self.source.consumer_secret,
                "code": self.request.GET["code"],
                "grant_type": "authorization_code",
            }
        else:
            LOGGER.warning("No code returned by the source")
            return None
        try:
            response = self.session.request(
                "post",
                self.source.access_token_url,
                data=args,
                headers=self._default_headers,
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch access token", exc=exc)
            return None
        else:
            return response.json()

    def get_redirect_args(self) -> Dict[str, str]:
        "Get request parameters for redirect url."
        callback = self.request.build_absolute_uri(self.callback)
        client_id: str = self.source.consumer_key
        args: Dict[str, str] = {
            "client_id": client_id,
            "redirect_uri": callback,
            "response_type": "code",
        }
        state = self.get_application_state()
        if state is not None:
            args["state"] = state
            self.request.session[self.session_key] = state
        return args

    def parse_raw_token(self, raw_token: str) -> Tuple[str, Optional[str]]:
        "Parse token and secret from raw token response."
        # Load as json first then parse as query string
        try:
            token_data = json.loads(raw_token)
        except ValueError:
            token = parse_qs(raw_token)["access_token"][0]
        else:
            token = token_data["access_token"]
        return (token, None)

    def do_request(self, method: str, url: str, **kwargs) -> Response:
        "Build remote url request. Constructs necessary auth."
        user_token = kwargs.pop("token", self.token)
        token, _ = self.parse_raw_token(user_token)
        if token is not None:
            params = kwargs.get("params", {})
            params["access_token"] = token
            kwargs["params"] = params
        return super().do_request(method, url, **kwargs)

    @property
    def session_key(self):
        return "oauth-client-{0}-request-state".format(self.source.name)
