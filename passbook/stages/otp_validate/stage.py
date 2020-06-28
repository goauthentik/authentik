from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django_otp import match_token, user_has_device
from django_otp.models import Device
from structlog import get_logger

from passbook.flows.models import NotConfiguredAction, Stage
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import StageView
from passbook.stages.otp_validate.forms import ValidationForm
from passbook.stages.otp_validate.models import OTPValidateStage

LOGGER = get_logger()


class OTPValidateStageView(FormView, StageView):

    form_class = ValidationForm

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        has_devices = user_has_device(user)
        stage: OTPValidateStage = self.executor.current_stage

        if not has_devices:
            if stage.not_configured_action == NotConfiguredAction.SKIP:
                LOGGER.debug("OTP not configured, skipping stage")
                return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: ValidationForm) -> HttpResponse:
        """Verify OTP Token"""
        device = match_token(
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER],
            form.cleaned_data.get("code"),
        )
        if not device:
            messages.error(self.request, _("Invalid OTP."))
            return self.form_invalid(form)
        return self.executor.stage_ok()
