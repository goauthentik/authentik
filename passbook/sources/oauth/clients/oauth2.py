"""OAuth Clients"""
import json
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from django.http import HttpRequest
from django.utils.crypto import constant_time_compare, get_random_string
from requests.exceptions import RequestException
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

    # pylint: disable=unused-argument
    def check_application_state(self, request: HttpRequest, callback: str):
        "Check optional state parameter."
        stored = request.session.get(self.session_key, None)
        returned = request.GET.get("state", None)
        check = False
        if stored is not None:
            if returned is not None:
                check = constant_time_compare(stored, returned)
            else:
                LOGGER.warning("No state parameter returned by the source.")
        else:
            LOGGER.warning("No state stored in the sesssion.")
        return check

    def get_access_token(self, request: HttpRequest, callback=None, **request_kwargs):
        "Fetch access token from callback request."
        callback = request.build_absolute_uri(callback or request.path)
        if not self.check_application_state(request, callback):
            LOGGER.warning("Application state check failed.")
            return None
        if "code" in request.GET:
            args = {
                "client_id": self.source.consumer_key,
                "redirect_uri": callback,
                "client_secret": self.source.consumer_secret,
                "code": request.GET["code"],
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
                **request_kwargs,
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch access token", exc=exc)
            return None
        else:
            return response.json()

    # pylint: disable=unused-argument
    def get_application_state(self, request: HttpRequest, callback):
        "Generate state optional parameter."
        return get_random_string(32)

    def get_redirect_args(self, request, callback):
        "Get request parameters for redirect url."
        callback = request.build_absolute_uri(callback)
        args = {
            "client_id": self.source.consumer_key,
            "redirect_uri": callback,
            "response_type": "code",
        }
        state = self.get_application_state(request, callback)
        if state is not None:
            args["state"] = state
            request.session[self.session_key] = state
        return args

    def parse_raw_token(self, raw_token):
        "Parse token and secret from raw token response."
        if raw_token is None:
            return (None, None)
        # Load as json first then parse as query string
        try:
            token_data = json.loads(raw_token)
        except ValueError:
            token = parse_qs(raw_token).get("access_token", [None])[0]
        else:
            token = token_data.get("access_token", None)
        return (token, None)

    def request(self, method, url, **kwargs):
        "Build remote url request. Constructs necessary auth."
        user_token = kwargs.pop("token", self.token)
        token, _ = self.parse_raw_token(user_token)
        if token is not None:
            params = kwargs.get("params", {})
            params["access_token"] = token
            kwargs["params"] = params
        return super(OAuth2Client, self).session.request(method, url, **kwargs)

    @property
    def session_key(self):
        return "oauth-client-{0}-request-state".format(self.source.name)
