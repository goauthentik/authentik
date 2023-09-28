"""Static OTP Setup stage"""
from django.http import HttpRequest, HttpResponse
from rest_framework.fields import CharField, ListField

from authentik.flows.challenge import ChallengeResponse, ChallengeTypes, WithUserInfoChallenge
from authentik.flows.stage import ChallengeStageView
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_static.models import (
    AuthenticatorStaticStage,
    StaticDevice,
    StaticToken,
)

SESSION_STATIC_DEVICE = "static_device"
SESSION_STATIC_TOKENS = "static_device_tokens"


class AuthenticatorStaticChallenge(WithUserInfoChallenge):
    """Static authenticator challenge"""

    codes = ListField(child=CharField())
    component = CharField(default="ak-stage-authenticator-static")


class AuthenticatorStaticChallengeResponse(ChallengeResponse):
    """Pseudo class for static response"""

    component = CharField(default="ak-stage-authenticator-static")


class AuthenticatorStaticStageView(ChallengeStageView):
    """Static OTP Setup stage"""

    response_class = AuthenticatorStaticChallengeResponse

    def get_challenge(self, *args, **kwargs) -> AuthenticatorStaticChallenge:
        tokens: list[StaticToken] = self.request.session[SESSION_STATIC_TOKENS]
        return AuthenticatorStaticChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "codes": [token.token for token in tokens],
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.get_pending_user()
        if not user.is_authenticated:
            self.logger.debug("No pending user, continuing")
            return self.executor.stage_ok()

        stage: AuthenticatorStaticStage = self.executor.current_stage

        if SESSION_STATIC_DEVICE not in self.request.session:
            device = StaticDevice(user=user, confirmed=False, name="Static Token")
            tokens = []
            for _ in range(0, stage.token_count):
                tokens.append(
                    StaticToken(device=device, token=generate_id(length=stage.token_length))
                )
            self.request.session[SESSION_STATIC_DEVICE] = device
            self.request.session[SESSION_STATIC_TOKENS] = tokens
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Verify OTP Token"""
        device: StaticDevice = self.request.session[SESSION_STATIC_DEVICE]
        device.confirmed = True
        device.save()
        for token in self.request.session[SESSION_STATIC_TOKENS]:
            token.save()
        del self.request.session[SESSION_STATIC_DEVICE]
        del self.request.session[SESSION_STATIC_TOKENS]
        return self.executor.stage_ok()
