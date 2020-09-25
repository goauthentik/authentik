"""OAuth Base views"""
from typing import Optional, Type

from passbook.sources.oauth.clients.base import BaseOAuthClient
from passbook.sources.oauth.clients.oauth1 import OAuthClient
from passbook.sources.oauth.clients.oauth2 import OAuth2Client
from passbook.sources.oauth.models import OAuthSource


# pylint: disable=too-few-public-methods
class OAuthClientMixin:
    "Mixin for getting OAuth client for a source."

    client_class: Optional[Type[BaseOAuthClient]] = None

    def get_client(self, source: OAuthSource) -> BaseOAuthClient:
        "Get instance of the OAuth client for this source."
        if self.client_class is not None:
            # pylint: disable=not-callable
            return self.client_class(source)
        if source.request_token_url:
            return OAuthClient(source)
        return OAuth2Client(source)
