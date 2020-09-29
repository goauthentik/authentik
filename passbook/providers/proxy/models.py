"""passbook proxy models"""
import string
from random import SystemRandom
from typing import Iterable, Type
from urllib.parse import urljoin

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext as _

from passbook.crypto.models import CertificateKeyPair
from passbook.lib.models import DomainlessURLValidator
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
        validators=[DomainlessURLValidator(schemes=("http", "https"))]
    )
    external_host = models.TextField(
        validators=[DomainlessURLValidator(schemes=("http", "https"))]
    )
    internal_host_ssl_validation = models.BooleanField(
        default=True, help_text=_("Validate SSL Certificates of upstream servers")
    )

    skip_path_regex = models.TextField(
        default="",
        blank=True,
        help_text=_(
            (
                "Regular expressions for which authentication is not required. "
                "Each new line is interpreted as a new Regular Expression."
            )
        ),
    )

    certificate = models.ForeignKey(
        CertificateKeyPair, on_delete=models.SET_NULL, null=True, blank=True,
    )

    cookie_secret = models.TextField(default=get_cookie_secret)

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.providers.proxy.forms import ProxyProviderForm

        return ProxyProviderForm

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
