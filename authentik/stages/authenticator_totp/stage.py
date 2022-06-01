"""TOTP Setup stage"""
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import ValidationError

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage
from authentik.stages.authenticator_totp.settings import OTP_TOTP_ISSUER


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
        if not self.device:
            raise ValidationError(_("Code does not match"))
        if not self.device.verify_token(code):
            self.device.confirmed = False
            raise ValidationError(_("Code does not match"))
        return code


class AuthenticatorTOTPStageView(ChallengeStageView):
    """OTP totp Setup stage"""

    response_class = AuthenticatorTOTPChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        user = self.get_pending_user()
        device: TOTPDevice = TOTPDevice.objects.filter(user=user).first()
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
        user = self.get_pending_user()
        response.device = TOTPDevice.objects.filter(user=user).first()
        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.get_pending_user()
        if not user.is_authenticated:
            self.logger.debug("No pending user, continuing")
            return self.executor.stage_ok()

        stage: AuthenticatorTOTPStage = self.executor.current_stage

        devices = TOTPDevice.objects.filter(user=user)
        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if devices.exists():
            if not any(x.confirmed for x in devices):
                return super().get(request, *args, **kwargs)
            return self.executor.stage_ok()

        TOTPDevice.objects.create(
            user=user, confirmed=False, digits=stage.digits, name="TOTP Authenticator"
        )
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """TOTP Token is validated by challenge"""
        user = self.get_pending_user()
        device: TOTPDevice = TOTPDevice.objects.filter(user=user).first()
        if not device:
            return self.executor.stage_invalid()
        device.confirmed = True
        device.save()
        return self.executor.stage_ok()
