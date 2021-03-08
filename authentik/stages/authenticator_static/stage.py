"""Static OTP Setup stage"""
from django.http import HttpRequest, HttpResponse
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from rest_framework.fields import CharField, ListField
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_static.models import AuthenticatorStaticStage

LOGGER = get_logger()
SESSION_STATIC_DEVICE = "static_device"
SESSION_STATIC_TOKENS = "static_device_tokens"


class AuthenticatorStaticChallenge(WithUserInfoChallenge):
    """Static authenticator challenge"""

    codes = ListField(child=CharField())


class AuthenticatorStaticStageView(ChallengeStageView):
    """Static OTP Setup stage"""

    def get_challenge(self, *args, **kwargs) -> AuthenticatorStaticChallenge:
        tokens: list[StaticToken] = self.request.session[SESSION_STATIC_TOKENS]
        return AuthenticatorStaticChallenge(
            data={
                "type": ChallengeTypes.native.value,
                "component": "ak-stage-authenticator-static",
                "codes": [token.token for token in tokens],
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()

        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if StaticDevice.objects.filter(user=user).exists():
            return self.executor.stage_ok()

        stage: AuthenticatorStaticStage = self.executor.current_stage

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

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Verify OTP Token"""
        device: StaticDevice = self.request.session[SESSION_STATIC_DEVICE]
        device.save()
        for token in self.request.session[SESSION_STATIC_TOKENS]:
            token.save()
        del self.request.session[SESSION_STATIC_DEVICE]
        del self.request.session[SESSION_STATIC_TOKENS]
        return self.executor.stage_ok()
