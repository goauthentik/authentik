"""passbook app_gw models"""
import string
from random import SystemRandom
from typing import Optional

from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext as _
from oidc_provider.models import Client

from passbook import __version__
from passbook.core.models import Outlet
from passbook.lib.utils.template import render_to_string


class ApplicationGatewayOutlet(Outlet):
    """This outlet uses oauth2_proxy with the OIDC Outlet."""

    name = models.TextField()
    internal_host = models.TextField()
    external_host = models.TextField()

    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    form = "passbook.channels.out_app_gw.forms.ApplicationGatewayOutletForm"

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        cookie_secret = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(50)
        )
        return render_to_string(
            "app_gw/setup_modal.html",
            {"outlet": self, "cookie_secret": cookie_secret, "version": __version__},
        )

    def __str__(self):
        return f"Application Gateway {self.name}"

    class Meta:

        verbose_name = _("Application Gateway Outlet")
        verbose_name_plural = _("Application Gateway Outlets")
