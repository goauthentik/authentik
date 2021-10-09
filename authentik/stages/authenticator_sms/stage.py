"""SMS Setup stage"""
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
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
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice

LOGGER = get_logger()
SESSION_SMS_DEVICE = "sms_device"


class AuthenticatorSMSChallenge(WithUserInfoChallenge):
    """SMS Setup challenge"""

    config_url = CharField()
    component = CharField(default="ak-stage-authenticator-sms")


class AuthenticatorSMSChallengeResponse(ChallengeResponse):
    """SMS Challenge response, device is set by get_response_instance"""

    device: SMSDevice

    code = IntegerField()
    component = CharField(default="ak-stage-authenticator-sms")

    def validate_code(self, code: int) -> int:
        """Validate sms code"""
        if self.device is not None:
            if not self.device.verify_token(code):
                raise ValidationError(_("Code does not match"))
        return code


class AuthenticatorSMSStageView(ChallengeStageView):
    """OTP sms Setup stage"""

    response_class = AuthenticatorSMSChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return AuthenticatorSMSChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
            }
        )

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        response = super().get_response_instance(data)
        response.device = self.request.session[SESSION_SMS_DEVICE]
        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()

        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if SMSDevice.objects.filter(user=user).exists():
            return self.executor.stage_ok()

        stage: AuthenticatorSMSStage = self.executor.current_stage

        if SESSION_SMS_DEVICE not in self.request.session:
            device = SMSDevice(user=user, confirmed=True, digits=stage.digits)

            self.request.session[SESSION_SMS_DEVICE] = device
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """SMS Token is validated by challenge"""
        device: SMSDevice = self.request.session[SESSION_SMS_DEVICE]
        device.save()
        del self.request.session[SESSION_SMS_DEVICE]
        return self.executor.stage_ok()
