"""oidc models"""
from typing import Optional

from django.db import models
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from oidc_provider.models import Client

from passbook.core.models import Provider
from passbook.lib.utils.template import render_to_string


class OpenIDProvider(Provider):
    """Proxy model for OIDC Client"""

    # Since oidc_provider doesn't currently support swappable models
    # (https://github.com/juanifioren/django-oidc-provider/pull/305)
    # we have a 1:1 relationship, and update oidc_client when the form is saved.

    oidc_client = models.OneToOneField(Client, on_delete=models.CASCADE)

    form = "passbook.providers.oidc.forms.OIDCProviderForm"

    @property
    def name(self):
        """Name property for UI"""
        return self.oidc_client.name

    def __str__(self):
        return "OpenID Connect Provider %s" % self.oidc_client.__str__()

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        return render_to_string(
            "oidc_provider/setup_url_modal.html",
            {
                "provider": self,
                "authorize": request.build_absolute_uri(
                    reverse("oidc_provider:authorize")
                ),
                "token": request.build_absolute_uri(reverse("oidc_provider:token")),
                "userinfo": request.build_absolute_uri(
                    reverse("oidc_provider:userinfo")
                ),
                "provider_info": request.build_absolute_uri(
                    reverse("oidc_provider:provider-info")
                ),
            },
        )

    class Meta:

        verbose_name = _("OpenID Provider")
        verbose_name_plural = _("OpenID Providers")
