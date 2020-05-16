"""Oauth2 provider product extension"""

from typing import Optional

from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from oauth2_provider.models import AbstractApplication

from passbook.core.models import Provider
from passbook.lib.utils.template import render_to_string


class OAuth2Provider(Provider, AbstractApplication):
    """Associate an OAuth2 Application with a Product"""

    form = "passbook.providers.oauth.forms.OAuth2ProviderForm"

    def __str__(self):
        return f"OAuth2 Provider {self.name}"

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        return render_to_string(
            "oauth2_provider/setup_url_modal.html",
            {
                "provider": self,
                "authorize_url": request.build_absolute_uri(
                    reverse("passbook_providers_oauth:oauth2-authorize")
                ),
                "token_url": request.build_absolute_uri(
                    reverse("passbook_providers_oauth:token")
                ),
                "userinfo_url": request.build_absolute_uri(
                    reverse("passbook_api:openid")
                ),
            },
        )

    class Meta:

        verbose_name = _("OAuth2 Provider")
        verbose_name_plural = _("OAuth2 Providers")
