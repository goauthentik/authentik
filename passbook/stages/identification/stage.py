"""Identification stage logic"""
from typing import List, Optional

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog import get_logger

from passbook.core.models import Source, User
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import AuthenticationStage
from passbook.lib.config import CONFIG
from passbook.stages.identification.forms import IdentificationForm
from passbook.stages.identification.models import IdentificationStage

LOGGER = get_logger()


class IdentificationStageView(FormView, AuthenticationStage):
    """Form to identify the user"""

    form_class = IdentificationForm

    def get_template_names(self) -> List[str]:
        current_stage: IdentificationStage = self.executor.current_stage
        return [current_stage.template]

    def get_context_data(self, **kwargs):
        kwargs["config"] = CONFIG.y("passbook")
        kwargs["title"] = _("Log in to your account")
        kwargs["primary_action"] = _("Log in")
        # TODO: show this based on the existence of an enrollment flow
        kwargs["show_sign_up_notice"] = CONFIG.y("passbook.sign_up.enabled")
        kwargs["sources"] = []
        sources = (
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
            query |= Q(**{search_field: uid_value})
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
            return self.executor.stage_invalid()
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = pre_user
        return self.executor.stage_ok()
