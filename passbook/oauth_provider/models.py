"""Oauth2 provider product extension"""

from oauth2_provider.models import AbstractApplication

from passbook.core.models import Provider


class OAuth2Provider(Provider, AbstractApplication):
    """Associate an OAuth2 Application with a Product"""

    def __str__(self):
        return self.name
