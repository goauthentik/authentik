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
from authentik.lib.generators import generate_key
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
    """Apple Platform SSO enforcement policy for the login window, screen unlock and
    FileVault. Maps to the LoginPolicy/UnlockPolicy/FileVaultPolicy keys of the
    com.apple.extensiblesso payload. macOS only."""

    NONE = "none", _("None (silent background token only)")
    ATTEMPT = "attempt", _("Attempt authentication (enforced only when online)")
    REQUIRE = "require", _("Require authentication")


class ApplePSSOBiometricRequirement(models.TextChoices):
    """Which biometric, if any, is required to use the user Secure Enclave key. Maps to the
    mutually exclusive members of
    ASAuthorizationProviderExtensionLoginConfiguration.UserSecureEnclaveKeyBiometricPolicy.
    macOS only."""

    NONE = "none", _("None (no biometric required)")
    CURRENT_SET = "current_set", _("Touch ID or Apple Watch, invalidated if enrolment changes")
    ANY = "any", _("Touch ID or Apple Watch, any enrolment")


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

    # Apple Platform SSO (macOS) login-window behaviour. These map to the LoginPolicy,
    # UnlockPolicy and FileVaultPolicy keys of the generated com.apple.extensiblesso
    # payload and only affect macOS devices. When left at "none" the key is omitted and
    # Platform SSO runs in its passive, background-token-only mode.
    apple_psso_login_policy = models.TextField(
        choices=ApplePSSOAuthenticationPolicy.choices,
        default=ApplePSSOAuthenticationPolicy.NONE,
    )
    apple_psso_unlock_policy = models.TextField(
        choices=ApplePSSOAuthenticationPolicy.choices,
        default=ApplePSSOAuthenticationPolicy.NONE,
    )
    apple_psso_filevault_policy = models.TextField(
        choices=ApplePSSOAuthenticationPolicy.choices,
        default=ApplePSSOAuthenticationPolicy.NONE,
    )
    # Apple Platform SSO maximum interval (seconds) before a full re-authentication is
    # required. Maps to LoginFrequency; Apple's default is 64800 (18 hours), minimum 3600.
    apple_psso_login_frequency = models.PositiveIntegerField(default=64800)
    # Biometric requirement for the user Secure Enclave key. Together these map to
    # ASAuthorizationProviderExtensionLoginConfiguration.userSecureEnclaveKeyBiometricPolicy,
    # an OptionSet applied by the native agent's PSSO extension (macOS only,
    # UserSecureEnclaveKey). Apple's option set has one requirement plus two independent
    # modifiers, so it is modelled here as a choice plus two booleans rather than a flag.
    apple_psso_biometric_requirement = models.TextField(
        choices=ApplePSSOBiometricRequirement.choices,
        default=ApplePSSOBiometricRequirement.NONE,
    )
    # Maps to PasswordFallback. Defaults on: without it a user whose Touch ID is cancelled,
    # failing, or never enrolled has no way to use the key at all — and Apple's guidance is
    # explicit that if neither biometrics nor web-based authentication is available, the
    # user cannot log in. Macs without Touch ID hardware are the common case.
    apple_psso_biometric_password_fallback = models.BooleanField(default=True)
    # Maps to ReuseDuringUnlock: reuse the Touch ID presented at unlock rather than
    # prompting again.
    apple_psso_biometric_reuse_during_unlock = models.BooleanField(default=False)

    @property
    def apple_psso_biometric_policies(self) -> list[str]:
        """Flattens the biometric settings into the list the agent applies as Apple's
        UserSecureEnclaveKeyBiometricPolicy OptionSet.

        Modifiers are meaningless on their own — PasswordFallback with no requirement is a
        policy that demands nothing while reading like it demands something — so an unset
        requirement yields an empty list and the agent leaves the property untouched."""
        requirement = {
            ApplePSSOBiometricRequirement.CURRENT_SET: "touch_id_or_watch_current_set",
            ApplePSSOBiometricRequirement.ANY: "touch_id_or_watch_any",
        }.get(self.apple_psso_biometric_requirement)
        if requirement is None:
            return []
        policies = [requirement]
        if self.apple_psso_biometric_password_fallback:
            policies.append("password_fallback")
        if self.apple_psso_biometric_reuse_during_unlock:
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


class AppleIndependentSecureEnclave(Authenticator):
    """A device-independent secure enclave key, used by Tap-to-login"""

    uuid = models.UUIDField(primary_key=True, default=uuid4)

    apple_secure_enclave_key = models.TextField()
    apple_enclave_key_id = models.TextField()
    device_type = models.TextField()

    class Meta:
        verbose_name = _("Apple Independent Secure Enclave")
        verbose_name_plural = _("Apple Independent Secure Enclaves")
