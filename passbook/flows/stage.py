"""passbook stage Base view"""
from typing import Any, Dict

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.views import FlowExecutorView


class StageView(TemplateView):
    """Abstract Stage, inherits TemplateView but can be combined with FormView"""

    template_name = "login/form_with_user.html"

    executor: FlowExecutorView

    request: HttpRequest = None

    def __init__(self, executor: FlowExecutorView):
        self.executor = executor

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs["title"] = self.executor.flow.name
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            kwargs["user"] = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        kwargs["primary_action"] = _("Continue")
        return super().get_context_data(**kwargs)
