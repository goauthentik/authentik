"""OAuth Clients"""
import json
from typing import Dict, Optional
from urllib.parse import parse_qs, urlencode

from django.http import HttpRequest
from django.utils.crypto import constant_time_compare, get_random_string
from django.utils.encoding import force_text
from requests import Session
from requests.exceptions import RequestException
from requests_oauthlib import OAuth1
from structlog import get_logger

from passbook import __version__

LOGGER = get_logger()


class BaseOAuthClient:
    """Base OAuth Client"""

    session: Session = None

    def __init__(self, source, token=""):  # nosec
        self.source = source
        self.token = token
        self.session = Session()
        self.session.headers.update({"User-Agent": "passbook %s" % __version__})

    def get_access_token(self, request, callback=None):
        "Fetch access token from callback request."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_profile_info(self, token: Dict[str, str]):
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
            return response.json() or response.text

    def get_redirect_args(self, request, callback) -> Dict[str, str]:
        "Get request parameters for redirect url."
        raise NotImplementedError("Defined in a sub-class")  # pragma: no cover

    def get_redirect_url(self, request, callback, parameters=None):
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


class OAuthClient(BaseOAuthClient):
    """OAuth1 Client"""

    _default_headers = {
        "Accept": "application/json",
    }

    def get_access_token(
        self, request: HttpRequest, callback=None
    ) -> Optional[Dict[str, str]]:
        "Fetch access token from callback request."
        raw_token = request.session.get(self.session_key, None)
        verifier = request.GET.get("oauth_verifier", None)
        if raw_token is not None and verifier is not None:
            data = {
                "oauth_verifier": verifier,
                "oauth_callback": callback,
                "token": raw_token,
            }
            callback = request.build_absolute_uri(callback or request.path)
            callback = force_text(callback)
            try:
                response = self.session.request(
                    "post",
                    self.source.access_token_url,
                    data=data,
                    headers=self._default_headers,
                )
                response.raise_for_status()
            except RequestException as exc:
                LOGGER.warning("Unable to fetch access token", exc=exc)
                return None
            else:
                return response.json()
        return None

    def get_request_token(self, request, callback):
        "Fetch the OAuth request token. Only required for OAuth 1.0."
        callback = force_text(request.build_absolute_uri(callback))
        try:
            response = self.session.request(
                "post",
                self.source.request_token_url,
                data={"oauth_callback": callback},
                headers=self._default_headers,
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch request token", exc=exc)
            return None
        else:
            return response.text

    def get_redirect_args(self, request, callback):
        "Get request parameters for redirect url."
        callback = force_text(request.build_absolute_uri(callback))
        raw_token = self.get_request_token(request, callback)
        token, secret = self.parse_raw_token(raw_token)
        if token is not None and secret is not None:
            request.session[self.session_key] = raw_token
        return {
            "oauth_token": token,
            "oauth_callback": callback,
        }

    def parse_raw_token(self, raw_token):
        "Parse token and secret from raw token response."
        if raw_token is None:
            return (None, None)
        query_string = parse_qs(raw_token)
        token = query_string.get("oauth_token", [None])[0]
        secret = query_string.get("oauth_token_secret", [None])[0]
        return (token, secret)

    def request(self, method, url, **kwargs):
        "Build remote url request. Constructs necessary auth."
        user_token = kwargs.pop("token", self.token)
        token, secret = self.parse_raw_token(user_token)
        callback = kwargs.pop("oauth_callback", None)
        verifier = kwargs.get("data", {}).pop("oauth_verifier", None)
        oauth = OAuth1(
            resource_owner_key=token,
            resource_owner_secret=secret,
            client_key=self.source.consumer_key,
            client_secret=self.source.consumer_secret,
            verifier=verifier,
            callback_uri=callback,
        )
        kwargs["auth"] = oauth
        return super(OAuthClient, self).session.request(method, url, **kwargs)

    @property
    def session_key(self):
        return "oauth-client-{0}-request-token".format(self.source.name)


class OAuth2Client(BaseOAuthClient):
    """OAuth2 Client"""

    _default_headers = {
        "Accept": "application/json",
    }

    # pylint: disable=unused-argument
    def check_application_state(self, request, callback):
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

    def get_access_token(self, request, callback=None, **request_kwargs):
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
    def get_application_state(self, request, callback):
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


def get_client(source, token=""):  # nosec
    "Return the API client for the given source."
    cls = OAuth2Client
    if source.request_token_url:
        cls = OAuthClient
    return cls(source, token)
