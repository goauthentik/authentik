"""WebAuthn stage"""

from typing import TYPE_CHECKING, cast

from cryptography.x509 import Certificate, load_pem_x509_certificate
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.http import HttpRequest
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer, Serializer, ValidationError
from structlog.stdlib import get_logger
from webauthn.authentication.generate_authentication_options import generate_authentication_options
from webauthn.authentication.verify_authentication_response import verify_authentication_response
from webauthn.helpers import parse_authentication_credential_json
from webauthn.helpers.base64url_to_bytes import base64url_to_bytes
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidJSONStructure
from webauthn.helpers.options_to_json_dict import options_to_json_dict
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    UserVerificationRequirement,
)

from authentik.core.models import User
from authentik.core.signals import login_failed
from authentik.core.types import UserSettingSerializer
from authentik.events.middleware import audit_ignore
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.models import InternallyManagedMixin, SerializerModel, SimpleThroughModel
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD_ARGS

UNKNOWN_DEVICE_TYPE_AAGUID = "00000000-0000-0000-0000-000000000000"
PLAN_CONTEXT_WEBAUTHN_CHALLENGE = "goauthentik.io/stages/authenticator_webauthn/challenge"
LOGGER = get_logger()

if TYPE_CHECKING:
    from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage


class UserVerification(models.TextChoices):
    """The degree to which the Relying Party wishes to verify a user's identity.

    Members:
        `REQUIRED`: User verification must occur
        `PREFERRED`: User verification would be great, but if not that's okay too
        `DISCOURAGED`: User verification should not occur, but it's okay if it does

    https://www.w3.org/TR/webauthn-2/#enumdef-userverificationrequirement
    """

    REQUIRED = "required"
    PREFERRED = "preferred"
    DISCOURAGED = "discouraged"


class ResidentKeyRequirement(models.TextChoices):
    """The Relying Party's preference for the authenticator to create a dedicated "client-side"
    credential for it. Requiring an authenticator to store a dedicated credential should not be
    done lightly due to the limited storage capacity of some types of authenticators.

    Members:
        `DISCOURAGED`: The authenticator should not create a dedicated credential
        `PREFERRED`: The authenticator can create and store a dedicated credential, but if it
            doesn't that's alright too
        `REQUIRED`: The authenticator MUST create a dedicated credential. If it cannot, the RP
            is prepared for an error to occur.

    https://www.w3.org/TR/webauthn-2/#enum-residentKeyRequirement
    """

    DISCOURAGED = "discouraged"
    PREFERRED = "preferred"
    REQUIRED = "required"


class AuthenticatorAttachment(models.TextChoices):
    """How an authenticator is connected to the client/browser.

    Members:
        `PLATFORM`: A non-removable authenticator, like TouchID or Windows Hello
        `CROSS_PLATFORM`: A "roaming" authenticator, like a YubiKey

    https://www.w3.org/TR/webauthn-2/#enumdef-authenticatorattachment
    """

    PLATFORM = "platform"
    CROSS_PLATFORM = "cross-platform"


class WebAuthnHint(models.TextChoices):
    """Hints to guide the browser in prioritizing the preferred authenticator during
    WebAuthn registration and authentication. Unlike authenticatorAttachment, hints are
    advisory and browsers may ignore them.

    Members:
        `SECURITY_KEY`: A portable FIDO2 authenticator, like a YubiKey
        `CLIENT_DEVICE`: The device WebAuthn is being called on, like TouchID or Windows Hello
        `HYBRID`: A platform authenticator on a mobile device, accessed via QR code

    https://w3c.github.io/webauthn/#enumdef-publickeycredentialhint
    """

    SECURITY_KEY = "security-key"
    CLIENT_DEVICE = "client-device"
    HYBRID = "hybrid"


class AuthenticatorWebAuthnStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup WebAuthn-based authentication for the user."""

    user_verification = models.TextField(
        choices=UserVerification.choices,
        default=UserVerification.PREFERRED,
    )
    resident_key_requirement = models.TextField(
        choices=ResidentKeyRequirement.choices,
        default=ResidentKeyRequirement.PREFERRED,
    )
    authenticator_attachment = models.TextField(  # noqa: DJ001
        choices=AuthenticatorAttachment.choices, default=None, null=True
    )

    hints = ArrayField(
        models.TextField(choices=WebAuthnHint.choices),
        default=list,
        blank=True,
    )

    device_type_restrictions = models.ManyToManyField(
        "WebAuthnDeviceType", blank=True, through="AuthenticatorWebAuthnStageDeviceTypeRestriction"
    )

    max_attempts = models.PositiveIntegerField(default=0)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_webauthn.api.stages import (
            AuthenticatorWebAuthnStageSerializer,
        )

        return AuthenticatorWebAuthnStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.authenticator_webauthn.stage import AuthenticatorWebAuthnStageView

        return AuthenticatorWebAuthnStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-webauthn-form"

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-webauthn",
            }
        )

    def __str__(self) -> str:
        return f"WebAuthn Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("WebAuthn Authenticator Setup Stage")
        verbose_name_plural = _("WebAuthn Authenticator Setup Stages")


class WebAuthnDevice(SerializerModel, Device):
    """WebAuthn Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    name = models.TextField(max_length=200)
    credential_id = models.TextField(unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    rp_id = models.CharField(max_length=253)

    created_on = models.DateTimeField(auto_now_add=True)
    last_t = models.DateTimeField(default=now)

    attestation_certificate_pem = models.TextField(null=True, default=None)
    attestation_certificate_fingerprint = models.TextField(null=True, default=None)
    aaguid = models.TextField(default=UNKNOWN_DEVICE_TYPE_AAGUID)
    device_type = models.ForeignKey(
        "WebAuthnDeviceType", on_delete=models.SET_DEFAULT, null=True, default=None
    )

    def get_challenge_for_device(
        self, request: HttpRequest, executor: FlowExecutorView, stage: Stage | None = None
    ):
        """Send the client a challenge that we'll check later"""
        executor.plan.context.pop(PLAN_CONTEXT_WEBAUTHN_CHALLENGE, None)
        stage = cast(AuthenticatorValidateStage, stage or executor.current_stage)

        allowed_credentials = []

        if self.pk:
            # We want all the user's WebAuthn devices and merge their challenges
            for user_device in WebAuthnDevice.objects.filter(user=self.user).order_by("name"):
                user_device: WebAuthnDevice
                allowed_credentials.append(user_device.descriptor)

        authentication_options = generate_authentication_options(
            rp_id=get_rp_id(request),
            allow_credentials=allowed_credentials,
            user_verification=UserVerificationRequirement(stage.webauthn_user_verification),
        )

        executor.plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = authentication_options.challenge

        options_dict = options_to_json_dict(authentication_options)
        if stage.webauthn_hints:
            options_dict["hints"] = list(stage.webauthn_hints)
        return options_dict

    def validate_challenge(
        self,
        request: HttpRequest,
        input: dict,
        executor: FlowExecutorView,
        user: User,
        stage: Stage | None = None,
    ):
        """Validate WebAuthn Challenge"""
        from authentik.stages.authenticator_validate.models import DeviceClasses

        challenge = executor.plan.context.get(PLAN_CONTEXT_WEBAUTHN_CHALLENGE)
        stage = stage or executor.current_stage

        if "MinuteMaid" in request.META.get("HTTP_USER_AGENT", ""):
            # Workaround for Android sign-in, when signing into Google Workspace on android while
            # adding the account to the system (not in Chrome), for some reason `type` is not set
            # so in that case we fall back to `public-key`
            # since that's the only option we support anyways
            input.setdefault("type", PublicKeyCredentialType.PUBLIC_KEY)
        try:
            credential = parse_authentication_credential_json(input)
        except InvalidJSONStructure as exc:
            LOGGER.warning("Invalid WebAuthn challenge response", exc=exc)
            raise ValidationError("Invalid device", "invalid") from None

        device = WebAuthnDevice.objects.filter(credential_id=credential.id).first()
        if not device:
            raise ValidationError("Invalid device", "invalid")
        # We can only check the device's user if the user we're given isn't anonymous
        # as this validation is also used for password-less login where webauthn is the very first
        # step done by a user. Only if this validation happens at a later stage we can check
        # that the device belongs to the user
        if not user.is_anonymous and device.user != user:
            raise ValidationError("Invalid device", "invalid")
        # When a device_type was set when creating the device (2024.4+), and we have a limitation,
        # make sure the device type is allowed.
        if (
            device.device_type
            and stage.webauthn_allowed_device_types.exists()
            and not stage.webauthn_allowed_device_types.filter(pk=device.device_type.pk).exists()
        ):
            raise ValidationError(
                _(
                    "Invalid device type. Contact your {brand} administrator for help.".format(
                        brand=request.brand.branding_title
                    )
                ),
                "invalid",
            )
        try:
            authentication_verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=get_rp_id(request),
                expected_origin=get_origin(request),
                credential_public_key=base64url_to_bytes(device.public_key),
                credential_current_sign_count=device.sign_count,
                require_user_verification=stage.webauthn_user_verification
                == UserVerification.REQUIRED,
            )
        except InvalidAuthenticationResponse as exc:
            LOGGER.warning("Assertion failed", exc=exc)
            login_failed.send(
                sender=__name__,
                credentials={"username": user.username},
                request=request,
                stage=executor.current_stage,
                context={
                    PLAN_CONTEXT_METHOD_ARGS: {
                        "device": device,
                        "device_class": DeviceClasses.WEBAUTHN.value,
                        "device_type": device.device_type,
                    },
                },
            )
            raise ValidationError("Assertion failed") from exc

        with audit_ignore():
            device.set_sign_count(authentication_verification.new_sign_count)
        return device

    @property
    def descriptor(self) -> PublicKeyCredentialDescriptor:
        """Get a publickeydescriptor for this device"""
        return PublicKeyCredentialDescriptor(id=base64url_to_bytes(self.credential_id))

    @property
    def attestation_certificate(self) -> Certificate | None:
        if not self.attestation_certificate_pem:
            return None
        return load_pem_x509_certificate(self.attestation_certificate_pem.encode())

    def set_sign_count(self, sign_count: int) -> None:
        """Set the sign_count and update the last_t datetime."""
        self.sign_count = sign_count
        self.last_t = now()
        self.save()

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_webauthn.api.devices import WebAuthnDeviceSerializer

        return WebAuthnDeviceSerializer

    def __str__(self):
        return str(self.name) or str(self.user_id)

    class Meta:
        verbose_name = _("WebAuthn Device")
        verbose_name_plural = _("WebAuthn Devices")


class WebAuthnDeviceType(InternallyManagedMixin, SerializerModel):
    """WebAuthn device type, used to restrict which device types are allowed"""

    aaguid = models.UUIDField(primary_key=True, unique=True)

    description = models.TextField()
    icon = models.TextField(null=True)

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_webauthn.api.device_types import (
            WebAuthnDeviceTypeSerializer,
        )

        return WebAuthnDeviceTypeSerializer

    class Meta:
        verbose_name = _("WebAuthn Device type")
        verbose_name_plural = _("WebAuthn Device types")

    def __str__(self) -> str:
        return f"WebAuthn device type {self.description} ({self.aaguid})"


class AuthenticatorWebAuthnStageDeviceTypeRestriction(SimpleThroughModel):
    authenticator_webauthn_stage = models.ForeignKey(
        AuthenticatorWebAuthnStage,
        on_delete=models.CASCADE,
        db_column="authenticatorwebauthnstage_id",
    )
    device_type_restriction = models.ForeignKey(
        WebAuthnDeviceType,
        on_delete=models.CASCADE,
        db_column="webauthndevicetype_id",
    )

    class Meta:
        db_table = "authentik_stages_authenticator_webauthn_authenticatorwebaute3a7"
        unique_together = (("authenticator_webauthn_stage", "device_type_restriction"),)
        verbose_name = _("Authenticator WebAuthn Stage Device Type Restriction")
        verbose_name_plural = _("Authenticator WebAuthn Stage Device Type Restrictions")

    def __str__(self):
        return (
            "AuthenticatorWebAuthnStageDeviceTypeRestriction for AuthenticatorWebAuthnStage "
            f"{self.authenticator_webauthn_stage_id} "
            f"and WebAuthnDeviceType {self.device_type_restriction_id}."
        )
