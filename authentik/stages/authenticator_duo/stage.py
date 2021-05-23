"""Duo stage"""
from django.http import HttpRequest, HttpResponse
from rest_framework.fields import CharField
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice

LOGGER = get_logger()

SESSION_KEY_DUO_USER_ID = "authentik_stages_authenticator_duo_user_id"
SESSION_KEY_DUO_ACTIVATION_CODE = "authentik_stages_authenticator_duo_activation_code"


class AuthenticatorDuoChallenge(WithUserInfoChallenge):
    """Duo Challenge"""

    activation_barcode = CharField()
    activation_code = CharField()
    stage_uuid = CharField()


class AuthenticatorDuoStageView(ChallengeStageView):
    """Duo stage"""

    def get_challenge(self, *args, **kwargs) -> Challenge:
        user = self.get_pending_user()
        stage: AuthenticatorDuoStage = self.executor.current_stage
        enroll = stage.client.enroll(user.username)
        user_id = enroll["user_id"]
        self.request.session[SESSION_KEY_DUO_USER_ID] = user_id
        self.request.session[SESSION_KEY_DUO_ACTIVATION_CODE] = enroll[
            "activation_code"
        ]
        return AuthenticatorDuoChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-stage-authenticator-duo",
                "activation_barcode": enroll["activation_barcode"],
                "activation_code": enroll["activation_code"],
                "stage_uuid": stage.stage_uuid,
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
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
                user=self.get_pending_user(), duo_user_id=user_id, stage=stage
            )
        else:
            return self.executor.stage_invalid(
                "Device with Credential ID already exists."
            )
        return self.executor.stage_ok()
