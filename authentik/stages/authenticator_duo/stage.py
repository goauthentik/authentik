"""Duo stage"""
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from rest_framework.fields import CharField

from authentik.events.models import Event, EventAction
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import InvalidStageError
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice

SESSION_KEY_DUO_USER_ID = "authentik/stages/authenticator_duo/user_id"
SESSION_KEY_DUO_ACTIVATION_CODE = "authentik/stages/authenticator_duo/activation_code"


class AuthenticatorDuoChallenge(WithUserInfoChallenge):
    """Duo Challenge"""

    activation_barcode = CharField()
    activation_code = CharField()
    stage_uuid = CharField()
    component = CharField(default="ak-stage-authenticator-duo")


class AuthenticatorDuoChallengeResponse(ChallengeResponse):
    """Pseudo class for duo response"""

    component = CharField(default="ak-stage-authenticator-duo")


class AuthenticatorDuoStageView(ChallengeStageView):
    """Duo stage"""

    response_class = AuthenticatorDuoChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        user = self.get_pending_user()
        stage: AuthenticatorDuoStage = self.executor.current_stage
        try:
            enroll = stage.client.enroll(user.username)
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to enroll user: {str(exc)}",
                user=user,
            ).from_http(self.request, user)
            raise InvalidStageError(str(exc)) from exc
        user_id = enroll["user_id"]
        self.request.session[SESSION_KEY_DUO_USER_ID] = user_id
        self.request.session[SESSION_KEY_DUO_ACTIVATION_CODE] = enroll["activation_code"]
        return AuthenticatorDuoChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "activation_barcode": enroll["activation_barcode"],
                "activation_code": enroll["activation_code"],
                "stage_uuid": str(stage.stage_uuid),
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            self.logger.debug("No pending user, continuing")
            return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        # Duo Challenge has already been validated
        stage: AuthenticatorDuoStage = self.executor.current_stage
        user_id = self.request.session.get(SESSION_KEY_DUO_USER_ID)
        activation_code = self.request.session.get(SESSION_KEY_DUO_ACTIVATION_CODE)
        enroll_status = stage.client.enroll_status(user_id, activation_code)
        if enroll_status != "success":
            return HttpResponse(status=420)
        existing_device = DuoDevice.objects.filter(duo_user_id=user_id).first()
        self.request.session.pop(SESSION_KEY_DUO_USER_ID)
        self.request.session.pop(SESSION_KEY_DUO_ACTIVATION_CODE)
        if not existing_device:
            DuoDevice.objects.create(
                name="Duo Device",
                user=self.get_pending_user(),
                duo_user_id=user_id,
                stage=stage,
                last_t=now(),
            )
        else:
            return self.executor.stage_invalid("Device with Credential ID already exists.")
        return self.executor.stage_ok()

    def cleanup(self):
        self.request.session.pop(SESSION_KEY_DUO_USER_ID)
        self.request.session.pop(SESSION_KEY_DUO_ACTIVATION_CODE)
