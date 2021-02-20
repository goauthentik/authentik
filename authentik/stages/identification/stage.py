"""Identification stage logic"""
from dataclasses import asdict
from typing import Optional

from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.core.api.applications import ApplicationSerializer
from authentik.core.models import Source, User
from authentik.core.types import UILoginButtonSerializer
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import (
    PLAN_CONTEXT_PENDING_USER_IDENTIFIER,
    ChallengeStageView,
)
from authentik.flows.views import SESSION_KEY_APPLICATION_PRE
from authentik.stages.identification.models import IdentificationStage, UserFields

LOGGER = get_logger()


class IdentificationChallenge(Challenge):
    """Identification challenges with all UI elements"""

    input_type = CharField()
    application_pre = ApplicationSerializer(required=False)

    enroll_url = CharField(required=False)
    recovery_url = CharField(required=False)
    primary_action = CharField()
    sources = UILoginButtonSerializer(many=True, required=False)


class IdentificationChallengeResponse(ChallengeResponse):
    """Identification challenge"""

    uid_field = CharField()
    pre_user: Optional[User] = None

    def validate_uid_field(self, value: str) -> str:
        """Validate that user exists"""
        pre_user = self.stage.get_user(value)
        if not pre_user:
            LOGGER.debug("invalid_login", identifier=value)
            raise ValidationError("Failed to authenticate.")
        self.pre_user = pre_user
        return value


class IdentificationStageView(ChallengeStageView):
    """Form to identify the user"""

    response_class = IdentificationChallengeResponse

    def get_user(self, uid_value: str) -> Optional[User]:
        """Find user instance. Returns None if no user was found."""
        current_stage: IdentificationStage = self.executor.current_stage
        query = Q()
        for search_field in current_stage.user_fields:
            model_field = search_field
            if current_stage.case_insensitive_matching:
                model_field += "__iexact"
            else:
                model_field += "__exact"
            query |= Q(**{model_field: uid_value})
        users = User.objects.filter(query)
        if users.exists():
            LOGGER.debug("Found user", user=users.first(), query=query)
            return users.first()
        return None

    def get_challenge(self) -> Challenge:
        current_stage: IdentificationStage = self.executor.current_stage
        challenge = IdentificationChallenge(
            data={
                "type": ChallengeTypes.native,
                "component": "ak-stage-identification",
                "primary_action": _("Log in"),
                "input_type": "text",
            }
        )
        if current_stage.user_fields == [UserFields.E_MAIL]:
            challenge.initial_data["input_type"] = "email"
        # If the user has been redirected to us whilst trying to access an
        # application, SESSION_KEY_APPLICATION_PRE is set in the session
        if SESSION_KEY_APPLICATION_PRE in self.request.session:
            challenge.initial_data["application_pre"] = self.request.session[
                SESSION_KEY_APPLICATION_PRE
            ]
        # Check for related enrollment and recovery flow, add URL to view
        if current_stage.enrollment_flow:
            challenge.initial_data["enroll_url"] = reverse(
                "authentik_flows:flow-executor-shell",
                kwargs={"flow_slug": current_stage.enrollment_flow.slug},
            )
        if current_stage.recovery_flow:
            challenge.initial_data["recovery_url"] = reverse(
                "authentik_flows:flow-executor-shell",
                kwargs={"flow_slug": current_stage.recovery_flow.slug},
            )

        # Check all enabled source, add them if they have a UI Login button.
        ui_sources = []
        sources: list[Source] = (
            Source.objects.filter(enabled=True).order_by("name").select_subclasses()
        )
        for source in sources:
            ui_login_button = source.ui_login_button
            if ui_login_button:
                ui_sources.append(asdict(ui_login_button))
        challenge.initial_data["sources"] = ui_sources
        return challenge

    def challenge_valid(
        self, response: IdentificationChallengeResponse
    ) -> HttpResponse:
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = response.pre_user
        current_stage: IdentificationStage = self.executor.current_stage
        if not current_stage.show_matched_user:
            self.executor.plan.context[
                PLAN_CONTEXT_PENDING_USER_IDENTIFIER
            ] = response.validated_data.get("uid_field")
        return self.executor.stage_ok()
