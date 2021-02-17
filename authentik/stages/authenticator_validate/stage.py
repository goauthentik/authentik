"""OTP Validation"""
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.views.generic import FormView
from django_otp import user_has_device
from structlog.stdlib import get_logger

from authentik.flows.models import NotConfiguredAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.authenticator_validate.forms import ValidationForm
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage

LOGGER = get_logger()


class AuthenticatorValidateStageView(FormView, StageView):
    """OTP Validation"""

    form_class = ValidationForm

    def get_form_kwargs(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs["user"] = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        return kwargs

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        has_devices = user_has_device(user)
        stage: AuthenticatorValidateStage = self.executor.current_stage

        if not has_devices:
            if stage.not_configured_action == NotConfiguredAction.SKIP:
                LOGGER.debug("Authenticator not configured, skipping stage")
                return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: ValidationForm) -> HttpResponse:
        """Verify OTP Token"""
        # Since we do token checking in the form, we know the token is valid here
        # so we can just continue
        return self.executor.stage_ok()
