"""passbook proxy models"""
import string
from random import SystemRandom
from typing import Iterable, Optional, Type
from urllib.parse import urljoin

from django.core.validators import URLValidator
from django.db import models
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext as _

from passbook.crypto.models import CertificateKeyPair
from passbook.lib.utils.template import render_to_string
from passbook.outposts.models import OutpostModel
from passbook.providers.oauth2.constants import (
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from passbook.providers.oauth2.models import (
    ClientTypes,
    JWTAlgorithms,
    OAuth2Provider,
    ResponseTypes,
    ScopeMapping,
)


def get_cookie_secret():
    """Generate random 32-character string for cookie-secret"""
    return "".join(
        SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32)
    )


def _get_callback_url(uri: str) -> str:
    return urljoin(uri, "/pbprox/callback")


class ProxyProvider(OutpostModel, OAuth2Provider):
    """Protect applications that don't support any of the other
    Protocols by using a Reverse-Proxy."""

    internal_host = models.TextField(
        validators=[URLValidator(schemes=("http", "https"))]
    )
    external_host = models.TextField(
        validators=[URLValidator(schemes=("http", "https"))]
    )

    cookie_secret = models.TextField(default=get_cookie_secret)

    certificate = models.ForeignKey(
        CertificateKeyPair, on_delete=models.SET_NULL, null=True
    )

    def form(self) -> Type[ModelForm]:
        from passbook.providers.proxy.forms import ProxyProviderForm

        return ProxyProviderForm

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        from passbook.providers.proxy.views import DockerComposeView

        docker_compose_yaml = DockerComposeView(request=request).get_compose(self)
        return render_to_string(
            "providers/proxy/setup_modal.html",
            {"provider": self, "docker_compose": docker_compose_yaml},
        )

    def set_oauth_defaults(self):
        """Ensure all OAuth2-related settings are correct"""
        self.client_type = ClientTypes.CONFIDENTIAL
        self.response_type = ResponseTypes.CODE
        self.jwt_alg = JWTAlgorithms.RS256
        self.rsa_key = CertificateKeyPair.objects.first()
        scopes = ScopeMapping.objects.filter(
            scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL]
        )
        self.property_mappings.set(scopes)
        self.redirect_uris = "\n".join(
            [
                _get_callback_url(self.external_host),
                _get_callback_url(self.internal_host),
            ]
        )

    def __str__(self):
        return f"Proxy Provider {self.name}"

    def get_required_objects(self) -> Iterable[models.Model]:
        required_models = [self]
        if self.certificate is not None:
            required_models.append(self.certificate)
        return required_models

    class Meta:

        verbose_name = _("Proxy Provider")
        verbose_name_plural = _("Proxy Providers")
