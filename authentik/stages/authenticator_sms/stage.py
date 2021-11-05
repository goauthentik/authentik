"""SMS Setup stage"""
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, IntegerField
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
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()
SESSION_SMS_DEVICE = "sms_device"


class AuthenticatorSMSChallenge(WithUserInfoChallenge):
    """SMS Setup challenge"""

    # Set to true if no previous prompt stage set the phone number
    # this stage will also check prompt_data.phone
    phone_number_required = BooleanField(default=True)
    component = CharField(default="ak-stage-authenticator-sms")


class AuthenticatorSMSChallengeResponse(ChallengeResponse):
    """SMS Challenge response, device is set by get_response_instance"""

    device: SMSDevice

    code = IntegerField(required=False)
    phone_number = CharField(required=False)

    component = CharField(default="ak-stage-authenticator-sms")

    def validate(self, attrs: dict) -> dict:
        """Check"""
        stage: AuthenticatorSMSStage = self.device.stage
        if "code" not in attrs:
            self.device.phone_number = attrs["phone_number"]
            # No code yet, but we have a phone number, so send a verification message
            stage.send(self.device.token, self.device)
            return super().validate(attrs)
        if not self.device.verify_token(str(attrs["code"])):
            raise ValidationError(_("Code does not match"))
        self.device.confirmed = True
        return super().validate(attrs)


class AuthenticatorSMSStageView(ChallengeStageView):
    """OTP sms Setup stage"""

    response_class = AuthenticatorSMSChallengeResponse

    def _has_phone_number(self) -> Optional[str]:
        context = self.executor.plan.context
        if "phone" in context.get(PLAN_CONTEXT_PROMPT, {}):
            LOGGER.debug("got phone number from plan context")
            return context.get(PLAN_CONTEXT_PROMPT, {}).get("phone")
        if SESSION_SMS_DEVICE in self.request.session:
            LOGGER.debug("got phone number from device in session")
            device: SMSDevice = self.request.session[SESSION_SMS_DEVICE]
            if device.phone_number == "":
                return None
            return device.phone_number
        return None

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return AuthenticatorSMSChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "phone_number_required": self._has_phone_number() is None,
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
            device = SMSDevice(user=user, confirmed=False, stage=stage, name="SMS Device")
            device.generate_token(commit=False)
            if phone_number := self._has_phone_number():
                device.phone_number = phone_number
            self.request.session[SESSION_SMS_DEVICE] = device
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """SMS Token is validated by challenge"""
        device: SMSDevice = self.request.session[SESSION_SMS_DEVICE]
        if not device.confirmed:
            return self.challenge_invalid(response)
        device.save()
        del self.request.session[SESSION_SMS_DEVICE]
        return self.executor.stage_ok()
