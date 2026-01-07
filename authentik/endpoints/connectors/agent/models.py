from typing import TYPE_CHECKING
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import ExpiringModel, User, default_token_key
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.models import (
    Connector,
    Device,
    DeviceAccessGroup,
    DeviceConnection,
    DeviceUserBinding,
)
from authentik.flows.stage import StageView
from authentik.lib.generators import generate_key
from authentik.lib.models import InternallyManagedMixin, SerializerModel
from authentik.lib.utils.time import timedelta_string_validator

if TYPE_CHECKING:
    from authentik.endpoints.connectors.agent.controller import AgentConnectorController


class AgentConnector(Connector):
    """Configure authentication and add device compliance using the authentik Agent."""

    refresh_interval = models.TextField(
        default="minutes=30",
        validators=[timedelta_string_validator],
    )

    auth_session_duration = models.TextField(
        default="hours=8", validators=[timedelta_string_validator]
    )
    auth_terminate_session_on_expiry = models.BooleanField(default=False)
    authorization_flow = models.ForeignKey(
        "authentik_flows.Flow", null=True, on_delete=models.SET_DEFAULT, default=None
    )
    jwt_federation_providers = models.ManyToManyField(
        "authentik_providers_oauth2.OAuth2Provider", blank=True, default=None
    )

    nss_uid_offset = models.PositiveIntegerField(default=1000)
    nss_gid_offset = models.PositiveIntegerField(default=1000)

    challenge_key = models.ForeignKey(CertificateKeyPair, on_delete=models.CASCADE, null=True)
    challenge_idle_timeout = models.TextField(
        validators=[timedelta_string_validator], default="seconds=5"
    )
    challenge_trigger_check_in = models.BooleanField(default=False)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.connectors.agent.api.connectors import (
            AgentConnectorSerializer,
        )

        return AgentConnectorSerializer

    @property
    def stage(self) -> type[StageView] | None:
        from authentik.endpoints.connectors.agent.stage import (
            AuthenticatorEndpointStageView,
        )

        return AuthenticatorEndpointStageView

    @property
    def controller(self) -> type["AgentConnectorController"]:
        from authentik.endpoints.connectors.agent.controller import AgentConnectorController

        return AgentConnectorController

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-agent-form"

    class Meta:
        verbose_name = _("Agent Connector")
        verbose_name_plural = _("Agent Connectors")


class AgentDeviceConnection(DeviceConnection):

    apple_key_exchange_key = models.TextField()
    apple_encryption_key = models.TextField()
    apple_enc_key_id = models.TextField()
    apple_signing_key = models.TextField()
    apple_sign_key_id = models.TextField()


class AgentDeviceUserBinding(DeviceUserBinding):

    apple_secure_enclave_key = models.TextField()
    apple_enclave_key_id = models.TextField()


class DeviceToken(InternallyManagedMixin, ExpiringModel):
    """Per-device token used for authentication."""

    token_uuid = models.UUIDField(primary_key=True, default=uuid4)
    device = models.ForeignKey(AgentDeviceConnection, on_delete=models.CASCADE)
    key = models.TextField(default=generate_key)

    class Meta:
        verbose_name = _("Device Token")
        verbose_name_plural = _("Device Tokens")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["key"]),
        ]


class EnrollmentToken(ExpiringModel, SerializerModel):
    """Token used during enrollment, a device will receive
    a device token for further authentication"""

    token_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField()
    key = models.TextField(default=default_token_key)
    connector = models.ForeignKey(AgentConnector, on_delete=models.CASCADE)
    device_group = models.ForeignKey(
        DeviceAccessGroup, on_delete=models.SET_DEFAULT, default=None, null=True
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.connectors.agent.api.enrollment_tokens import (
            EnrollmentTokenSerializer,
        )

        return EnrollmentTokenSerializer

    class Meta:
        verbose_name = _("Enrollment Token")
        verbose_name_plural = _("Enrollment Tokens")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["key"]),
        ]
        permissions = [
            ("view_enrollment_token_key", _("View token's key")),
        ]


class DeviceAuthenticationToken(InternallyManagedMixin, ExpiringModel):

    identifier = models.UUIDField(default=uuid4, primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    device_token = models.ForeignKey(DeviceToken, on_delete=models.CASCADE)
    connector = models.ForeignKey(AgentConnector, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None)
    token = models.TextField()

    def __str__(self):
        return f"Device authentication token {self.identifier}"

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Device authentication token")
        verbose_name_plural = _("Device authentication tokens")


class AppleNonce(InternallyManagedMixin, ExpiringModel):
    nonce = models.TextField()
    device_token = models.ForeignKey(DeviceToken, on_delete=models.CASCADE)

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Apple Nonce")
        verbose_name_plural = _("Apple Nonces")
