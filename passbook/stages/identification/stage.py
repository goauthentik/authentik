"""Identification stage logic"""
from typing import List, Optional

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import reverse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog import get_logger

from passbook.core.models import Source, User
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import StageView
from passbook.flows.views import SESSION_KEY_APPLICATION_PRE
from passbook.stages.identification.forms import IdentificationForm
from passbook.stages.identification.models import IdentificationStage

LOGGER = get_logger()


class IdentificationStageView(FormView, StageView):
    """Form to identify the user"""

    form_class = IdentificationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["stage"] = self.executor.current_stage
        return kwargs

    def get_template_names(self) -> List[str]:
        current_stage: IdentificationStage = self.executor.current_stage
        return [current_stage.template]

    def get_context_data(self, **kwargs):
        current_stage: IdentificationStage = self.executor.current_stage
        # If the user has been redirected to us whilst trying to access an
        # application, SESSION_KEY_APPLICATION_PRE is set in the session
        if SESSION_KEY_APPLICATION_PRE in self.request.session:
            kwargs["application_pre"] = self.request.session[
                SESSION_KEY_APPLICATION_PRE
            ]
        # Check for related enrollment and recovery flow, add URL to view
        if current_stage.enrollment_flow:
            kwargs["enroll_url"] = reverse(
                "passbook_flows:flow-executor-shell",
                kwargs={"flow_slug": current_stage.enrollment_flow.slug},
            )
        if current_stage.recovery_flow:
            kwargs["recovery_url"] = reverse(
                "passbook_flows:flow-executor-shell",
                kwargs={"flow_slug": current_stage.recovery_flow.slug},
            )
        kwargs["primary_action"] = _("Log in")

        # Check all enabled source, add them if they have a UI Login button.
        kwargs["sources"] = []
        sources: List[Source] = (
            Source.objects.filter(enabled=True).order_by("name").select_subclasses()
        )
        for source in sources:
            ui_login_button = source.ui_login_button
            if ui_login_button:
                kwargs["sources"].append(ui_login_button)
        return super().get_context_data(**kwargs)

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

    def form_valid(self, form: IdentificationForm) -> HttpResponse:
        """Form data is valid"""
        pre_user = self.get_user(form.cleaned_data.get("uid_field"))
        if not pre_user:
            LOGGER.debug("invalid_login")
            messages.error(self.request, _("Failed to authenticate."))
            return self.form_invalid(form)
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = pre_user
        return self.executor.stage_ok()
