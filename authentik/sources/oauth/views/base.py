"""OAuth Base views"""
from typing import Optional, Type

from django.http.request import HttpRequest

from authentik.sources.oauth.clients.base import BaseOAuthClient
from authentik.sources.oauth.clients.oauth1 import OAuthClient
from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource


# pylint: disable=too-few-public-methods
class OAuthClientMixin:
    "Mixin for getting OAuth client for a source."

    request: HttpRequest  # Set by View class

    client_class: Optional[Type[BaseOAuthClient]] = None

    def get_client(self, source: OAuthSource, **kwargs) -> BaseOAuthClient:
        "Get instance of the OAuth client for this source."
        if self.client_class is not None:
            # pylint: disable=not-callable
            return self.client_class(source, self.request, **kwargs)
        if source.request_token_url:
            return OAuthClient(source, self.request, **kwargs)
        return OAuth2Client(source, self.request, **kwargs)
