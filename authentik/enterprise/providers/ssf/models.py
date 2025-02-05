from datetime import datetime
from functools import cached_property
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.templatetags.static import static
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from jwt import encode

from authentik.core.models import BackchannelProvider, ExpiringModel, Token
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.models import CreatedUpdatedModel
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator
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

    PENDING_NEW = "pending_new"
    PENDING_FAILED = "pending_failed"
    SENT = "sent"


class SSFProvider(BackchannelProvider):
    """Shared Signals Framework provider to allow applications to
    receive user events from authentik."""

    signing_key = models.ForeignKey(
        CertificateKeyPair,
        verbose_name=_("Signing Key"),
        on_delete=models.CASCADE,
        help_text=_("Key used to sign the SSF Events."),
    )

    oidc_auth_providers = models.ManyToManyField(OAuth2Provider, blank=True, default=None)

    token = models.ForeignKey(Token, on_delete=models.CASCADE, null=True, default=None)

    event_retention = models.TextField(
        default="days=30",
        validators=[timedelta_string_validator],
    )

    @cached_property
    def jwt_key(self) -> tuple[PrivateKeyTypes, str]:
        """Get either the configured certificate or the client secret"""
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
        verbose_name = _("Shared Signals Framework Provider")
        verbose_name_plural = _("Shared Signals Framework Providers")
        permissions = [
            # This overrides the default "add_stream" permission of the Stream object,
            # as the user requesting to add a stream must have the permission on the provider
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

    iss = models.TextField()

    class Meta:
        verbose_name = _("SSF Stream")
        verbose_name_plural = _("SSF Streams")
        default_permissions = ["change", "delete", "view"]

    def __str__(self) -> str:
        return "SSF Stream"

    def prepare_event_payload(self, type: EventTypes, event_data: dict, **kwargs) -> dict:
        jti = uuid4()
        _now = now()
        return {
            "uuid": jti,
            "stream_id": str(self.pk),
            "type": type,
            "expiring": True,
            "status": SSFEventStatus.PENDING_NEW,
            "expires": _now + timedelta_from_string(self.provider.event_retention),
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


class StreamEvent(CreatedUpdatedModel, ExpiringModel):
    """Single stream event to be sent"""

    uuid = models.UUIDField(default=uuid4, primary_key=True, editable=False)

    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    status = models.TextField(choices=SSFEventStatus.choices)

    type = models.TextField(choices=EventTypes.choices)
    payload = models.JSONField(default=dict)

    def expire_action(self, *args, **kwargs):
        """Only allow automatic cleanup of successfully sent event"""
        if self.status != SSFEventStatus.SENT:
            return
        return super().expire_action(*args, **kwargs)

    def __str__(self):
        return f"Stream event {self.type}"

    class Meta:
        verbose_name = _("SSF Stream Event")
        verbose_name_plural = _("SSF Stream Events")
        ordering = ("-created",)
