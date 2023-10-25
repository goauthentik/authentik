"""RAC Views"""
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from authentik.core.models import Application
from authentik.core.views.interface import InterfaceView
from authentik.enterprise.policy import EnterprisePolicyAccessView
from authentik.flows.challenge import RedirectChallenge
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import FlowPlanner
from authentik.flows.stage import RedirectStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.utils.urls import redirect_with_qs

CONNECTION_TOKEN = "ctoken"  # nosec


class RACInterface(EnterprisePolicyAccessView, InterfaceView):
    """Start RAC connection"""

    template_name = "if/rac.html"

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["app"])
        self.provider = self.application.provider

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        token = generate_id()
        if CONNECTION_TOKEN not in self.request.session:
            planner = FlowPlanner(self.provider.authorization_flow)
            planner.allow_empty_flows = True
            try:
                plan = planner.plan(self.request)
            except FlowNonApplicableException:
                raise Http404
            plan.insert_stage(
                in_memory_stage(
                    RACFinalStage,
                    token=token,
                    destination=self.request.build_absolute_uri(
                        reverse(
                            "authentik_enterprise_providers_rac:if-rac",
                            kwargs={
                                "app": self.application.slug,
                            },
                        )
                    ),
                )
            )
            request.session[SESSION_KEY_PLAN] = plan
            return redirect_with_qs(
                "authentik_core:if-flow",
                request.GET,
                flow_slug=self.provider.authorization_flow.slug,
            )
        return super().get(request, *args, **kwargs)


class RACFinalStage(RedirectStage):
    """RAC Connection final stage, set the connection token in the stage"""

    def get_challenge(self, *args, **kwargs) -> RedirectChallenge:
        self.request.session[CONNECTION_TOKEN] = self.executor.current_stage.token
        return super().get_challenge(*args, **kwargs)
