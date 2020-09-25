"""OAuth Clients"""
from typing import Dict, Optional
from urllib.parse import parse_qs

from django.http import HttpRequest
from django.utils.encoding import force_str
from requests.exceptions import RequestException
from requests_oauthlib import OAuth1
from structlog import get_logger

from passbook import __version__
from passbook.sources.oauth.clients.base import BaseOAuthClient

LOGGER = get_logger()


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

    def get_request_token(self, request: HttpRequest, callback):
        "Fetch the OAuth request token. Only required for OAuth 1.0."
        callback = request.build_absolute_uri(callback)
        try:
            response = self.session.request(
                "post",
                self.source.request_token_url,
                data={
                    "oauth_callback": callback,
                    "oauth_consumer_key": self.source.consumer_key,
                },
                headers=self._default_headers,
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch request token", exc=exc)
            return None
        else:
            return response.text

    def get_redirect_args(self, request: HttpRequest, callback):
        "Get request parameters for redirect url."
        callback = force_str(request.build_absolute_uri(callback))
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
