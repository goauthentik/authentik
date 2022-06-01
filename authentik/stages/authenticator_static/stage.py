"""Static OTP Setup stage"""
from django.http import HttpRequest, HttpResponse
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from rest_framework.fields import CharField, ListField

from authentik.flows.challenge import ChallengeResponse, ChallengeTypes, WithUserInfoChallenge
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_static.models import AuthenticatorStaticStage


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
        user = self.get_pending_user()
        tokens: list[StaticToken] = StaticToken.objects.filter(device__user=user)
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

        devices = StaticDevice.objects.filter(user=user)
        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if devices.exists():
            if not any(x.confirmed for x in devices):
                return super().get(request, *args, **kwargs)
            return self.executor.stage_ok()

        device = StaticDevice.objects.create(user=user, confirmed=False, name="Static Token")
        for _ in range(0, stage.token_count):
            StaticToken.objects.create(device=device, token=StaticToken.random_token())
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Verify OTP Token"""
        user = self.get_pending_user()
        device: StaticDevice = StaticDevice.objects.filter(user=user).first()
        if not device:
            return self.executor.stage_invalid()
        device.confirmed = True
        device.save()
        return self.executor.stage_ok()
