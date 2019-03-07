"""Oauth2 provider product extension"""

from django.utils.translation import gettext as _
from oauth2_provider.models import AbstractApplication

from passbook.core.models import Provider


class OAuth2Provider(Provider, AbstractApplication):
    """Associate an OAuth2 Application with a Product"""

    form = 'passbook.oauth_provider.forms.OAuth2ProviderForm'

    def __str__(self):
        return "OAuth2 Provider %s" % self.name

    class Meta:

        verbose_name = _('OAuth2 Provider')
        verbose_name_plural = _('OAuth2 Providers')
