"""Identification stage logic"""
from typing import List, Optional

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from rest_framework.fields import CharField
from structlog.stdlib import get_logger

from authentik.core.models import Source, User
from authentik.core.types import UILoginButton
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import (
    PLAN_CONTEXT_PENDING_USER_IDENTIFIER,
    ChallengeStageView,
    StageView,
)
from authentik.flows.views import SESSION_KEY_APPLICATION_PRE
from authentik.stages.identification.forms import IdentificationForm
from authentik.stages.identification.models import IdentificationStage, UserFields

LOGGER = get_logger()


class IdentificationChallengeResponse(ChallengeResponse):

    uid_field = CharField()


class IdentificationStageView(ChallengeStageView):
    """Form to identify the user"""

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
        args = {"input_type": "text"}
        if current_stage.user_fields == [UserFields.E_MAIL]:
            args["input_type"] = "email"
        # If the user has been redirected to us whilst trying to access an
        # application, SESSION_KEY_APPLICATION_PRE is set in the session
        if SESSION_KEY_APPLICATION_PRE in self.request.session:
            args["application_pre"] = self.request.session[SESSION_KEY_APPLICATION_PRE]
        # Check for related enrollment and recovery flow, add URL to view
        if current_stage.enrollment_flow:
            args["enroll_url"] = reverse(
                "authentik_flows:flow-executor-shell",
                args={"flow_slug": current_stage.enrollment_flow.slug},
            )
        if current_stage.recovery_flow:
            args["recovery_url"] = reverse(
                "authentik_flows:flow-executor-shell",
                args={"flow_slug": current_stage.recovery_flow.slug},
            )
        args["primary_action"] = _("Log in")

        # Check all enabled source, add them if they have a UI Login button.
        args["sources"] = []
        sources: List[Source] = (
            Source.objects.filter(enabled=True).order_by("name").select_subclasses()
        )
        for source in sources:
            ui_login_button = source.ui_login_button
            if ui_login_button:
                args["sources"].append(ui_login_button)
        return Challenge(
            data={
                "type": ChallengeTypes.native,
                "component": "ak-stage-identification",
                "args": args,
            }
        )

    def challenge_valid(
        self, challenge: IdentificationChallengeResponse
    ) -> HttpResponse:
        user_identifier = challenge.data.get("uid_field")
        pre_user = self.get_user(user_identifier)
        if not pre_user:
            LOGGER.debug("invalid_login")
            messages.error(self.request, _("Failed to authenticate."))
            return self.challenge_invalid(challenge)
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = pre_user

        current_stage: IdentificationStage = self.executor.current_stage
        if not current_stage.show_matched_user:
            self.executor.plan.context[
                PLAN_CONTEXT_PENDING_USER_IDENTIFIER
            ] = user_identifier

        return self.executor.stage_ok()
