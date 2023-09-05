"""authentik consent stage"""
from typing import Optional
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.consent.models import ConsentMode, ConsentStage, UserConsent

PLAN_CONTEXT_CONSENT = "consent"
PLAN_CONTEXT_CONSENT_HEADER = "consent_header"
PLAN_CONTEXT_CONSENT_PERMISSIONS = "consent_permissions"
PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS = "consent_additional_permissions"
SESSION_KEY_CONSENT_TOKEN = "authentik/stages/consent/token"  # nosec


class ConsentPermissionSerializer(PassiveSerializer):
    """Permission used for consent"""

    name = CharField(allow_blank=True)
    id = CharField()


class ConsentChallenge(WithUserInfoChallenge):
    """Challenge info for consent screens"""

    header_text = CharField(required=False)
    permissions = ConsentPermissionSerializer(many=True)
    additional_permissions = ConsentPermissionSerializer(many=True)
    component = CharField(default="ak-stage-consent")
    token = CharField(required=True)


class ConsentChallengeResponse(ChallengeResponse):
    """Consent challenge response, any valid response request is valid"""

    component = CharField(default="ak-stage-consent")
    token = CharField(required=True)


class ConsentStageView(ChallengeStageView):
    """Simple consent checker."""

    response_class = ConsentChallengeResponse

    def get_challenge(self) -> Challenge:
        token = str(uuid4())
        self.request.session[SESSION_KEY_CONSENT_TOKEN] = token
        data = {
            "type": ChallengeTypes.NATIVE.value,
            "permissions": self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_PERMISSIONS, []),
            "additional_permissions": self.executor.plan.context.get(
                PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS, []
            ),
            "token": token,
        }
        if PLAN_CONTEXT_CONSENT_HEADER in self.executor.plan.context:
            data["header_text"] = self.executor.plan.context[PLAN_CONTEXT_CONSENT_HEADER]
        challenge = ConsentChallenge(data=data)
        return challenge

    def should_always_prompt(self) -> bool:
        """Check if the current request should require a prompt for non consent reasons,
        i.e. this stage injected from another stage, mode is always requireed or no application
        is set."""
        current_stage: ConsentStage = self.executor.current_stage
        # Make this StageView work when injected, in which case `current_stage` is an instance
        # of the base class, and we don't save any consent, as it is assumed to be a one-time
        # prompt
        if not isinstance(current_stage, ConsentStage):
            return True
        # For always require, we always return the challenge
        if current_stage.mode == ConsentMode.ALWAYS_REQUIRE:
            return True
        # at this point we need to check consent from database
        if PLAN_CONTEXT_APPLICATION not in self.executor.plan.context:
            # No application in this plan, hence we can't check DB and require user consent
            return True
        return None

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if self.should_always_prompt():
            return super().get(request, *args, **kwargs)
        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]

        user = self.request.user
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]

        consent: Optional[UserConsent] = UserConsent.filter_not_expired(
            user=user, application=application
        ).first()
        self.executor.plan.context[PLAN_CONTEXT_CONSENT] = consent

        if consent:
            perms = self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_PERMISSIONS, [])
            allowed_perms = set(consent.permissions.split(" ") if consent.permissions != "" else [])
            requested_perms = set(x["id"] for x in perms)

            if allowed_perms != requested_perms:
                self.executor.plan.context[PLAN_CONTEXT_CONSENT_PERMISSIONS] = [
                    x for x in perms if x["id"] in allowed_perms
                ]
                self.executor.plan.context[PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS] = [
                    x for x in perms if x["id"] in requested_perms.difference(allowed_perms)
                ]
                return super().get(request, *args, **kwargs)
            return self.executor.stage_ok()

        # No consent found, return consent prompt
        return super().get(request, *args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        if response.data["token"] != self.request.session[SESSION_KEY_CONSENT_TOKEN]:
            self.logger.info("Invalid consent token, re-showing prompt")
            return self.get(self.request)
        if self.should_always_prompt():
            return self.executor.stage_ok()
        current_stage: ConsentStage = self.executor.current_stage
        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        permissions = self.executor.plan.context.get(
            PLAN_CONTEXT_CONSENT_PERMISSIONS, []
        ) + self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS, [])
        permissions_string = " ".join(x["id"] for x in permissions)

        if not self.executor.plan.context.get(PLAN_CONTEXT_CONSENT, None):
            self.executor.plan.context[PLAN_CONTEXT_CONSENT] = UserConsent(
                user=self.request.user,
                application=application,
            )
        consent: UserConsent = self.executor.plan.context[PLAN_CONTEXT_CONSENT]
        consent.permissions = permissions_string
        if current_stage.mode == ConsentMode.PERMANENT:
            consent.expiring = False
        if current_stage.mode == ConsentMode.EXPIRING:
            consent.expires = now() + timedelta_from_string(current_stage.consent_expire_in)
        consent.save()
        return self.executor.stage_ok()
