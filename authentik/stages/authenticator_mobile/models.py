"""Mobile authenticator stage"""
from typing import Optional
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _
from django.views import View
from firebase_admin import credentials, initialize_app
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import (
    AndroidConfig,
    AndroidNotification,
    APNSConfig,
    APNSPayload,
    Aps,
    Message,
    Notification,
    send,
)
from rest_framework.serializers import BaseSerializer, Serializer
from structlog.stdlib import get_logger

from authentik.core.models import ExpiringModel
from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.generators import generate_id
from authentik.lib.models import SerializerModel
from authentik.stages.authenticator.models import Device
from authentik.tenants.utils import DEFAULT_TENANT

cred = credentials.Certificate("firebase.json")
initialize_app(cred)

LOGGER = get_logger()


def default_token_key():
    """Default token key"""
    return generate_id(40)


class AuthenticatorMobileStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup Mobile authenticator devices"""

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_mobile.api.stage import (
            AuthenticatorMobileStageSerializer,
        )

        return AuthenticatorMobileStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_mobile.stage import AuthenticatorMobileStageView

        return AuthenticatorMobileStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-mobile-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-mobile",
            }
        )

    def __str__(self) -> str:
        return f"Mobile Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("Mobile Authenticator Setup Stage")
        verbose_name_plural = _("Mobile Authenticator Setup Stages")


class MobileDevice(SerializerModel, Device):
    """Mobile authenticator for a single user"""

    uuid = models.UUIDField(primary_key=True, default=uuid4)

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorMobileStage, on_delete=models.CASCADE)

    device_id = models.TextField(unique=True)
    firebase_token = models.TextField(blank=True)

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_mobile.api.device import MobileDeviceSerializer

        return MobileDeviceSerializer

    def send_message(self, request: Optional[HttpRequest], **context):
        """Send mobile message"""
        branding = DEFAULT_TENANT.branding_title
        domain = ""
        if request:
            branding = request.tenant.branding_title
            domain = request.get_host()
        message = Message(
            notification=Notification(
                title=__("%(brand)s authentication request" % {"brand": branding}),
                body=__(
                    "%(user)s is attempting to log in to %(domain)s"
                    % {
                        "user": self.user.username,
                        "domain": domain,
                    }
                ),
            ),
            android=AndroidConfig(
                priority="normal",
                notification=AndroidNotification(icon="stock_ticker_update", color="#f45342"),
            ),
            apns=APNSConfig(
                headers={"apns-push-type": "alert", "apns-priority": "10"},
                payload=APNSPayload(
                    aps=Aps(
                        badge=0,
                        sound="default",
                        content_available=True,
                    ),
                    interruption_level="time-sensitive",
                ),
            ),
            token=self.firebase_token,
        )
        try:
            response = send(message)
            LOGGER.debug("Sent notification", id=response)
        except (ValueError, FirebaseError) as exc:
            LOGGER.warning("failed to push", exc=exc)
        return True

    def __str__(self):
        return str(self.name) or str(self.user)

    class Meta:
        verbose_name = _("Mobile Device")
        verbose_name_plural = _("Mobile Devices")


class MobileDeviceToken(ExpiringModel):
    """Mobile device token"""

    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    token = models.TextField(default=default_token_key)
