"""Duo stage"""

from django.http import HttpResponse
from django.utils.timezone import now
from rest_framework.fields import CharField

from authentik.events.models import Event, EventAction
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallengeMixin,
)
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import InvalidStageError
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice

SESSION_KEY_DUO_ENROLL = "authentik/stages/authenticator_duo/enroll"


class AuthenticatorDuoChallenge(WithUserInfoChallengeMixin, Challenge):
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

    def duo_enroll(self):
        """Enroll User with Duo API and save results"""
        user = self.get_pending_user()
        stage: AuthenticatorDuoStage = self.executor.current_stage
        try:
            enroll = stage.auth_client().enroll(user.username)
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to enroll user: {str(exc)}",
                user=user,
            ).from_http(self.request, user)
            raise InvalidStageError(str(exc)) from exc
        self.request.session[SESSION_KEY_DUO_ENROLL] = enroll
        return enroll

    def get_challenge(self, *args, **kwargs) -> Challenge:
        stage: AuthenticatorDuoStage = self.executor.current_stage
        if SESSION_KEY_DUO_ENROLL not in self.request.session:
            self.duo_enroll()
        enroll = self.request.session[SESSION_KEY_DUO_ENROLL]
        return AuthenticatorDuoChallenge(
            data={
                "activation_barcode": enroll["activation_barcode"],
                "activation_code": enroll["activation_code"],
                "stage_uuid": str(stage.stage_uuid),
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        # Duo Challenge has already been validated
        stage: AuthenticatorDuoStage = self.executor.current_stage
        enroll = self.request.session.get(SESSION_KEY_DUO_ENROLL)
        enroll_status = stage.auth_client().enroll_status(
            enroll["user_id"], enroll["activation_code"]
        )
        if enroll_status != "success":
            return self.executor.stage_invalid(f"Invalid enrollment status: {enroll_status}.")
        existing_device = DuoDevice.objects.filter(duo_user_id=enroll["user_id"]).first()
        self.request.session.pop(SESSION_KEY_DUO_ENROLL)
        if not existing_device:
            DuoDevice.objects.create(
                name="Duo Authenticator",
                user=self.get_pending_user(),
                duo_user_id=enroll["user_id"],
                stage=stage,
                last_t=now(),
            )
        else:
            return self.executor.stage_invalid("Device with Credential ID already exists.")
        return self.executor.stage_ok()

    def cleanup(self):
        self.request.session.pop(SESSION_KEY_DUO_ENROLL, None)
