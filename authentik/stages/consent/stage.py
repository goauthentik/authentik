"""authentik consent stage"""
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from rest_framework.fields import CharField

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    PermissionSerializer,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.templatetags.authentik_utils import avatar
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent

PLAN_CONTEXT_CONSENT_HEADER = "consent_header"
PLAN_CONTEXT_CONSENT_PERMISSIONS = "consent_permissions"


class ConsentChallenge(WithUserInfoChallenge):
    """Challenge info for consent screens"""

    header_text = CharField()
    permissions = PermissionSerializer(many=True)


class ConsentChallengeResponse(ChallengeResponse):
    """Consent challenge response, any valid response request is valid"""


class ConsentStageView(ChallengeStageView):
    """Simple consent checker."""

    response_class = ConsentChallengeResponse

    def get_challenge(self) -> Challenge:
        challenge = ConsentChallenge(
            data={
                "type": ChallengeTypes.native,
                "component": "ak-stage-consent",
            }
        )
        if PLAN_CONTEXT_CONSENT_HEADER in self.executor.plan.context:
            challenge.initial_data["header_text"] = self.executor.plan.context[
                PLAN_CONTEXT_CONSENT_HEADER
            ]
        if PLAN_CONTEXT_CONSENT_PERMISSIONS in self.executor.plan.context:
            challenge.initial_data["permissions"] = self.executor.plan.context[
                PLAN_CONTEXT_CONSENT_PERMISSIONS
            ]
        # If there's a pending user, update the `username` field
        # this field is only used by password managers.
        # If there's no user set, an error is raised later.
        if user := self.get_pending_user():
            challenge.initial_data["pending_user"] = user.username
            challenge.initial_data["pending_user_avatar"] = avatar(user)
        return challenge

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        current_stage: ConsentStage = self.executor.current_stage
        # For always require, we always return the challenge
        if current_stage.mode == ConsentMode.ALWAYS_REQUIRE:
            return super().get(request, *args, **kwargs)
        # at this point we need to check consent from database
        if PLAN_CONTEXT_APPLICATION not in self.executor.plan.context:
            # No application in this plan, hence we can't check DB and require user consent
            return super().get(request, *args, **kwargs)

        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]

        user = self.request.user
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]

        if UserConsent.filter_not_expired(user=user, application=application).exists():
            return self.executor.stage_ok()

        # No consent found, return consent
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        current_stage: ConsentStage = self.executor.current_stage
        if PLAN_CONTEXT_APPLICATION not in self.executor.plan.context:
            return self.executor.stage_ok()
        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        # Since we only get here when no consent exists, we can create it without update
        if current_stage.mode == ConsentMode.PERMANENT:
            UserConsent.objects.create(
                user=self.request.user, application=application, expiring=False
            )
        if current_stage.mode == ConsentMode.EXPIRING:
            UserConsent.objects.create(
                user=self.request.user,
                application=application,
                expires=now() + timedelta_from_string(current_stage.consent_expire_in),
            )
        return self.executor.stage_ok()
