"""TOTP Setup stage"""
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage
from authentik.stages.authenticator_totp.settings import OTP_TOTP_ISSUER

LOGGER = get_logger()
SESSION_TOTP_DEVICE = "totp_device"


class AuthenticatorTOTPChallenge(WithUserInfoChallenge):
    """TOTP Setup challenge"""

    config_url = CharField()
    component = CharField(default="ak-stage-authenticator-totp")


class AuthenticatorTOTPChallengeResponse(ChallengeResponse):
    """TOTP Challenge response, device is set by get_response_instance"""

    device: TOTPDevice

    code = IntegerField()
    component = CharField(default="ak-stage-authenticator-totp")

    def validate_code(self, code: int) -> int:
        """Validate totp code"""
        if self.device is not None:
            if not self.device.verify_token(code):
                raise ValidationError(_("Code does not match"))
        return code


class AuthenticatorTOTPStageView(ChallengeStageView):
    """OTP totp Setup stage"""

    response_class = AuthenticatorTOTPChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        device: TOTPDevice = self.request.session[SESSION_TOTP_DEVICE]
        return AuthenticatorTOTPChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "config_url": device.config_url.replace(
                    OTP_TOTP_ISSUER, slugify(self.request.tenant.branding_title)
                ),
            }
        )

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        response = super().get_response_instance(data)
        response.device = self.request.session[SESSION_TOTP_DEVICE]
        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()

        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if TOTPDevice.objects.filter(user=user).exists():
            return self.executor.stage_ok()

        stage: AuthenticatorTOTPStage = self.executor.current_stage

        if SESSION_TOTP_DEVICE not in self.request.session:
            device = TOTPDevice(
                user=user, confirmed=True, digits=stage.digits, name="TOTP Authenticator"
            )

            self.request.session[SESSION_TOTP_DEVICE] = device
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """TOTP Token is validated by challenge"""
        device: TOTPDevice = self.request.session[SESSION_TOTP_DEVICE]
        device.save()
        del self.request.session[SESSION_TOTP_DEVICE]
        return self.executor.stage_ok()
