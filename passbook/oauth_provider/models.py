"""Oauth2 provider product extension"""

from django.shortcuts import reverse
from django.utils.translation import gettext as _
from oauth2_provider.models import AbstractApplication

from passbook.core.models import Provider


class OAuth2Provider(Provider, AbstractApplication):
    """Associate an OAuth2 Application with a Product"""

    form = 'passbook.oauth_provider.forms.OAuth2ProviderForm'

    def __str__(self):
        return "OAuth2 Provider %s" % self.name

    def html_setup_urls(self, request):
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        return "oauth2_provider/setup_url_modal.html", {
            'provider': self,
            'authorize_url': request.build_absolute_uri(
                reverse('passbook_oauth_provider:oauth2-authorize')),
            'token_url': request.build_absolute_uri(
                reverse('passbook_oauth_provider:token')),
            'userinfo_url': request.build_absolute_uri(
                reverse('passbook_api:openid')),
        }

    class Meta:

        verbose_name = _('OAuth2 Provider')
        verbose_name_plural = _('OAuth2 Providers')
