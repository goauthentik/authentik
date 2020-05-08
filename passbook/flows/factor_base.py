"""passbook multi-factor authentication engine"""
from typing import Any, Dict

from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.views import FlowExecutorView
from passbook.lib.config import CONFIG


class AuthenticationFactor(TemplateView):
    """Abstract Authentication factor, inherits TemplateView but can be combined with FormView"""

    form: ModelForm = None

    executor: FlowExecutorView

    request: HttpRequest = None
    template_name = "login/form_with_user.html"

    def __init__(self, executor: FlowExecutorView):
        self.executor = executor

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs["config"] = CONFIG.y("passbook")
        kwargs["title"] = _("Log in to your account")
        kwargs["primary_action"] = _("Log in")
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            kwargs["user"] = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return super().get_context_data(**kwargs)
