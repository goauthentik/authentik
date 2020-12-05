"""Static OTP Setup stage"""
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.views.generic import FormView
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from structlog import get_logger

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.otp_static.forms import SetupForm
from authentik.stages.otp_static.models import OTPStaticStage

LOGGER = get_logger()
SESSION_STATIC_DEVICE = "static_device"
SESSION_STATIC_TOKENS = "static_device_tokens"


class OTPStaticStageView(FormView, StageView):
    """Static OTP Setup stage"""

    form_class = SetupForm

    def get_form_kwargs(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs(**kwargs)
        tokens = self.request.session[SESSION_STATIC_TOKENS]
        kwargs["tokens"] = tokens
        return kwargs

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()

        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if StaticDevice.objects.filter(user=user).exists():
            return self.executor.stage_ok()

        stage: OTPStaticStage = self.executor.current_stage

        if SESSION_STATIC_DEVICE not in self.request.session:
            device = StaticDevice(user=user, confirmed=True)
            tokens = []
            for _ in range(0, stage.token_count):
                tokens.append(
                    StaticToken(device=device, token=StaticToken.random_token())
                )
            self.request.session[SESSION_STATIC_DEVICE] = device
            self.request.session[SESSION_STATIC_TOKENS] = tokens
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: SetupForm) -> HttpResponse:
        """Verify OTP Token"""
        device: StaticDevice = self.request.session[SESSION_STATIC_DEVICE]
        device.save()
        for token in self.request.session[SESSION_STATIC_TOKENS]:
            token.save()
        del self.request.session[SESSION_STATIC_DEVICE]
        del self.request.session[SESSION_STATIC_TOKENS]
        return self.executor.stage_ok()
