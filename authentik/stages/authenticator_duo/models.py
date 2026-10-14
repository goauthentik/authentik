"""Duo stage"""

from typing import Any, cast
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.db import models
from django.http import Http404, HttpRequest
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _
from django.views import View
from duo_client.admin import Admin
from duo_client.auth import Auth
from rest_framework.serializers import BaseSerializer, Serializer, ValidationError
from structlog.stdlib import get_logger

from authentik.core.models import Application, User
from authentik.core.signals import login_failed
from authentik.core.types import UserSettingSerializer
from authentik.events.models import Event, EventAction
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.models import SerializerModel
from authentik.lib.utils.http import authentik_user_agent
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_validate.models import DeviceClasses
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD_ARGS

LOGGER = get_logger()


class AuthenticatorDuoStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup Duo authentication for the user."""

    api_hostname = models.TextField()

    client_id = models.TextField()
    client_secret = models.TextField()

    admin_integration_key = models.TextField(blank=True, default="")
    admin_secret_key = models.TextField(blank=True, default="")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_duo.api import AuthenticatorDuoStageSerializer

        return AuthenticatorDuoStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.authenticator_duo.stage import AuthenticatorDuoStageView

        return AuthenticatorDuoStageView

    def auth_client(self) -> Auth:
        """Get an API Client to talk to duo"""
        return Auth(
            self.client_id,
            self.client_secret,
            self.api_hostname,
            user_agent=authentik_user_agent(),
        )

    def admin_client(self) -> Admin:
        """Get an API Client to talk to duo"""
        if self.admin_integration_key == "" or self.admin_secret_key == "":  # nosec
            raise ValueError("Admin credentials not configured")
        client = Admin(
            self.admin_integration_key,
            self.admin_secret_key,
            self.api_hostname,
            user_agent=authentik_user_agent(),
        )
        return client

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-duo-form"

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-duo",
            }
        )

    def __str__(self) -> str:
        return f"Duo Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("Duo Authenticator Setup Stage")
        verbose_name_plural = _("Duo Authenticator Setup Stages")


class DuoDevice(SerializerModel, Device):
    """Duo Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorDuoStage, on_delete=models.PROTECT)
    duo_user_id = models.TextField()
    last_t = models.DateTimeField(auto_now=True)

    def validate_challenge(
        self, request: HttpRequest, input: Any, executor: FlowExecutorView, user: User
    ):
        """Duo authentication"""
        if self.user != user:
            LOGGER.warning("device mismatch")
            raise Http404
        stage = cast(AuthenticatorDuoStage, self.stage)

        # Get additional context for push
        pushinfo = {
            __("Domain"): request.get_host(),
        }
        if PLAN_CONTEXT_APPLICATION in executor.plan.context:
            pushinfo[__("Application")] = executor.plan.context.get(
                PLAN_CONTEXT_APPLICATION, Application()
            ).name

        try:
            response = stage.auth_client().auth(
                "auto",
                user_id=self.duo_user_id,
                ipaddr=ClientIPMiddleware.get_client_ip(request),
                type=__(
                    "{brand_name} Login request".format_map(
                        {
                            "brand_name": request.brand.branding_title,
                        }
                    )
                ),
                display_username=user.username,
                device="auto",
                pushinfo=urlencode(pushinfo),
            )
            # {'result': 'allow', 'status': 'allow', 'status_msg': 'Success. Logging you in...'}
            if response["result"] == "deny":
                LOGGER.debug(
                    "duo push response", result=response["result"], msg=response["status_msg"]
                )
                login_failed.send(
                    sender=__name__,
                    credentials={"username": user.username},
                    request=request,
                    stage=executor.current_stage,
                    context={
                        PLAN_CONTEXT_METHOD_ARGS: {
                            "device_class": DeviceClasses.DUO.value,
                            "duo_response": response,
                        }
                    },
                )
                raise ValidationError("Duo denied access", code="denied")
            return self
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to DUO authenticate user: {str(exc)}",
                user=user,
            ).from_http(request, user)
            raise ValidationError("Duo denied access", code="denied") from exc

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_duo.api import DuoDeviceSerializer

        return DuoDeviceSerializer

    def __str__(self):
        return str(self.name) or str(self.user_id)

    class Meta:
        verbose_name = _("Duo Device")
        verbose_name_plural = _("Duo Devices")
