"""OAuth Provider Models"""
import base64
import binascii
import json
import time
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, List, Optional, Type
from urllib.parse import urlparse
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.forms import ModelForm
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils import dateformat, timezone
from django.utils.translation import gettext_lazy as _
from jwkest.jwk import Key, RSAKey, SYMKey, import_rsa_key
from jwkest.jws import JWS

from authentik.core.models import ExpiringModel, PropertyMapping, Provider, User
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.utils.template import render_to_string
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
from authentik.providers.oauth2.apps import AuthentikProviderOAuth2Config
from authentik.providers.oauth2.generators import (
    generate_client_id,
    generate_client_secret,
)


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


class SubModes(models.TextChoices):
    """Mode after which 'sub' attribute is generateed, for compatibility reasons"""

    HASHED_USER_ID = "hashed_user_id", _("Based on the Hashed User ID")
    USER_USERNAME = "user_username", _("Based on the username")
    USER_EMAIL = (
        "user_email",
        _("Based on the User's Email. This is recommended over the UPN method."),
    )
    USER_UPN = (
        "user_upn",
        _(
            (
                "Based on the User's UPN, only works if user has a 'upn' attribute set. "
                "Use this method only if you have different UPN and Mail domains."
            )
        ),
    )


class ResponseTypes(models.TextChoices):
    """Response Type required by the client."""

    CODE = "code", _("code (Authorization Code Flow)")
    CODE_ADFS = (
        "code#adfs",
        _("code (ADFS Compatibility Mode, sends id_token as access_token)"),
    )
    ID_TOKEN = "id_token", _("id_token (Implicit Flow)")
    ID_TOKEN_TOKEN = "id_token token", _("id_token token (Implicit Flow)")
    CODE_TOKEN = "code token", _("code token (Hybrid Flow)")
    CODE_ID_TOKEN = "code id_token", _("code id_token (Hybrid Flow)")
    CODE_ID_TOKEN_TOKEN = "code id_token token", _("code id_token token (Hybrid Flow)")


class JWTAlgorithms(models.TextChoices):
    """Algorithm used to sign the JWT Token"""

    HS256 = "HS256", _("HS256 (Symmetric Encryption)")
    RS256 = "RS256", _("RS256 (Asymmetric Encryption)")


class ScopeMapping(PropertyMapping):
    """Map an OAuth Scope to users properties"""

    scope_name = models.TextField(help_text=_("Scope used by the client"))
    description = models.TextField(
        blank=True,
        help_text=_(
            (
                "Description shown to the user when consenting. "
                "If left empty, the user won't be informed."
            )
        ),
    )

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.providers.oauth2.forms import ScopeMappingForm

        return ScopeMappingForm

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
        help_text=_(ClientTypes.__doc__),
    )
    client_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Client ID"),
        default=generate_client_id,
    )
    client_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Client Secret"),
        default=generate_client_secret,
    )
    response_type = models.TextField(
        choices=ResponseTypes.choices,
        default=ResponseTypes.CODE,
        help_text=_(ResponseTypes.__doc__),
    )
    jwt_alg = models.CharField(
        max_length=10,
        choices=JWTAlgorithms.choices,
        default=JWTAlgorithms.RS256,
        verbose_name=_("JWT Algorithm"),
        help_text=_(JWTAlgorithms.__doc__),
    )
    redirect_uris = models.TextField(
        default="",
        verbose_name=_("Redirect URIs"),
        help_text=_("Enter each URI on a new line."),
    )

    include_claims_in_id_token = models.BooleanField(
        default=True,
        verbose_name=_("Include claims in id_token"),
        help_text=_(
            (
                "Include User claims from scopes in the id_token, for applications "
                "that don't access the userinfo endpoint."
            )
        ),
    )

    token_validity = models.TextField(
        default="minutes=10",
        validators=[timedelta_string_validator],
        help_text=_(
            (
                "Tokens not valid on or after current time + this value "
                "(Format: hours=1;minutes=2;seconds=3)."
            )
        ),
    )

    sub_mode = models.TextField(
        choices=SubModes.choices,
        default=SubModes.HASHED_USER_ID,
        help_text=_(
            (
                "Configure what data should be used as unique User Identifier. For most cases, "
                "the default should be fine."
            )
        ),
    )

    rsa_key = models.ForeignKey(
        CertificateKeyPair,
        verbose_name=_("RSA Key"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_(
            "Key used to sign the tokens. Only required when JWT Algorithm is set to RS256."
        ),
    )

    def create_refresh_token(
        self, user: User, scope: List[str], id_token: Optional["IDToken"] = None
    ) -> "RefreshToken":
        """Create and populate a RefreshToken object."""
        token = RefreshToken(
            user=user,
            provider=self,
            access_token=uuid4().hex,
            refresh_token=uuid4().hex,
            expires=timezone.now() + timedelta_from_string(self.token_validity),
            scope=scope,
        )
        if id_token:
            token.id_token = id_token
        return token

    def get_jwt_keys(self) -> List[Key]:
        """
        Takes a provider and returns the set of keys associated with it.
        Returns a list of keys.
        """
        if self.jwt_alg == JWTAlgorithms.RS256:
            # if the user selected RS256 but didn't select a
            # CertificateKeyPair, we fall back to HS256
            if not self.rsa_key:
                self.jwt_alg = JWTAlgorithms.HS256
                self.save()
            else:
                # Because the JWT Library uses python cryptodome,
                # we can't directly pass the RSAPublicKey
                # object, but have to load it ourselves
                key = import_rsa_key(self.rsa_key.key_data)
                keys = [RSAKey(key=key, kid=self.rsa_key.kid)]
                if not keys:
                    raise Exception("You must add at least one RSA Key.")
                return keys

        if self.jwt_alg == JWTAlgorithms.HS256:
            return [SYMKey(key=self.client_secret, alg=self.jwt_alg)]

        raise Exception("Unsupported key algorithm.")

    def get_issuer(self, request: HttpRequest) -> Optional[str]:
        """Get issuer, based on request"""
        try:
            mountpoint = AuthentikProviderOAuth2Config.mountpoints[
                "authentik.providers.oauth2.urls"
            ]
            # pylint: disable=no-member
            return request.build_absolute_uri(f"/{mountpoint}{self.application.slug}/")
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    @property
    def launch_url(self) -> Optional[str]:
        """Guess launch_url based on first redirect_uri"""
        if self.redirect_uris == "":
            return None
        main_url = self.redirect_uris.split("\n")[0]
        launch_url = urlparse(main_url)
        return main_url.replace(launch_url.path, "")

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.providers.oauth2.forms import OAuth2ProviderForm

        return OAuth2ProviderForm

    def __str__(self):
        return f"OAuth2 Provider {self.name}"

    def encode(self, payload: Dict[str, Any]) -> str:
        """Represent the ID Token as a JSON Web Token (JWT)."""
        keys = self.get_jwt_keys()
        # If the provider does not have an RSA Key assigned, it was switched to Symmetric
        self.refresh_from_db()
        jws = JWS(payload, alg=self.jwt_alg)
        return jws.sign_compact(keys)

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        try:
            # pylint: disable=no-member
            return render_to_string(
                "providers/oauth2/setup_url_modal.html",
                {
                    "provider": self,
                    "issuer": self.get_issuer(request),
                    "authorize": request.build_absolute_uri(
                        reverse(
                            "authentik_providers_oauth2:authorize",
                        )
                    ),
                    "token": request.build_absolute_uri(
                        reverse(
                            "authentik_providers_oauth2:token",
                        )
                    ),
                    "userinfo": request.build_absolute_uri(
                        reverse(
                            "authentik_providers_oauth2:userinfo",
                        )
                    ),
                    "provider_info": request.build_absolute_uri(
                        reverse(
                            "authentik_providers_oauth2:provider-info",
                            kwargs={"application_slug": self.application.slug},
                        )
                    ),
                },
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    class Meta:

        verbose_name = _("OAuth2/OpenID Provider")
        verbose_name_plural = _("OAuth2/OpenID Providers")


class BaseGrantModel(models.Model):
    """Base Model for all grants"""

    provider = models.ForeignKey(OAuth2Provider, on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    _scope = models.TextField(default="", verbose_name=_("Scopes"))

    @property
    def scope(self) -> List[str]:
        """Return scopes as list of strings"""
        return self._scope.split()

    @scope.setter
    def scope(self, value):
        self._scope = " ".join(value)

    class Meta:
        abstract = True


class AuthorizationCode(ExpiringModel, BaseGrantModel):
    """OAuth2 Authorization Code"""

    code = models.CharField(max_length=255, unique=True, verbose_name=_("Code"))
    nonce = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Nonce")
    )
    is_open_id = models.BooleanField(
        default=False, verbose_name=_("Is Authentication?")
    )
    code_challenge = models.CharField(
        max_length=255, null=True, verbose_name=_("Code Challenge")
    )
    code_challenge_method = models.CharField(
        max_length=255, null=True, verbose_name=_("Code Challenge Method")
    )

    class Meta:
        verbose_name = _("Authorization Code")
        verbose_name_plural = _("Authorization Codes")

    def __str__(self):
        return "{0} - {1}".format(self.provider, self.code)


@dataclass
class IDToken:
    """The primary extension that OpenID Connect makes to OAuth 2.0 to enable End-Users to be
    Authenticated is the ID Token data structure. The ID Token is a security token that contains
    Claims about the Authentication of an End-User by an Authorization Server when using a Client,
    and potentially other requested Claims. The ID Token is represented as a
    JSON Web Token (JWT) [JWT].

    https://openid.net/specs/openid-connect-core-1_0.html#IDToken"""

    # All these fields need to optional so we can save an empty IDToken for non-OpenID flows.
    iss: Optional[str] = None
    sub: Optional[str] = None
    aud: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    auth_time: Optional[int] = None

    nonce: Optional[str] = None
    at_hash: Optional[str] = None

    claims: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "IDToken":
        """Reconstruct ID Token from json dictionary"""
        token = IDToken()
        for key, value in data.items():
            setattr(token, key, value)
        return token

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dict, and update with keys from `claims`"""
        dic = asdict(self)
        dic.pop("claims")
        dic.update(self.claims)
        return dic


class RefreshToken(ExpiringModel, BaseGrantModel):
    """OAuth2 Refresh Token"""

    access_token = models.CharField(
        max_length=255, unique=True, verbose_name=_("Access Token")
    )
    refresh_token = models.CharField(
        max_length=255, unique=True, verbose_name=_("Refresh Token")
    )
    _id_token = models.TextField(verbose_name=_("ID Token"))

    class Meta:
        verbose_name = _("OAuth2 Token")
        verbose_name_plural = _("OAuth2 Tokens")

    @property
    def id_token(self) -> IDToken:
        """Load ID Token from json"""
        if self._id_token:
            raw_token = json.loads(self._id_token)
            return IDToken.from_dict(raw_token)
        return IDToken()

    @id_token.setter
    def id_token(self, value: IDToken):
        self._id_token = json.dumps(asdict(value))

    def __str__(self):
        return f"{self.provider} - {self.access_token}"

    @property
    def at_hash(self):
        """Get hashed access_token"""
        hashed_access_token = (
            sha256(self.access_token.encode("ascii")).hexdigest().encode("ascii")
        )
        return (
            base64.urlsafe_b64encode(
                binascii.unhexlify(hashed_access_token[: len(hashed_access_token) // 2])
            )
            .rstrip(b"=")
            .decode("ascii")
        )

    def create_id_token(self, user: User, request: HttpRequest) -> IDToken:
        """Creates the id_token.
        See: http://openid.net/specs/openid-connect-core-1_0.html#IDToken"""
        sub = ""
        if self.provider.sub_mode == SubModes.HASHED_USER_ID:
            sub = sha256(f"{user.id}-{settings.SECRET_KEY}".encode("ascii")).hexdigest()
        elif self.provider.sub_mode == SubModes.USER_EMAIL:
            sub = user.email
        elif self.provider.sub_mode == SubModes.USER_USERNAME:
            sub = user.username
        elif self.provider.sub_mode == SubModes.USER_UPN:
            sub = user.attributes["upn"]
        else:
            raise ValueError(
                (
                    f"Provider {self.provider} has invalid sub_mode "
                    f"selected: {self.provider.sub_mode}"
                )
            )

        # Convert datetimes into timestamps.
        now = int(time.time())
        iat_time = now
        exp_time = int(
            now + timedelta_from_string(self.provider.token_validity).seconds
        )
        user_auth_time = user.last_login or user.date_joined
        auth_time = int(dateformat.format(user_auth_time, "U"))

        token = IDToken(
            iss=self.provider.get_issuer(request),
            sub=sub,
            aud=self.provider.client_id,
            exp=exp_time,
            iat=iat_time,
            auth_time=auth_time,
        )

        # Include (or not) user standard claims in the id_token.
        if self.provider.include_claims_in_id_token:
            from authentik.providers.oauth2.views.userinfo import UserInfoView

            user_info = UserInfoView()
            user_info.request = request
            claims = user_info.get_claims(self)
            token.claims = claims

        return token
