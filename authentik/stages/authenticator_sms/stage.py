"""SMS Setup stage"""

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, IntegerField

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallengeMixin,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_sms.models import (
    AuthenticatorSMSStage,
    SMSDevice,
    hash_phone_number,
)
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

SESSION_KEY_SMS_DEVICE = "authentik/stages/authenticator_sms/sms_device"
PLAN_CONTEXT_PHONE = "phone"


class AuthenticatorSMSChallenge(WithUserInfoChallengeMixin, Challenge):
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
        if "code" not in attrs:
            if "phone_number" not in attrs:
                raise ValidationError("phone_number required")
            self.device.phone_number = attrs["phone_number"]
            self.stage.validate_and_send(attrs["phone_number"])
            return super().validate(attrs)
        if not self.device.verify_token(str(attrs["code"])):
            raise ValidationError(_("Code does not match"))
        self.device.confirmed = True
        return super().validate(attrs)


class AuthenticatorSMSStageView(ChallengeStageView):
    """OTP sms Setup stage"""

    response_class = AuthenticatorSMSChallengeResponse

    def validate_and_send(self, phone_number: str):
        """Validate phone number and send message"""
        stage: AuthenticatorSMSStage = self.executor.current_stage
        hashed_number = hash_phone_number(phone_number)
        query = Q(phone_number=hashed_number) | Q(phone_number=phone_number)
        if SMSDevice.objects.filter(query, stage=stage.pk).exists():
            raise ValidationError(_("Invalid phone number"))
        # No code yet, but we have a phone number, so send a verification message
        device: SMSDevice = self.request.session[SESSION_KEY_SMS_DEVICE]
        stage.send(device.token, device)

    def _has_phone_number(self) -> str | None:
        context = self.executor.plan.context
        if PLAN_CONTEXT_PHONE in context.get(PLAN_CONTEXT_PROMPT, {}):
            self.logger.debug("got phone number from plan context")
            return context.get(PLAN_CONTEXT_PROMPT, {}).get(PLAN_CONTEXT_PHONE)
        if SESSION_KEY_SMS_DEVICE in self.request.session:
            self.logger.debug("got phone number from device in session")
            device: SMSDevice = self.request.session[SESSION_KEY_SMS_DEVICE]
            if device.phone_number == "":
                return None
            return device.phone_number
        return None

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return AuthenticatorSMSChallenge(
            data={
                "phone_number_required": self._has_phone_number() is None,
            }
        )

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        response = super().get_response_instance(data)
        response.device = self.request.session[SESSION_KEY_SMS_DEVICE]
        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.get_pending_user()

        stage: AuthenticatorSMSStage = self.executor.current_stage

        if SESSION_KEY_SMS_DEVICE not in self.request.session:
            device = SMSDevice(user=user, confirmed=False, stage=stage, name="SMS Device")
            device.generate_token(commit=False)
            self.request.session[SESSION_KEY_SMS_DEVICE] = device
            if phone_number := self._has_phone_number():
                device.phone_number = phone_number
                try:
                    self.validate_and_send(phone_number)
                except ValidationError as exc:
                    # We had a phone number given already (at this point only possible from flow
                    # context), but an error occurred while sending a number (most likely)
                    # due to a duplicate device, so delete the number we got given, reset the state
                    # (ish) and retry
                    device.phone_number = ""
                    self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}).pop(
                        PLAN_CONTEXT_PHONE, None
                    )
                    self.request.session.pop(SESSION_KEY_SMS_DEVICE, None)
                    self.logger.warning("failed to send SMS message to pre-set number", exc=exc)
                    return self.get(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """SMS Token is validated by challenge"""
        device: SMSDevice = self.request.session[SESSION_KEY_SMS_DEVICE]
        if not device.confirmed:
            return self.challenge_invalid(response)
        stage: AuthenticatorSMSStage = self.executor.current_stage
        if stage.verify_only:
            self.logger.debug("Hashing number on device")
            device.set_hashed_number()
        device.save()
        del self.request.session[SESSION_KEY_SMS_DEVICE]
        return self.executor.stage_ok()
