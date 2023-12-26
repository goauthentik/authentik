"""RAC Views"""
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from authentik.core.models import Application
from authentik.core.views.interface import InterfaceView
from authentik.enterprise.policy import EnterprisePolicyAccessView
from authentik.enterprise.providers.rac.models import ConnectionToken, Endpoint, RACProvider
from authentik.flows.challenge import RedirectChallenge
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import FlowPlanner
from authentik.flows.stage import RedirectStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.policies.engine import PolicyEngine


class RACStartView(EnterprisePolicyAccessView):
    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["app"])
        self.endpoint = get_object_or_404(Endpoint, pk=self.kwargs["endpoint"])
        self.provider = self.application.provider

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(self.request)
        except FlowNonApplicableException:
            raise Http404
        plan.insert_stage(
            in_memory_stage(
                RACFinalStage,
                endpoint=self.endpoint,
                provider=self.provider,
                destination=self.request.build_absolute_uri(
                    reverse(
                        "authentik_providers_rac:if-rac",
                        kwargs={
                            "app": self.application.slug,
                            "endpoint": str(self.endpoint.pk),
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


class RACInterface(InterfaceView):
    """Start RAC connection"""

    template_name = "if/rac.html"


class RACFinalStage(RedirectStage):
    """RAC Connection final stage, set the connection token in the stage"""

    def get_challenge(self, *args, **kwargs) -> RedirectChallenge:
        endpoint: Endpoint = self.executor.current_stage.endpoint
        provider: RACProvider = self.executor.current_stage.provider
        engine = PolicyEngine(endpoint, self.request.user, self.request)
        engine.build()
        passing = engine.result
        if not passing.passing:
            return self.executor.stage_invalid(", ".join(passing.messages))
        ConnectionToken.objects.create(
            provider=provider,
            endpoint=endpoint,
        )
        return super().get_challenge(*args, **kwargs)
