"""OTP Validation"""
from django.http import HttpRequest, HttpResponse
from django_otp import user_has_device
from rest_framework.fields import IntegerField
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.models import NotConfiguredAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_validate.forms import ValidationForm
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage

LOGGER = get_logger()


class CodeChallengeResponse(ChallengeResponse):
    """Challenge used for Code-based authenticators"""

    code = IntegerField(min_value=0)


class WebAuthnChallengeResponse(ChallengeResponse):
    """Challenge used for WebAuthn authenticators"""


class AuthenticatorValidateStageView(ChallengeStageView):
    """OTP Validation"""

    form_class = ValidationForm

    # def get_form_kwargs(self, **kwargs) -> dict[str, Any]:
    #     kwargs = super().get_form_kwargs(**kwargs)
    #     kwargs["user"] = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
    #     return kwargs

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check if a user is set, and check if the user has any devices
        if not, we can skip this entire stage"""
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

    # def get_form_kwargs(self, **kwargs) -> Dict[str, Any]:
    #     kwargs = super().get_form_kwargs(**kwargs)
    #     kwargs["user"] = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
    #     return kwargs

    def get_challenge(self) -> Challenge:
        return Challenge(
            {
                "type": ChallengeTypes.native,
                # TODO: use component based on devices
                "component": "ak-stage-authenticator-validate",
                "args": {"user": "foo.bar.baz"},
            }
        )

    def challenge_valid(self, challenge: ChallengeResponse) -> HttpResponse:
        print(challenge)
        return HttpResponse()

    # def form_valid(self, form: ValidationForm) -> HttpResponse:
    #     """Verify OTP Token"""
    #     # Since we do token checking in the form, we know the token is valid here
    #     # so we can just continue
    #     return self.executor.stage_ok()
