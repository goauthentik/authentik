"""oauth2 provider end_session Views"""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlanner
from authentik.flows.stage import SessionEndStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.policies.views import PolicyAccessView

LOGGER = get_logger()


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

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check for active logout flow before policy checks"""

        # First resolve the provider/application to ensure we have them for logging
        self.resolve_provider_application()

        # Check if we're already in an active logout flow (being called from iframe)
        if SESSION_KEY_PLAN in request.session:
            # We're being called from an iframe during an active logout flow
            # Just return a simple success response instead of starting a new flow
            LOGGER.debug(
                "OIDC end-session called during active logout flow, returning success",
                application=self.application.slug,
                has_active_plan=True,
            )
            # Return a minimal HTML page that won't break the iframe
            return HttpResponse(
                "<html><body>Logout successful</body></html>", content_type="text/html", status=200
            )

        # Otherwise, continue with normal policy checks
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the flow planner for the invalidation flow"""
        # Normal flow: start a new invalidation flow
        # (Active flow check is already done in dispatch())
        planner = FlowPlanner(self.flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(self.request, self.flow)
