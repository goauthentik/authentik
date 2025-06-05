"""RAC Views"""

from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext as _

from authentik.core.models import Application
from authentik.core.views.interface import InterfaceView
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import RedirectChallenge
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlanner
from authentik.flows.stage import RedirectStage
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.policies.views import PolicyAccessView
from authentik.providers.rac.models import ConnectionToken, Endpoint, RACProvider


class RACStartView(PolicyAccessView):
    """Start a RAC connection by checking access and creating a connection token"""

    endpoint: Endpoint

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["app"])
        # Endpoint permissions are validated in the RACFinalStage below
        self.endpoint = get_object_or_404(Endpoint, pk=self.kwargs["endpoint"])
        self.provider = RACProvider.objects.get(application=self.application)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Start flow planner for RAC provider"""
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                self.request,
                {
                    PLAN_CONTEXT_APPLICATION: self.application,
                },
            )
        except FlowNonApplicableException:
            raise Http404 from None
        plan.append_stage(
            in_memory_stage(
                RACFinalStage,
                application=self.application,
                endpoint=self.endpoint,
                provider=self.provider,
            )
        )
        return plan.to_redirect(request, self.provider.authorization_flow)


class RACInterface(InterfaceView):
    """Start RAC connection"""

    template_name = "if/rac.html"
    token: ConnectionToken

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Early sanity check to ensure token still exists
        token = ConnectionToken.filter_not_expired(token=self.kwargs["token"]).first()
        if not token:
            return redirect("authentik_core:if-user")
        self.token = token
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["token"] = self.token
        return super().get_context_data(**kwargs)


class RACFinalStage(RedirectStage):
    """RAC Connection final stage, set the connection token in the stage"""

    endpoint: Endpoint
    provider: RACProvider
    application: Application

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.endpoint = self.executor.current_stage.endpoint
        self.provider = self.executor.current_stage.provider
        self.application = self.executor.current_stage.application
        # Check policies bound to endpoint directly
        engine = PolicyEngine(self.endpoint, self.request.user, self.request)
        engine.use_cache = False
        engine.build()
        passing = engine.result
        if not passing.passing:
            return self.executor.stage_invalid(", ".join(passing.messages))
        # Check if we're already at the maximum connection limit
        all_tokens = ConnectionToken.filter_not_expired(
            endpoint=self.endpoint,
        )
        if self.endpoint.maximum_connections > -1:
            if all_tokens.count() >= self.endpoint.maximum_connections:
                msg = [_("Maximum connection limit reached.")]
                # Check if any other tokens exist for the current user, and inform them
                # they are already connected
                if all_tokens.filter(session__user=self.request.user).exists():
                    msg.append(_("(You are already connected in another tab/window)"))
                return self.executor.stage_invalid(" ".join(msg))
        return super().dispatch(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs) -> RedirectChallenge:
        token = ConnectionToken.objects.create(
            provider=self.provider,
            endpoint=self.endpoint,
            settings=self.executor.plan.context.get("connection_settings", {}),
            session=self.request.session["authenticatedsession"],
            expires=now() + timedelta_from_string(self.provider.connection_expiry),
            expiring=True,
        )
        Event.new(
            EventAction.AUTHORIZE_APPLICATION,
            authorized_application=self.application,
            flow=self.executor.plan.flow_pk,
            endpoint=self.endpoint.name,
        ).from_http(self.request)
        self.executor.current_stage.destination = self.request.build_absolute_uri(
            reverse("authentik_providers_rac:if-rac", kwargs={"token": str(token.token)})
        )
        return super().get_challenge(*args, **kwargs)
