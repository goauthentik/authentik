"""authentik proxy models"""

import string
from collections.abc import Iterable
from random import SystemRandom
from urllib.parse import urljoin
from uuid import uuid4

from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer

from authentik.core.models import ExpiringModel
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.models import DomainlessURLValidator
from authentik.outposts.models import OutpostModel
from authentik.providers.oauth2.models import (
    ClientTypes,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)

SCOPE_AK_PROXY = "ak_proxy"
OUTPOST_CALLBACK_SIGNATURE = "X-authentik-auth-callback"


def get_cookie_secret():
    """Generate random 32-character string for cookie-secret"""
    return "".join(SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))


def _get_callback_url(uri: str) -> list[RedirectURI]:
    return [
        RedirectURI(
            RedirectURIMatchingMode.STRICT,
            urljoin(uri, "outpost.goauthentik.io/callback") + f"?{OUTPOST_CALLBACK_SIGNATURE}=true",
        ),
        RedirectURI(RedirectURIMatchingMode.STRICT, uri + f"?{OUTPOST_CALLBACK_SIGNATURE}=true"),
    ]


class ProxyMode(models.TextChoices):
    """All modes a Proxy provider can operate in"""

    PROXY = "proxy"
    FORWARD_SINGLE = "forward_single"
    FORWARD_DOMAIN = "forward_domain"


class ProxyProvider(OutpostModel, OAuth2Provider):
    """Protect applications that don't support any of the other
    Protocols by using a Reverse-Proxy."""

    internal_host = models.TextField(
        validators=[DomainlessURLValidator(schemes=("http", "https"))],
        blank=True,
    )
    external_host = models.TextField(validators=[DomainlessURLValidator(schemes=("http", "https"))])
    internal_host_ssl_validation = models.BooleanField(
        default=True,
        help_text=_("Validate SSL Certificates of upstream servers"),
        verbose_name=_("Internal host SSL Validation"),
    )
    mode = models.TextField(
        default=ProxyMode.PROXY,
        choices=ProxyMode.choices,
        help_text=_(
            "Enable support for forwardAuth in traefik and nginx auth_request. Exclusive with "
            "internal_host."
        ),
    )

    skip_path_regex = models.TextField(
        default="",
        blank=True,
        help_text=_(
            "Regular expressions for which authentication is not required. "
            "Each new line is interpreted as a new Regular Expression."
        ),
    )

    intercept_header_auth = models.BooleanField(
        default=True,
        help_text=_(
            "When enabled, this provider will intercept the authorization header and authenticate "
            "requests based on its value."
        ),
    )
    basic_auth_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Set HTTP-Basic Authentication"),
        help_text=_(
            "Set a custom HTTP-Basic Authentication header based on values from authentik."
        ),
    )
    basic_auth_user_attribute = models.TextField(
        blank=True,
        verbose_name=_("HTTP-Basic Username Key"),
        help_text=_(
            "User/Group Attribute used for the user part of the HTTP-Basic Header. "
            "If not set, the user's Email address is used."
        ),
    )
    basic_auth_password_attribute = models.TextField(
        blank=True,
        verbose_name=_("HTTP-Basic Password Key"),
        help_text=_("User/Group Attribute used for the password part of the HTTP-Basic Header."),
    )

    certificate = models.ForeignKey(
        CertificateKeyPair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    cookie_secret = models.TextField(default=get_cookie_secret)
    cookie_domain = models.TextField(default="", blank=True)

    @property
    def component(self) -> str:
        return "ak-provider-proxy-form"

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/proxy.svg")

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.proxy.api import ProxyProviderSerializer

        return ProxyProviderSerializer

    @property
    def launch_url(self) -> str | None:
        """Use external_host as launch URL"""
        return self.external_host

    def set_oauth_defaults(self):
        """Ensure all OAuth2-related settings are correct"""
        self.client_type = ClientTypes.CONFIDENTIAL
        self.signing_key = None
        self.include_claims_in_id_token = True
        scopes = ScopeMapping.objects.filter(
            managed__in=[
                "goauthentik.io/providers/oauth2/scope-openid",
                "goauthentik.io/providers/oauth2/scope-profile",
                "goauthentik.io/providers/oauth2/scope-email",
                "goauthentik.io/providers/oauth2/scope-entitlements",
                "goauthentik.io/providers/proxy/scope-proxy",
            ]
        )
        self.property_mappings.add(*list(scopes))
        self.redirect_uris = _get_callback_url(self.external_host)

    def __str__(self):
        return f"Proxy Provider {self.name}"

    def get_required_objects(self) -> Iterable[models.Model | str]:
        required_models = [self]
        if self.certificate is not None:
            required_models.append(self.certificate)
        return required_models

    class Meta:
        verbose_name = _("Proxy Provider")
        verbose_name_plural = _("Proxy Providers")
        authentik_used_by_shadows = ["authentik_providers_oauth2.oauth2provider"]


class ProxySessionManager(models.Manager):
    """Manager for ProxySession"""

    def get_queryset(self):
        """Filter out soft-deleted sessions"""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def cleanup_expired(self) -> int:
        """Delete expired sessions and return count of deleted sessions"""
        from django.utils import timezone
        result = self.filter(expires__lt=timezone.now()).delete()
        return result[0] if result else 0


class ProxySession(ExpiringModel):
    """Session for Proxy Outpost"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    
    provider_id = models.CharField(max_length=255, null=False, blank=False)
    
    session_key = models.CharField(max_length=255, null=False, blank=False)
    
    data = models.BinaryField()
    
    claims = models.TextField(blank=True, default="")
    
    redirect = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    deleted_at = models.DateTimeField(null=True, blank=True, default=None) # used by gorm for soft delete

    objects = ProxySessionManager()

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Proxy Provider Session")
        verbose_name_plural = _("Proxy Provider Sessions")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["session_key", "provider_id"]),
            models.Index(fields=["provider_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["deleted_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session_key", "provider_id"],
                name="unique_session_key_provider_id"
            ),
        ]
        
    def __str__(self):
        return f"Proxy Session {self.session_key} (Provider: {self.provider_id})"
