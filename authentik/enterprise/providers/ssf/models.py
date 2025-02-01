from datetime import datetime
from functools import cached_property
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from jwt import encode

from authentik.core.models import BackchannelProvider, Token, User
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider


class EventTypes(models.TextChoices):
    """SSF Event types supported by authentik"""

    CAEP_SESSION_REVOKED = "https://schemas.openid.net/secevent/caep/event-type/session-revoked"
    CAEP_CREDENTIAL_CHANGE = "https://schemas.openid.net/secevent/caep/event-type/credential-change"
    SET_VERIFICATION = "https://schemas.openid.net/secevent/ssf/event-type/verification"


class DeliveryMethods(models.TextChoices):
    """SSF Delivery methods"""

    RISC_PUSH = "https://schemas.openid.net/secevent/risc/delivery-method/push"
    RISC_POLL = "https://schemas.openid.net/secevent/risc/delivery-method/poll"


class SSFEventStatus(models.TextChoices):
    """SSF Event status"""

    PENDING = "pending"
    SENT = "sent"


class SSFProvider(BackchannelProvider):
    """Shared Signals Framework provider to allow applications to
    receive user events from authentik."""

    signing_key = models.ForeignKey(
        CertificateKeyPair,
        verbose_name=_("Signing Key"),
        on_delete=models.SET_NULL,
        null=True,
        help_text=_(
            "Key used to sign the tokens. Only required when JWT Algorithm is set to RS256."
        ),
    )

    oidc_auth_providers = models.ManyToManyField(OAuth2Provider, blank=True, default=None)

    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, default=None)

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

    @property
    def service_account_identifier(self) -> str:
        return f"ak-providers-ssf-{self.pk}"

    @property
    def serializer(self):
        from authentik.enterprise.providers.ssf.api.providers import SSFProviderSerializer

        return SSFProviderSerializer

    @property
    def icon_url(self) -> str | None:
        return static("authentik/sources/ssf.svg")

    @property
    def component(self) -> str:
        return "ak-provider-ssf-form"

    class Meta:
        verbose_name = _("SSF Provider")
        verbose_name_plural = _("SSF Providers")
        permissions = [
            ("add_stream", _("Add stream to SSF provider")),
        ]


class Stream(models.Model):
    """SSF Stream"""

    uuid = models.UUIDField(default=uuid4, primary_key=True, editable=False)
    provider = models.ForeignKey(SSFProvider, on_delete=models.CASCADE)

    delivery_method = models.TextField(choices=DeliveryMethods.choices)
    endpoint_url = models.TextField(null=True)

    events_requested = ArrayField(models.TextField(choices=EventTypes.choices), default=list)
    format = models.TextField()
    aud = ArrayField(models.TextField(), default=list)

    user_subjects = models.ManyToManyField(User, "UserStreamSubject")

    iss = models.TextField()

    class Meta:
        verbose_name = _("SSF Stream")
        verbose_name_plural = _("SSF Streams")
        default_permissions = ["change", "delete", "view"]

    def __str__(self) -> str:
        return "SSF Stream"

    def prepare_event_payload(self, type: EventTypes, event_data: dict, **kwargs) -> dict:
        jti = uuid4()
        return {
            "uuid": jti,
            "stream": self,
            "type": type,
            "payload": {
                "jti": jti.hex,
                "aud": self.aud,
                "iat": int(datetime.now().timestamp()),
                "iss": self.iss,
                "events": {type: event_data},
                **kwargs,
            },
        }

    def encode(self, data: dict) -> str:
        headers = {}
        if self.provider.signing_key:
            headers["kid"] = self.provider.signing_key.kid
        key, alg = self.provider.jwt_key
        return encode(data, key, algorithm=alg, headers=headers)


class UserStreamSubject(models.Model):
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Stream subject {self.stream_id} to {self.user_id}"


class StreamEvent(models.Model):
    """Single stream event to be sent"""

    uuid = models.UUIDField(default=uuid4, primary_key=True, editable=False)

    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    status = models.TextField(choices=SSFEventStatus.choices)

    type = models.TextField(choices=EventTypes.choices)
    payload = models.JSONField(default=dict)

    def __str__(self):
        return f"Stream event {self.type}"
