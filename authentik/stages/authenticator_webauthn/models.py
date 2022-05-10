"""WebAuthn stage"""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.models import Device
from rest_framework.serializers import BaseSerializer
from webauthn.helpers.base64url_to_bytes import base64url_to_bytes
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage


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


class AuthenticateWebAuthnStage(ConfigurableStage, Stage):
    """WebAuthn stage"""

    user_verification = models.TextField(
        choices=UserVerification.choices,
        default=UserVerification.PREFERRED,
    )
    resident_key_requirement = models.TextField(
        choices=ResidentKeyRequirement.choices,
        default=ResidentKeyRequirement.PREFERRED,
    )
    authenticator_attachment = models.TextField(
        choices=AuthenticatorAttachment.choices, default=None, null=True
    )

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_webauthn.api import AuthenticateWebAuthnStageSerializer

        return AuthenticateWebAuthnStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_webauthn.stage import AuthenticatorWebAuthnStageView

        return AuthenticatorWebAuthnStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-webauthn-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-webauthn",
            }
        )

    def __str__(self) -> str:
        return f"WebAuthn Authenticator Setup Stage {self.name}"

    class Meta:

        verbose_name = _("WebAuthn Authenticator Setup Stage")
        verbose_name_plural = _("WebAuthn Authenticator Setup Stages")


class WebAuthnDevice(Device):
    """WebAuthn Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    name = models.TextField(max_length=200)
    credential_id = models.CharField(max_length=300, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    rp_id = models.CharField(max_length=253)

    created_on = models.DateTimeField(auto_now_add=True)
    last_t = models.DateTimeField(default=now)

    @property
    def descriptor(self) -> PublicKeyCredentialDescriptor:
        """Get a publickeydescriptor for this device"""
        return PublicKeyCredentialDescriptor(id=base64url_to_bytes(self.credential_id))

    def set_sign_count(self, sign_count: int) -> None:
        """Set the sign_count and update the last_t datetime."""
        self.sign_count = sign_count
        self.last_t = now()
        self.save()

    def __str__(self):
        return self.name or str(self.user)

    class Meta:

        verbose_name = _("WebAuthn Device")
        verbose_name_plural = _("WebAuthn Devices")
