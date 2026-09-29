from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING
from uuid import uuid4

from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import User, default_token_key
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.models import (
    Connector,
    Device,
    DeviceAccessGroup,
    DeviceConnection,
    DeviceUserBinding,
)
from authentik.flows.stage import StageView
from authentik.lib.generators import generate_id, generate_key
from authentik.lib.models import (
    ExpiringModel,
    InternallyManagedMixin,
    SerializerModel,
    SimpleThroughModel,
)
from authentik.lib.utils.time import timedelta_string_validator
from authentik.stages.authenticator.models import Device as Authenticator

if TYPE_CHECKING:
    from authentik.endpoints.connectors.agent.controller import AgentConnectorController


class ApplePSSOAuthenticationPolicy(models.TextChoices):
    """Platform SSO policy for the login window, screen unlock and FileVault"""

    NONE = "none", _("None (silent background token only)")
    ATTEMPT = "attempt", _("Attempt authentication (enforced only when online)")
    REQUIRE = "require", _("Require authentication")


class ApplePSSOAuthenticationMethod(models.TextChoices):
    """How the user authenticates at the macOS login window"""

    USER_SECURE_ENCLAVE_KEY = "user_secure_enclave_key", _("User Secure Enclave key")
    PASSWORD = "password", _("Password")
    WEB = "web", _("Web")


class ApplePSSOBiometricRequirement(models.TextChoices):
    """Biometric required to use the user Secure Enclave key"""

    NONE = "none", _("None (no biometric required)")
    CURRENT_SET = "current_set", _("Touch ID or Apple Watch, invalidated if enrolment changes")
    ANY = "any", _("Touch ID or Apple Watch, any enrolment")


@dataclass
class ApplePSSOConfig:
    """Apple Platform SSO settings, stored as JSON on the connector"""

    # Decides which settings apply: biometrics for the Secure Enclave key, policies for password
    authentication_method: str = ApplePSSOAuthenticationMethod.USER_SECURE_ENCLAVE_KEY

    # Omitted from the profile when left at "none"
    login_policy: str = ApplePSSOAuthenticationPolicy.NONE
    unlock_policy: str = ApplePSSOAuthenticationPolicy.NONE
    filevault_policy: str = ApplePSSOAuthenticationPolicy.NONE
    # Without this, an unlock policy of "require" disables Touch ID and watch unlock
    unlock_allow_touch_id_or_watch: bool = True
    # Seconds before a full re-authentication is required, Apple's minimum is 3600
    login_frequency: int = 64800

    # Seconds unregistered local accounts can still log in after a policy lands, 0 to disable
    authentication_grace_period: int = 0
    # Seconds the local password keeps working offline, 0 to disable
    offline_grace_period: int = 0
    # Local accounts the policies don't apply to, such as a break-glass admin
    non_platform_sso_accounts: list[str] = field(default_factory=list)
    # Create a local account for users signing in without one
    enable_create_user_at_login: bool = False

    # Applied by the agent's PSSO extension
    biometric_requirement: str = ApplePSSOBiometricRequirement.NONE
    # Without this, users on Macs without Touch ID can't log in
    biometric_password_fallback: bool = True
    # Reuse the Touch ID presented at unlock instead of prompting again
    biometric_reuse_during_unlock: bool = False


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
        "authentik_providers_oauth2.OAuth2Provider",
        blank=True,
        default=None,
        through="AgentConnectorJWTFederationProvider",
    )

    nss_uid_offset = models.PositiveIntegerField(default=1000)
    nss_gid_offset = models.PositiveIntegerField(default=1000)

    challenge_key = models.ForeignKey(CertificateKeyPair, on_delete=models.CASCADE, null=True)
    challenge_idle_timeout = models.TextField(
        validators=[timedelta_string_validator], default="seconds=5"
    )
    challenge_trigger_check_in = models.BooleanField(default=False)

    # See ApplePSSOConfig, read through apple_psso_config to get defaults
    apple_psso = models.JSONField(default=dict, blank=True)

    @property
    def apple_psso_config(self) -> ApplePSSOConfig:
        known = {f.name for f in fields(ApplePSSOConfig)}
        return ApplePSSOConfig(**{k: v for k, v in self.apple_psso.items() if k in known})

    @property
    def apple_psso_biometric_policies(self) -> list[str]:
        """Biometric policies for the agent to apply, empty when no biometric is required"""
        config = self.apple_psso_config
        if config.authentication_method != ApplePSSOAuthenticationMethod.USER_SECURE_ENCLAVE_KEY:
            return []
        requirement = {
            ApplePSSOBiometricRequirement.CURRENT_SET: "touch_id_or_watch_current_set",
            ApplePSSOBiometricRequirement.ANY: "touch_id_or_watch_any",
        }.get(config.biometric_requirement)
        if requirement is None:
            return []
        policies = [requirement]
        if config.biometric_password_fallback:
            policies.append("password_fallback")
        if config.biometric_reuse_during_unlock:
            policies.append("reuse_during_unlock")
        return policies

    @property
    def icon_url(self):
        return static("dist/assets/icons/icon.svg")

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
    def controller(self) -> type[AgentConnectorController]:
        from authentik.endpoints.connectors.agent.controller import AgentConnectorController

        return AgentConnectorController

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-agent-form"

    class Meta:
        verbose_name = _("Agent Connector")
        verbose_name_plural = _("Agent Connectors")


class AgentConnectorJWTFederationProvider(SimpleThroughModel):
    agent_connector = models.ForeignKey(
        AgentConnector, on_delete=models.CASCADE, db_column="agentconnector_id"
    )
    oauth2_provider = models.ForeignKey(
        "authentik_providers_oauth2.OAuth2Provider",
        on_delete=models.CASCADE,
        db_column="oauth2provider_id",
    )

    class Meta:
        db_table = "authentik_endpoints_connectors_agent_agentconnector_jwt_fed2bc6"
        unique_together = (("agent_connector", "oauth2_provider"),)
        verbose_name = _("Agent Connector JWT Federation Provider")
        verbose_name_plural = _("Agent Connector JWT Federation Providers")

    def __str__(self):
        return (
            f"AgentConnectorJWTFederationProvider for AgentConnector {self.agent_connector_id} "
            f"and OAuth2Provider {self.oauth2_provider_id}."
        )


class AgentDeviceConnection(DeviceConnection):

    apple_key_exchange_key = models.TextField()
    apple_encryption_key = models.TextField()
    apple_enc_key_id = models.TextField()
    apple_signing_key = models.TextField()
    apple_sign_key_id = models.TextField()


class AgentDeviceUserBinding(DeviceUserBinding):

    apple_secure_enclave_key = models.TextField()
    apple_enclave_key_id = models.TextField()

    class Meta:
        verbose_name = _("Agent Device User binding")
        verbose_name_plural = _("Agent Device User bindings")


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


class AppleAuthorizationCode(InternallyManagedMixin, ExpiringModel):
    """Short-lived code issued by the authorize endpoint, exchanged for tokens."""

    code = models.TextField(default=generate_id)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    connector = models.ForeignKey("AgentConnector", on_delete=models.CASCADE)
    # The device the code was issued to, it is the only one allowed to redeem it
    device_connection = models.ForeignKey(AgentDeviceConnection, on_delete=models.CASCADE)
    state = models.TextField(default="")
    scope = models.TextField()

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Apple Authorization Code")
        verbose_name_plural = _("Apple Authorization Codes")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["code"]),
        ]


class AppleUnlockKey(InternallyManagedMixin, ExpiringModel):
    """Server-provisioned EC256 key for Platform SSO v2.0 user_unlock."""

    identifier = models.UUIDField(primary_key=True, default=uuid4)
    device_user = models.ForeignKey(AgentDeviceUserBinding, on_delete=models.CASCADE)
    private_key = models.TextField()
    certificate_der = models.TextField(default="")

    class Meta(ExpiringModel.Meta):
        verbose_name = _("Apple Unlock Key")
        verbose_name_plural = _("Apple Unlock Keys")


class AppleIndependentSecureEnclave(Authenticator):
    """A device-independent secure enclave key, used by Tap-to-login"""

    uuid = models.UUIDField(primary_key=True, default=uuid4)

    apple_secure_enclave_key = models.TextField()
    apple_enclave_key_id = models.TextField()
    device_type = models.TextField()

    class Meta:
        verbose_name = _("Apple Independent Secure Enclave")
        verbose_name_plural = _("Apple Independent Secure Enclaves")
