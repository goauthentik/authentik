"""passbook app_gw models"""
import string
from random import SystemRandom
from typing import Optional, Type

from django.core.validators import URLValidator
from django.db import models
from django.forms import ModelForm
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from oidc_provider.models import Client

from passbook import __version__
from passbook.core.models import Provider
from passbook.lib.utils.template import render_to_string


class ApplicationGatewayProvider(Provider):
    """Protect applications that don't support any of the other
    Protocols by using a Reverse-Proxy."""

    name = models.TextField()
    internal_host = models.TextField(validators=[URLValidator])
    external_host = models.TextField(validators=[URLValidator])

    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def form(self) -> Type[ModelForm]:
        from passbook.providers.app_gw.forms import ApplicationGatewayProviderForm

        return ApplicationGatewayProviderForm

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        cookie_secret = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(50)
        )
        full_issuer_user = request.build_absolute_uri(
            reverse("passbook_providers_oidc:authorize")
        )
        return render_to_string(
            "app_gw/setup_modal.html",
            {
                "provider": self,
                "cookie_secret": cookie_secret,
                "version": __version__,
                "full_issuer_user": full_issuer_user,
            },
        )

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _("Application Gateway Provider")
        verbose_name_plural = _("Application Gateway Providers")
