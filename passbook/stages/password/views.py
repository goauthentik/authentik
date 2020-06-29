"""password stage views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.stages.password.models import PasswordStage


class ChangeFlowInitView(LoginRequiredMixin, View):
    """Initiate planner for selected change flow and redirect to flow executor,
    or raise Http404 if no change_flow has been set."""

    def get(self, request: HttpRequest, stage_uuid: str) -> HttpResponse:
        """Initiate planner for selected change flow and redirect to flow executor,
        or raise Http404 if no change_flow has been set."""
        stage: PasswordStage = get_object_or_404(PasswordStage, pk=stage_uuid)
        if not stage.change_flow:
            raise Http404

        plan = FlowPlanner(stage.change_flow).plan(
            request, {PLAN_CONTEXT_PENDING_USER: request.user}
        )
        request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=stage.change_flow.slug,
        )
