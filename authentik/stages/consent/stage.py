"""authentik consent stage"""
from typing import Optional

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
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent

PLAN_CONTEXT_CONSENT_TITLE = "consent_title"
PLAN_CONTEXT_CONSENT_HEADER = "consent_header"
PLAN_CONTEXT_CONSENT_PERMISSIONS = "consent_permissions"
PLAN_CONTEXT_CONSNET_EXTRA_PERMISSIONS = "consent_additional_permissions"


class ConsentChallenge(WithUserInfoChallenge):
    """Challenge info for consent screens"""

    header_text = CharField(required=False)
    permissions = PermissionSerializer(many=True)
    additional_permissions = PermissionSerializer(many=True)
    component = CharField(default="ak-stage-consent")


class ConsentChallengeResponse(ChallengeResponse):
    """Consent challenge response, any valid response request is valid"""

    component = CharField(default="ak-stage-consent")


class ConsentStageView(ChallengeStageView):
    """Simple consent checker."""

    response_class = ConsentChallengeResponse

    def get_challenge(self) -> Challenge:
        data = {
            "type": ChallengeTypes.NATIVE.value,
            "permissions": self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_PERMISSIONS, []),
            "additional_permissions": self.executor.plan.context.get(
                PLAN_CONTEXT_CONSNET_EXTRA_PERMISSIONS, []
            ),
        }
        if PLAN_CONTEXT_CONSENT_TITLE in self.executor.plan.context:
            data["title"] = self.executor.plan.context[PLAN_CONTEXT_CONSENT_TITLE]
        if PLAN_CONTEXT_CONSENT_HEADER in self.executor.plan.context:
            data["header_text"] = self.executor.plan.context[PLAN_CONTEXT_CONSENT_HEADER]
        challenge = ConsentChallenge(data=data)
        return challenge

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        current_stage: ConsentStage = self.executor.current_stage
        # Make this StageView work when injected, in which case `current_stage` is an instance
        # of the base class, and we don't save any consent, as it is assumed to be a one-time
        # prompt
        if not isinstance(current_stage, ConsentStage):
            return super().get(request, *args, **kwargs)
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

        consent: Optional[UserConsent] = UserConsent.filter_not_expired(
            user=user, application=application
        ).first()

        if consent:
            perms = self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_PERMISSIONS, [])
            allowed_perms = set(consent.permissions.split(" "))
            requested_perms = set(x["id"] for x in perms)

            if allowed_perms != requested_perms:
                self.executor.plan.context[PLAN_CONTEXT_CONSENT_PERMISSIONS] = [
                    x for x in perms if x["id"] in allowed_perms
                ]
                self.executor.plan.context[PLAN_CONTEXT_CONSNET_EXTRA_PERMISSIONS] = [
                    x for x in perms if x["id"] in requested_perms.difference(allowed_perms)
                ]
                return super().get(request, *args, **kwargs)
            return self.executor.stage_ok()

        # No consent found, return consent prompt
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        current_stage: ConsentStage = self.executor.current_stage
        if PLAN_CONTEXT_APPLICATION not in self.executor.plan.context:
            return self.executor.stage_ok()
        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        permissions = self.executor.plan.context.get(
            PLAN_CONTEXT_CONSENT_PERMISSIONS, []
        ) + self.executor.plan.context.get(PLAN_CONTEXT_CONSNET_EXTRA_PERMISSIONS, [])
        permissions_string = " ".join(x["id"] for x in permissions)
        # Make this StageView work when injected, in which case `current_stage` is an instance
        # of the base class, and we don't save any consent, as it is assumed to be a one-time
        # prompt
        if not isinstance(current_stage, ConsentStage):
            return self.executor.stage_ok()
        # Since we only get here when no consent exists, we can create it without update
        if current_stage.mode == ConsentMode.PERMANENT:
            UserConsent.objects.create(
                user=self.request.user,
                application=application,
                expiring=False,
                permissions=permissions_string,
            )
        if current_stage.mode == ConsentMode.EXPIRING:
            UserConsent.objects.create(
                user=self.request.user,
                application=application,
                expires=now() + timedelta_from_string(current_stage.consent_expire_in),
                permissions=permissions_string,
            )
        return self.executor.stage_ok()
