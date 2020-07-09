"""OAuth Base views"""
from typing import Callable, Optional

from passbook.sources.oauth.clients import BaseOAuthClient, get_client
from passbook.sources.oauth.models import OAuthSource


# pylint: disable=too-few-public-methods
class OAuthClientMixin:
    "Mixin for getting OAuth client for a source."

    client_class: Optional[Callable] = None

    def get_client(self, source: OAuthSource) -> BaseOAuthClient:
        "Get instance of the OAuth client for this source."
        if self.client_class is not None:
            # pylint: disable=not-callable
            return self.client_class(source)
        return get_client(source)
