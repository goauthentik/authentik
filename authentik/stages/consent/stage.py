"""authentik consent stage"""

from hmac import compare_digest
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.consent.models import ConsentClient, ConsentMode, ConsentStage, UserConsent

PLAN_CONTEXT_CONSENT = "consent"
PLAN_CONTEXT_CONSENT_HEADER = "consent_header"
PLAN_CONTEXT_CONSENT_PERMISSIONS = "consent_permissions"
PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS = "consent_additional_permissions"
PLAN_CONTEXT_CONSENT_TOKEN = "goauthentik.io/stages/consent/token"  # nosec
# Optional `ConsentClient`: consent is given to this client of the application instead of
# to the application itself
PLAN_CONTEXT_CONSENT_CLIENT = "goauthentik.io/stages/consent/client"


class ConsentPermissionSerializer(PassiveSerializer):
    """Permission used for consent"""

    name = CharField(allow_blank=True)
    id = CharField()


class ConsentChallenge(WithUserInfoChallenge):
    """Challenge info for consent screens"""

    header_text = CharField(required=False)
    # Only set when consent is given to a client of the application, see `ConsentClient`
    client_id = CharField(required=False)
    client_name = CharField(required=False)
    redirect_host = CharField(required=False)
    permissions = ConsentPermissionSerializer(many=True)
    additional_permissions = ConsentPermissionSerializer(many=True)
    component = CharField(default="ak-stage-consent")
    token = CharField(required=True)


class ConsentChallengeResponse(ChallengeResponse):
    """Consent challenge response, any valid response request is valid"""

    component = CharField(default="ak-stage-consent")
    token = CharField(required=True)

    def validate_token(self, token: str):
        if not compare_digest(
            token, self.stage.executor.plan.context.get(PLAN_CONTEXT_CONSENT_TOKEN, "")
        ):
            raise ValidationError(_("Invalid consent token, re-showing prompt"))
        return token


class ConsentStageView(ChallengeStageView):
    """Simple consent checker."""

    response_class = ConsentChallengeResponse

    def get_challenge(self) -> Challenge:
        token = str(uuid4())
        self.executor.plan.context[PLAN_CONTEXT_CONSENT_TOKEN] = token
        data = {
            "permissions": self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_PERMISSIONS, []),
            "additional_permissions": self.executor.plan.context.get(
                PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS, []
            ),
            "token": token,
        }
        if PLAN_CONTEXT_CONSENT_HEADER in self.executor.plan.context:
            data["header_text"] = self.executor.plan.context[PLAN_CONTEXT_CONSENT_HEADER]
        client = self.consent_client
        if client:
            for field, value in (
                ("client_id", client.client_id),
                ("client_name", client.name),
                ("redirect_host", client.redirect_host),
            ):
                if value is not None:
                    data[field] = value
        challenge = ConsentChallenge(data=data)
        return challenge

    @property
    def consent_client(self) -> ConsentClient | None:
        """Client consent is given to, None when consent is given to the application"""
        client = self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_CLIENT)
        if client is None:
            return None
        if not isinstance(client, ConsentClient):
            raise TypeError("Invalid consent client in plan context")
        return client

    def should_always_prompt(self) -> bool:
        """Check if the current request should require a prompt for non consent reasons,
        i.e. this stage injected from another stage, mode is always required or no application
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

        client = self.consent_client
        consent: UserConsent | None = next(
            (
                consent
                for consent in UserConsent.objects.filter(
                    UserConsent.given_to_q(client), user=user, application=application
                )
                if consent.is_given_to(client)
            ),
            None,
        )
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
        if self.should_always_prompt():
            return self.executor.stage_ok()
        current_stage: ConsentStage = self.executor.current_stage
        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        permissions = self.executor.plan.context.get(
            PLAN_CONTEXT_CONSENT_PERMISSIONS, []
        ) + self.executor.plan.context.get(PLAN_CONTEXT_CONSENT_EXTRA_PERMISSIONS, [])
        permissions_string = " ".join(x["id"] for x in permissions)

        client = self.consent_client
        consent: UserConsent | None = self.executor.plan.context.get(PLAN_CONTEXT_CONSENT, None)
        # Never update consent that was given to another client than the plan's
        if not consent or not consent.is_given_to(client):
            consent = UserConsent(
                user=self.request.user,
                application=application,
                client_id=client.client_id if client else None,
                resource=client.resource if client else None,
            )
            self.executor.plan.context[PLAN_CONTEXT_CONSENT] = consent
        consent.permissions = permissions_string
        if current_stage.mode == ConsentMode.PERMANENT:
            consent.expiring = False
        if current_stage.mode == ConsentMode.EXPIRING:
            consent.expires = now() + timedelta_from_string(current_stage.consent_expire_in)
        # Expired consents are hidden from the default manager but might not have been
        # cleaned up yet, in which case they'd conflict with the unique constraint
        UserConsent.objects.including_expired().filter(
            UserConsent.given_to_q(client),
            user=consent.user,
            application=application,
            expiring=True,
            expires__lt=now(),
        ).exclude(pk=consent.pk).delete()
        consent.save()
        return self.executor.stage_ok()
