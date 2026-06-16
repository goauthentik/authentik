"""Authenticator Validation Stage"""

from typing import TYPE_CHECKING

from django.apps import apps
from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import NotConfiguredAction, Stage
from authentik.lib.utils.time import timedelta_string_validator
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_webauthn.models import UserVerification, WebAuthnHint

if TYPE_CHECKING:
    from authentik.stages.authenticator_validate.challenge import DeviceChallenger, FlowContext


class DeviceClasses(models.TextChoices):
    """Device classes this stage can validate"""

    # device class must match Device's class name so StaticDevice -> static
    STATIC = "static", _("Static")
    TOTP = "totp", _("TOTP")
    WEBAUTHN = "webauthn", _("WebAuthn")
    DUO = "duo", _("Duo")
    SMS = "sms", _("SMS")
    EMAIL = "email", _("Email")

    @staticmethod
    def from_model_label(model_label: str) -> DeviceClasses:
        return getattr(
            DeviceClasses, model_label.rsplit(".", maxsplit=1)[-1][: -len("device")].upper()
        )

    @staticmethod
    def from_model(model: type[Device]) -> DeviceClasses:
        return DeviceClasses.from_model_label(model._meta.label_lower)

    def as_type(self) -> type[Device]:
        """Get the Device model class for this device class"""
        model_name = f"{self.value}device"
        app_label_map = {
            DeviceClasses.STATIC: "authentik_stages_authenticator_static",
            DeviceClasses.TOTP: "authentik_stages_authenticator_totp",
            DeviceClasses.WEBAUTHN: "authentik_stages_authenticator_webauthn",
            DeviceClasses.DUO: "authentik_stages_authenticator_duo",
            DeviceClasses.SMS: "authentik_stages_authenticator_sms",
            DeviceClasses.EMAIL: "authentik_stages_authenticator_email",
        }
        app_label = app_label_map.get(self)
        return apps.get_model(app_label, model_name)


def default_device_classes() -> list:
    """By default, accept all device classes"""
    return [
        DeviceClasses.STATIC,
        DeviceClasses.TOTP,
        DeviceClasses.WEBAUTHN,
        DeviceClasses.DUO,
        DeviceClasses.SMS,
        DeviceClasses.EMAIL,
    ]


class AuthenticatorValidateStage(Stage):
    """Validate user's configured Multi Factor Authentication."""

    not_configured_action = models.TextField(
        choices=NotConfiguredAction.choices, default=NotConfiguredAction.SKIP
    )

    configuration_stages = models.ManyToManyField(
        Stage,
        blank=True,
        default=None,
        related_name="+",
        help_text=_(
            "Stages used to configure Authenticator when user doesn't have any compatible "
            "devices. After this configuration Stage passes, the user is not prompted again."
        ),
    )

    device_classes = ArrayField(
        models.TextField(choices=DeviceClasses.choices),
        help_text=_("Device classes which can be used to authenticate"),
        default=default_device_classes,
    )

    last_auth_threshold = models.TextField(
        default="seconds=0",
        validators=[timedelta_string_validator],
        help_text=_(
            "If any of the user's device has been used within this threshold, this "
            "stage will be skipped"
        ),
    )

    webauthn_user_verification = models.TextField(
        help_text=_("Enforce user verification for WebAuthn devices."),
        choices=UserVerification.choices,
        default=UserVerification.PREFERRED,
    )
    webauthn_hints = ArrayField(
        models.TextField(choices=WebAuthnHint.choices),
        default=list,
        blank=True,
    )
    webauthn_allowed_device_types = models.ManyToManyField(
        "authentik_stages_authenticator_webauthn.WebAuthnDeviceType", blank=True
    )

    email_otp_throttling_factor = models.FloatField(default=1)
    sms_otp_throttling_factor = models.FloatField(default=1)
    totp_otp_throttling_factor = models.FloatField(default=1)
    static_otp_throttling_factor = models.FloatField(default=1)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageSerializer

        return AuthenticatorValidateStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.authenticator_validate.stage import AuthenticatorValidateStageView

        return AuthenticatorValidateStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-validate-form"

    def get_throttling_factor(self, device_class: DeviceClasses) -> float | None:
        if device_class == DeviceClasses.EMAIL:
            return self.email_otp_throttling_factor
        elif device_class == DeviceClasses.SMS:
            return self.sms_otp_throttling_factor
        elif device_class == DeviceClasses.TOTP:
            return self.totp_otp_throttling_factor
        elif device_class == DeviceClasses.STATIC:
            return self.static_otp_throttling_factor
        return None

    def get_device_challenger(
        self,
        device_class: DeviceClasses,
        request: HttpRequest,
        flow_context: FlowContext,
    ) -> DeviceChallenger:
        from authentik.stages.authenticator_validate.challenge import DeviceChallenger

        device_type = device_class.as_type()
        return DeviceChallenger.get_subclass_for_device_type(device_type)(
            request, self, flow_context
        )

    class Meta:
        verbose_name = _("Authenticator Validation Stage")
        verbose_name_plural = _("Authenticator Validation Stages")
