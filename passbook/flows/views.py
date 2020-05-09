"""passbook multi-stage authentication engine"""
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from structlog import get_logger

from passbook.core.views.utils import PermissionDeniedView
from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, FlowDesignation, Stage
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan, FlowPlanner
from passbook.lib.config import CONFIG
from passbook.lib.utils.reflection import class_to_path, path_to_class
from passbook.lib.utils.urls import is_url_absolute, redirect_with_qs
from passbook.lib.views import bad_request_message

LOGGER = get_logger()
# Argument used to redirect user after login
NEXT_ARG_NAME = "next"
SESSION_KEY_PLAN = "passbook_flows_plan"


class FlowExecutorView(View):
    """Stage 1 Flow executor, passing requests to Stage Views"""

    flow: Flow

    plan: Optional[FlowPlan] = None
    current_stage: Stage
    current_stage_view: View

    def setup(self, request: HttpRequest, flow_slug: str):
        super().setup(request, flow_slug=flow_slug)
        # TODO: Do we always need this?
        self.flow = get_object_or_404(Flow, slug=flow_slug)

    def _check_config_domain(self) -> Optional[HttpResponse]:
        """Checks if current request's domain matches configured Domain, and
        adds a warning if not."""
        current_domain = self.request.get_host()
        if ":" in current_domain:
            current_domain, _ = current_domain.split(":")
        config_domain = CONFIG.y("domain")
        if current_domain != config_domain:
            message = (
                f"Current domain of '{current_domain}' doesn't "
                f"match configured domain of '{config_domain}'."
            )
            LOGGER.warning(message, flow_slug=self.flow.slug)
            return bad_request_message(self.request, message)
        return None

    def handle_invalid_flow(self, exc: BaseException) -> HttpResponse:
        """When a flow is non-applicable check if user is on the correct domain"""
        if NEXT_ARG_NAME in self.request.GET:
            LOGGER.debug("Redirecting to next on fail")
            return redirect(self.request.GET.get(NEXT_ARG_NAME))
        incorrect_domain_message = self._check_config_domain()
        if incorrect_domain_message:
            return incorrect_domain_message
        return bad_request_message(self.request, str(exc))

    def dispatch(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        # Early check if theres an active Plan for the current session
        if SESSION_KEY_PLAN not in self.request.session:
            LOGGER.debug(
                "No active Plan found, initiating planner", flow_slug=flow_slug
            )
            try:
                self.plan = self._initiate_plan()
            except FlowNonApplicableException as exc:
                LOGGER.warning("Flow not applicable to current user", exc=exc)
                return self.handle_invalid_flow(exc)
            except EmptyFlowException as exc:
                LOGGER.warning("Flow is empty", exc=exc)
                return self.handle_invalid_flow(exc)
        else:
            LOGGER.debug("Continuing existing plan", flow_slug=flow_slug)
            self.plan = self.request.session[SESSION_KEY_PLAN]
        # We don't save the Plan after getting the next stage
        # as it hasn't been successfully passed yet
        self.current_stage = self.plan.next()
        LOGGER.debug(
            "Current stage", current_stage=self.current_stage, flow_slug=self.flow.slug,
        )
        stage_cls = path_to_class(self.current_stage.type)
        self.current_stage_view = stage_cls(self)
        self.current_stage_view.request = request
        return super().dispatch(request)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass get request to current stage"""
        LOGGER.debug(
            "Passing GET",
            view_class=class_to_path(self.current_stage_view.__class__),
            flow_slug=self.flow.slug,
        )
        return self.current_stage_view.get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass post request to current stage"""
        LOGGER.debug(
            "Passing POST",
            view_class=class_to_path(self.current_stage_view.__class__),
            flow_slug=self.flow.slug,
        )
        return self.current_stage_view.post(request, *args, **kwargs)

    def _initiate_plan(self) -> FlowPlan:
        planner = FlowPlanner(self.flow)
        plan = planner.plan(self.request)
        self.request.session[SESSION_KEY_PLAN] = plan
        return plan

    def _flow_done(self) -> HttpResponse:
        """User Successfully passed all stages"""
        self.cancel()
        next_param = self.request.GET.get(NEXT_ARG_NAME, None)
        if next_param and not is_url_absolute(next_param):
            return redirect(next_param)
        return redirect_with_qs("passbook_core:overview")

    def stage_ok(self) -> HttpResponse:
        """Callback called by stages upon successful completion.
        Persists updated plan and context to session."""
        LOGGER.debug(
            "Stage ok",
            stage_class=class_to_path(self.current_stage_view.__class__),
            flow_slug=self.flow.slug,
        )
        self.plan.stages.pop(0)
        self.request.session[SESSION_KEY_PLAN] = self.plan
        if self.plan.stages:
            LOGGER.debug(
                "Continuing with next stage",
                reamining=len(self.plan.stages),
                flow_slug=self.flow.slug,
            )
            return redirect_with_qs(
                "passbook_flows:flow-executor", self.request.GET, **self.kwargs
            )
        # User passed all stages
        LOGGER.debug(
            "User passed all stages",
            user=self.plan.context[PLAN_CONTEXT_PENDING_USER],
            flow_slug=self.flow.slug,
        )
        return self._flow_done()

    def stage_invalid(self) -> HttpResponse:
        """Callback used stage when data is correct but a policy denies access
        or the user account is disabled."""
        LOGGER.debug("User invalid", flow_slug=self.flow.slug)
        self.cancel()
        return redirect_with_qs("passbook_flows:denied", self.request.GET)

    def cancel(self):
        """Cancel current execution and return a redirect"""
        del self.request.session[SESSION_KEY_PLAN]


class FlowPermissionDeniedView(PermissionDeniedView):
    """User could not be authenticated"""


class ToDefaultFlow(View):
    """Redirect to default flow matching by designation"""

    designation: Optional[FlowDesignation] = None

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        flow = get_object_or_404(Flow, designation=self.designation)
        # TODO: Get Flow depending on subdomain?
        return redirect_with_qs(
            "passbook_flows:flow-executor", request.GET, flow_slug=flow.slug
        )
