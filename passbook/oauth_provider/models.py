"""Oauth2 provider product extension"""

from oauth2_provider.models import AbstractApplication

from passbook.core.models import Provider
from django.utils.translation import gettext as _


class OAuth2Provider(Provider, AbstractApplication):
    """Associate an OAuth2 Application with a Product"""

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _('OAuth2 Provider')
        verbose_name_plural = _('OAuth2 Providers')
