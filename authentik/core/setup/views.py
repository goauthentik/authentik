from functools import lru_cache
from http import HTTPMethod, HTTPStatus

from django.contrib.staticfiles import finders
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django_tenants.utils import get_public_schema_name, schema_context
from structlog.stdlib import get_logger

from authentik.blueprints.models import BlueprintInstance
from authentik.core.apps import Setup
from authentik.flows.models import Flow, FlowAuthenticationRequirement, in_memory_stage
from authentik.flows.planner import FlowPlanner
from authentik.flows.stage import StageView
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant, normalize_base_url

LOGGER = get_logger()
FLOW_CONTEXT_START_BY = "goauthentik.io/core/setup/started-by"


@lru_cache
def read_static(path: str) -> str | None:
    result = finders.find(path)
    if not result:
        return None
    with open(result, encoding="utf8") as _file:
        return _file.read()


class SetupView(View):

    setup_flow_slug = "initial-setup"

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if request.method != HTTPMethod.HEAD and Setup.get():
            return redirect(reverse("authentik_core:root-redirect"))
        return super().dispatch(request, *args, **kwargs)

    def head(self, request: HttpRequest, *args, **kwargs):
        if Setup.get():
            return HttpResponse(status=HTTPStatus.SERVICE_UNAVAILABLE)
        if not Flow.objects.filter(slug=self.setup_flow_slug).exists():
            return HttpResponse(status=HTTPStatus.SERVICE_UNAVAILABLE)
        return HttpResponse(status=HTTPStatus.OK)

    def get(self, request: HttpRequest):
        flow = Flow.objects.filter(slug=self.setup_flow_slug).first()
        if not flow:
            LOGGER.info("Setup flow does not exist yet, waiting for worker to finish")
            return HttpResponse(
                read_static("dist/standalone/loading/startup.html"),
                status=HTTPStatus.SERVICE_UNAVAILABLE,
            )
        planner = FlowPlanner(flow)
        plan = planner.plan(request, {FLOW_CONTEXT_START_BY: "setup"})
        plan.append_stage(in_memory_stage(PostSetupStageView))
        return plan.to_redirect(request, flow)


class PostSetupStageView(StageView):
    """Run post-setup tasks"""

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Wrapper when this stage gets hit with a post request"""
        return self.get(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs):
        with transaction.atomic():
            # Persist the base_url captured during the setup flow onto the tenant
            base_url = normalize_base_url(
                (self.executor.plan.context.get(PLAN_CONTEXT_PROMPT) or {}).get("base_url")
            )
            if base_url:
                tenant = get_current_tenant()
                with schema_context(get_public_schema_name()):
                    Tenant.objects.filter(pk=tenant.pk).update(base_url=base_url)
            # Remember we're setup
            Setup.set(True)
            # Disable OOBE Blueprints
            BlueprintInstance.objects.filter(
                **{"metadata__labels__blueprints.goauthentik.io/system-oobe": "true"}
            ).update(enabled=False)
            # Make flow inaccessible
            Flow.objects.filter(slug="initial-setup").update(
                authentication=FlowAuthenticationRequirement.REQUIRE_SUPERUSER
            )
        return self.executor.stage_ok()
