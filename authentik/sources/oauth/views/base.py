"""OAuth Base views"""

from typing import Optional

from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.base import BaseOAuthClient
from authentik.sources.oauth.clients.oauth1 import OAuthClient
from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource

LOGGER = get_logger()


# pylint: disable=too-few-public-methods
class OAuthClientMixin:
    "Mixin for getting OAuth client for a source."

    request: HttpRequest  # Set by View class

    client_class: Optional[type[BaseOAuthClient]] = None

    def get_client(self, source: OAuthSource, **kwargs) -> BaseOAuthClient:
        "Get instance of the OAuth client for this source."
        if self.client_class is not None:
            # pylint: disable=not-callable
            return self.client_class(source, self.request, **kwargs)
        if source.source_type.request_token_url or source.request_token_url:
            client = OAuthClient(source, self.request, **kwargs)
        else:
            client = OAuth2Client(source, self.request, **kwargs)
        LOGGER.debug("Using client for oauth request", client=client)
        return client
