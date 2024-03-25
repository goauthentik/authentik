"""oauth2 provider end_session Views"""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from authentik.core.models import Application
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlanner
from authentik.flows.stage import SessionEndStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.policies.views import PolicyAccessView


class EndSessionView(PolicyAccessView):
    """Redirect to application's provider's invalidation flow"""

    flow: Flow

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
        self.provider = self.application.get_provider()
        if not self.provider:
            raise Http404
        self.flow = self.provider.invalidation_flow or self.request.brand.flow_invalidation
        if not self.flow:
            raise Http404

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the flow planner for the invalidation flow"""
        planner = FlowPlanner(self.flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        plan.insert_stage(in_memory_stage(SessionEndStage))
        request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=self.flow.slug,
        )
