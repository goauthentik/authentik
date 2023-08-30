"""OAuth Provider Models"""
import base64
import binascii
import json
from dataclasses import asdict
from functools import cached_property
from hashlib import sha256
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from dacite.core import from_dict
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from jwt import encode
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.models import ExpiringModel, PropertyMapping, Provider, User
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_code_fixed_length, generate_id, generate_key
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator
from authentik.providers.oauth2.id_token import IDToken, SubModes
from authentik.sources.oauth.models import OAuthSource

LOGGER = get_logger()


def generate_client_secret() -> str:
    """Generate client secret with adequate length"""
    return generate_id(128)


class ClientTypes(models.TextChoices):
    """Confidential clients are capable of maintaining the confidentiality
    of their credentials. Public clients are incapable."""

    CONFIDENTIAL = "confidential", _("Confidential")
    PUBLIC = "public", _("Public")


class GrantTypes(models.TextChoices):
    """OAuth2 Grant types we support"""

    AUTHORIZATION_CODE = "authorization_code"
    IMPLICIT = "implicit"
    HYBRID = "hybrid"


class ResponseMode(models.TextChoices):
    """https://openid.net/specs/oauth-v2-multiple-response-types-1_0.html#OAuth.Post"""

    QUERY = "query"
    FRAGMENT = "fragment"
    FORM_POST = "form_post"


class IssuerMode(models.TextChoices):
    """Configure how the `iss` field is created."""

    GLOBAL = "global", _("Same identifier is used for all providers")
    PER_PROVIDER = "per_provider", _(
        "Each provider has a different issuer, based on the application slug."
    )


class ResponseTypes(models.TextChoices):
    """Response Type required by the client."""

    CODE = "code", _("code (Authorization Code Flow)")
    ID_TOKEN = "id_token", _("id_token (Implicit Flow)")
    ID_TOKEN_TOKEN = "id_token token", _("id_token token (Implicit Flow)")
    CODE_TOKEN = "code token", _("code token (Hybrid Flow)")
    CODE_ID_TOKEN = "code id_token", _("code id_token (Hybrid Flow)")
    CODE_ID_TOKEN_TOKEN = "code id_token token", _("code id_token token (Hybrid Flow)")


class JWTAlgorithms(models.TextChoices):
    """Algorithm used to sign the JWT Token"""

    HS256 = "HS256", _("HS256 (Symmetric Encryption)")
    RS256 = "RS256", _("RS256 (Asymmetric Encryption)")
    ES256 = "ES256", _("ES256 (Asymmetric Encryption)")


class ScopeMapping(PropertyMapping):
    """Map an OAuth Scope to users properties"""

    scope_name = models.TextField(help_text=_("Scope used by the client"))
    description = models.TextField(
        blank=True,
        help_text=_(
            "Description shown to the user when consenting. "
            "If left empty, the user won't be informed."
        ),
    )

    @property
    def component(self) -> str:
        return "ak-property-mapping-scope-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.oauth2.api.scopes import ScopeMappingSerializer

        return ScopeMappingSerializer

    def __str__(self):
        return f"Scope Mapping {self.name} ({self.scope_name})"

    class Meta:
        verbose_name = _("Scope Mapping")
        verbose_name_plural = _("Scope Mappings")


class OAuth2Provider(Provider):
    """OAuth2 Provider for generic OAuth and OpenID Connect Applications."""

    client_type = models.CharField(
        max_length=30,
        choices=ClientTypes.choices,
        default=ClientTypes.CONFIDENTIAL,
        verbose_name=_("Client Type"),
        help_text=_(
            "Confidential clients are capable of maintaining the confidentiality "
            "of their credentials. Public clients are incapable"
        ),
    )
    client_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Client ID"),
        default=generate_id,
    )
    client_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Client Secret"),
        default=generate_client_secret,
    )
    redirect_uris = models.TextField(
        default="",
        blank=True,
        verbose_name=_("Redirect URIs"),
        help_text=_("Enter each URI on a new line."),
    )

    include_claims_in_id_token = models.BooleanField(
        default=True,
        verbose_name=_("Include claims in id_token"),
        help_text=_(
            "Include User claims from scopes in the id_token, for applications "
            "that don't access the userinfo endpoint."
        ),
    )

    access_code_validity = models.TextField(
        default="minutes=1",
        validators=[timedelta_string_validator],
        help_text=_(
            "Access codes not valid on or after current time + this value "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
    )
    access_token_validity = models.TextField(
        default="hours=1",
        validators=[timedelta_string_validator],
        help_text=_(
            "Tokens not valid on or after current time + this value "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
    )
    refresh_token_validity = models.TextField(
        default="days=30",
        validators=[timedelta_string_validator],
        help_text=_(
            "Tokens not valid on or after current time + this value "
            "(Format: hours=1;minutes=2;seconds=3)."
        ),
    )

    sub_mode = models.TextField(
        choices=SubModes.choices,
        default=SubModes.HASHED_USER_ID,
        help_text=_(
            "Configure what data should be used as unique User Identifier. For most cases, "
            "the default should be fine."
        ),
    )
    issuer_mode = models.TextField(
        choices=IssuerMode.choices,
        default=IssuerMode.PER_PROVIDER,
        help_text=_("Configure how the issuer field of the ID Token should be filled."),
    )

    signing_key = models.ForeignKey(
        CertificateKeyPair,
        verbose_name=_("Signing Key"),
        on_delete=models.SET_NULL,
        null=True,
        help_text=_(
            "Key used to sign the tokens. Only required when JWT Algorithm is set to RS256."
        ),
    )

    jwks_sources = models.ManyToManyField(
        OAuthSource,
        verbose_name=_(
            "Any JWT signed by the JWK of the selected source can be used to authenticate."
        ),
        related_name="oauth2_providers",
        default=None,
        blank=True,
    )

    @cached_property
    def jwt_key(self) -> tuple[str | PrivateKeyTypes, str]:
        """Get either the configured certificate or the client secret"""
        if not self.signing_key:
            # No Certificate at all, assume HS256
            return self.client_secret, JWTAlgorithms.HS256
        key: CertificateKeyPair = self.signing_key
        private_key = key.private_key
        if isinstance(private_key, RSAPrivateKey):
            return private_key, JWTAlgorithms.RS256
        if isinstance(private_key, EllipticCurvePrivateKey):
            return private_key, JWTAlgorithms.ES256
        raise ValueError(f"Invalid private key type: {type(private_key)}")

    def get_issuer(self, request: HttpRequest) -> Optional[str]:
        """Get issuer, based on request"""
        if self.issuer_mode == IssuerMode.GLOBAL:
            return request.build_absolute_uri(reverse("authentik_core:root-redirect"))
        try:
            url = reverse(
                "authentik_providers_oauth2:provider-root",
                kwargs={
                    # pylint: disable=no-member
                    "application_slug": self.application.slug,
                },
            )
            return request.build_absolute_uri(url)
        # pylint: disable=no-member
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    @property
    def launch_url(self) -> Optional[str]:
        """Guess launch_url based on first redirect_uri"""
        if self.redirect_uris == "":
            return None
        main_url = self.redirect_uris.split("\n", maxsplit=1)[0]
        try:
            launch_url = urlparse(main_url)._replace(path="")
            return urlunparse(launch_url)
        except ValueError as exc:
            LOGGER.warning("Failed to format launch url", exc=exc)
            return None

    @property
    def component(self) -> str:
        return "ak-provider-oauth2-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.oauth2.api.providers import OAuth2ProviderSerializer

        return OAuth2ProviderSerializer

    def __str__(self):
        return f"OAuth2 Provider {self.name}"

    def encode(self, payload: dict[str, Any]) -> str:
        """Represent the ID Token as a JSON Web Token (JWT)."""
        headers = {}
        if self.signing_key:
            headers["kid"] = self.signing_key.kid
        key, alg = self.jwt_key
        return encode(payload, key, algorithm=alg, headers=headers)

    class Meta:
        verbose_name = _("OAuth2/OpenID Provider")
        verbose_name_plural = _("OAuth2/OpenID Providers")


class BaseGrantModel(models.Model):
    """Base Model for all grants"""

    provider = models.ForeignKey(OAuth2Provider, on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    revoked = models.BooleanField(default=False)
    _scope = models.TextField(default="", verbose_name=_("Scopes"))
    auth_time = models.DateTimeField(verbose_name="Authentication time")

    @property
    def scope(self) -> list[str]:
        """Return scopes as list of strings"""
        return self._scope.split()

    @scope.setter
    def scope(self, value):
        self._scope = " ".join(value)

    class Meta:
        abstract = True


class AuthorizationCode(SerializerModel, ExpiringModel, BaseGrantModel):
    """OAuth2 Authorization Code"""

    code = models.CharField(max_length=255, unique=True, verbose_name=_("Code"))
    nonce = models.TextField(null=True, default=None, verbose_name=_("Nonce"))
    code_challenge = models.CharField(max_length=255, null=True, verbose_name=_("Code Challenge"))
    code_challenge_method = models.CharField(
        max_length=255, null=True, verbose_name=_("Code Challenge Method")
    )

    @property
    def serializer(self) -> Serializer:
        from authentik.providers.oauth2.api.tokens import ExpiringBaseGrantModelSerializer

        return ExpiringBaseGrantModelSerializer

    @property
    def c_hash(self):
        """https://openid.net/specs/openid-connect-core-1_0.html#IDToken"""
        hashed_code = sha256(self.code.encode("ascii")).hexdigest().encode("ascii")
        return (
            base64.urlsafe_b64encode(binascii.unhexlify(hashed_code[: len(hashed_code) // 2]))
            .rstrip(b"=")
            .decode("ascii")
        )

    class Meta:
        verbose_name = _("Authorization Code")
        verbose_name_plural = _("Authorization Codes")

    def __str__(self):
        return f"Authorization code for {self.provider} for user {self.user}"


class AccessToken(SerializerModel, ExpiringModel, BaseGrantModel):
    """OAuth2 access token, non-opaque using a JWT as identifier"""

    token = models.TextField()
    _id_token = models.TextField()

    @property
    def id_token(self) -> IDToken:
        """Load ID Token from json"""
        raw_token = json.loads(self._id_token)
        return from_dict(IDToken, raw_token)

    @id_token.setter
    def id_token(self, value: IDToken):
        self.token = value.to_access_token(self.provider)
        self._id_token = json.dumps(asdict(value))

    @property
    def at_hash(self):
        """Get hashed access_token"""
        hashed_access_token = sha256(self.token.encode("ascii")).hexdigest().encode("ascii")
        return (
            base64.urlsafe_b64encode(
                binascii.unhexlify(hashed_access_token[: len(hashed_access_token) // 2])
            )
            .rstrip(b"=")
            .decode("ascii")
        )

    @property
    def serializer(self) -> Serializer:
        from authentik.providers.oauth2.api.tokens import TokenModelSerializer

        return TokenModelSerializer

    class Meta:
        verbose_name = _("OAuth2 Access Token")
        verbose_name_plural = _("OAuth2 Access Tokens")

    def __str__(self):
        return f"Access Token for {self.provider} for user {self.user}"


class RefreshToken(SerializerModel, ExpiringModel, BaseGrantModel):
    """OAuth2 Refresh Token, opaque"""

    token = models.TextField(default=generate_client_secret)
    _id_token = models.TextField(verbose_name=_("ID Token"))

    @property
    def id_token(self) -> IDToken:
        """Load ID Token from json"""
        raw_token = json.loads(self._id_token)
        return from_dict(IDToken, raw_token)

    @id_token.setter
    def id_token(self, value: IDToken):
        self._id_token = json.dumps(asdict(value))

    @property
    def serializer(self) -> Serializer:
        from authentik.providers.oauth2.api.tokens import TokenModelSerializer

        return TokenModelSerializer

    class Meta:
        verbose_name = _("OAuth2 Refresh Token")
        verbose_name_plural = _("OAuth2 Refresh Tokens")

    def __str__(self):
        return f"Refresh Token for {self.provider} for user {self.user}"


class DeviceToken(ExpiringModel):
    """Temporary device token for OAuth device flow"""

    user = models.ForeignKey(
        "authentik_core.User", default=None, on_delete=models.CASCADE, null=True
    )
    provider = models.ForeignKey(OAuth2Provider, on_delete=models.CASCADE)
    device_code = models.TextField(default=generate_key)
    user_code = models.TextField(default=generate_code_fixed_length)
    _scope = models.TextField(default="", verbose_name=_("Scopes"))

    @property
    def scope(self) -> list[str]:
        """Return scopes as list of strings"""
        return self._scope.split()

    @scope.setter
    def scope(self, value):
        self._scope = " ".join(value)

    class Meta:
        verbose_name = _("Device Token")
        verbose_name_plural = _("Device Tokens")

    def __str__(self):
        return f"Device Token for {self.provider}"
