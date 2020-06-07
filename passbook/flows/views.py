"""passbook multi-stage authentication engine"""
from typing import Any, Dict, Optional

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, reverse
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import TemplateView, View
from structlog import get_logger

from passbook.core.views.utils import PermissionDeniedView
from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, FlowDesignation, Stage
from passbook.flows.planner import FlowPlan, FlowPlanner
from passbook.lib.utils.reflection import class_to_path, path_to_class
from passbook.lib.utils.urls import redirect_with_qs
from passbook.lib.views import bad_request_message

LOGGER = get_logger()
# Argument used to redirect user after login
NEXT_ARG_NAME = "next"
SESSION_KEY_PLAN = "passbook_flows_plan"


@method_decorator(xframe_options_sameorigin, name="dispatch")
class FlowExecutorView(View):
    """Stage 1 Flow executor, passing requests to Stage Views"""

    flow: Flow

    plan: Optional[FlowPlan] = None
    current_stage: Stage
    current_stage_view: View

    def setup(self, request: HttpRequest, flow_slug: str):
        super().setup(request, flow_slug=flow_slug)
        self.flow = get_object_or_404(Flow.objects.select_related(), slug=flow_slug)

    def handle_invalid_flow(self, exc: BaseException) -> HttpResponse:
        """When a flow is non-applicable check if user is on the correct domain"""
        if NEXT_ARG_NAME in self.request.GET:
            LOGGER.debug("f(exec): Redirecting to next on fail")
            return redirect(self.request.GET.get(NEXT_ARG_NAME))
        message = exc.__doc__ if exc.__doc__ else str(exc)
        return bad_request_message(self.request, message)

    def dispatch(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        # Early check if theres an active Plan for the current session
        if SESSION_KEY_PLAN in self.request.session:
            self.plan = self.request.session[SESSION_KEY_PLAN]
            if self.plan.flow_pk != self.flow.pk.hex:
                LOGGER.warning(
                    "f(exec): Found existing plan for other flow, deleteing plan",
                    flow_slug=flow_slug,
                )
                # Existing plan is deleted from session and instance
                self.plan = None
                self.cancel()
            LOGGER.debug("f(exec): Continuing existing plan", flow_slug=flow_slug)

        # Don't check session again as we've either already loaded the plan or we need to plan
        if not self.plan:
            LOGGER.debug(
                "f(exec): No active Plan found, initiating planner", flow_slug=flow_slug
            )
            try:
                self.plan = self._initiate_plan()
            except FlowNonApplicableException as exc:
                LOGGER.warning("f(exec): Flow not applicable to current user", exc=exc)
                return self.handle_invalid_flow(exc)
            except EmptyFlowException as exc:
                LOGGER.warning("f(exec): Flow is empty", exc=exc)
                return self.handle_invalid_flow(exc)
        # We don't save the Plan after getting the next stage
        # as it hasn't been successfully passed yet
        self.current_stage = self.plan.next()
        LOGGER.debug(
            "f(exec): Current stage",
            current_stage=self.current_stage,
            flow_slug=self.flow.slug,
        )
        stage_cls = path_to_class(self.current_stage.type)
        self.current_stage_view = stage_cls(self)
        self.current_stage_view.args = self.args
        self.current_stage_view.kwargs = self.kwargs
        self.current_stage_view.request = request
        return super().dispatch(request)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass get request to current stage"""
        LOGGER.debug(
            "f(exec): Passing GET",
            view_class=class_to_path(self.current_stage_view.__class__),
            flow_slug=self.flow.slug,
        )
        stage_response = self.current_stage_view.get(request, *args, **kwargs)
        return to_stage_response(request, stage_response)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass post request to current stage"""
        LOGGER.debug(
            "f(exec): Passing POST",
            view_class=class_to_path(self.current_stage_view.__class__),
            flow_slug=self.flow.slug,
        )
        stage_response = self.current_stage_view.post(request, *args, **kwargs)
        return to_stage_response(request, stage_response)

    def _initiate_plan(self) -> FlowPlan:
        planner = FlowPlanner(self.flow)
        plan = planner.plan(self.request)
        self.request.session[SESSION_KEY_PLAN] = plan
        return plan

    def _flow_done(self) -> HttpResponse:
        """User Successfully passed all stages"""
        self.cancel()
        next_param = self.request.GET.get(NEXT_ARG_NAME, "passbook_core:overview")
        return redirect_with_qs(next_param)

    def stage_ok(self) -> HttpResponse:
        """Callback called by stages upon successful completion.
        Persists updated plan and context to session."""
        LOGGER.debug(
            "f(exec): Stage ok",
            stage_class=class_to_path(self.current_stage_view.__class__),
            flow_slug=self.flow.slug,
        )
        self.plan.stages.pop(0)
        self.request.session[SESSION_KEY_PLAN] = self.plan
        if self.plan.stages:
            LOGGER.debug(
                "f(exec): Continuing with next stage",
                reamining=len(self.plan.stages),
                flow_slug=self.flow.slug,
            )
            return redirect_with_qs(
                "passbook_flows:flow-executor", self.request.GET, **self.kwargs
            )
        # User passed all stages
        LOGGER.debug(
            "f(exec): User passed all stages",
            flow_slug=self.flow.slug,
            context=self.plan.context,
        )
        return self._flow_done()

    def stage_invalid(self) -> HttpResponse:
        """Callback used stage when data is correct but a policy denies access
        or the user account is disabled."""
        LOGGER.debug("f(exec): Stage invalid", flow_slug=self.flow.slug)
        self.cancel()
        return redirect_with_qs("passbook_flows:denied", self.request.GET)

    def cancel(self):
        """Cancel current execution and return a redirect"""
        if SESSION_KEY_PLAN in self.request.session:
            del self.request.session[SESSION_KEY_PLAN]


class FlowPermissionDeniedView(PermissionDeniedView):
    """User could not be authenticated"""


class ToDefaultFlow(View):
    """Redirect to default flow matching by designation"""

    designation: Optional[FlowDesignation] = None

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        flow = Flow.with_policy(request, designation=self.designation)
        if not flow:
            raise Http404
        # If user already has a pending plan, clear it so we don't have to later.
        if SESSION_KEY_PLAN in self.request.session:
            plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
            if plan.flow_pk != flow.pk.hex:
                LOGGER.warning(
                    "f(def): Found existing plan for other flow, deleteing plan",
                    flow_slug=flow.slug,
                )
                del self.request.session[SESSION_KEY_PLAN]
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell", request.GET, flow_slug=flow.slug
        )


class FlowExecutorShellView(TemplateView):
    """Executor Shell view, loads a dummy card with a spinner
    that loads the next stage in the background."""

    template_name = "flows/shell.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        kwargs["exec_url"] = reverse("passbook_flows:flow-executor", kwargs=self.kwargs)
        kwargs["msg_url"] = reverse("passbook_api:messages-list")
        return kwargs


def to_stage_response(request: HttpRequest, source: HttpResponse) -> HttpResponse:
    """Convert normal HttpResponse into JSON Response"""
    if isinstance(source, HttpResponseRedirect) or source.status_code == 302:
        redirect_url = source["Location"]
        if request.path != redirect_url:
            return JsonResponse({"type": "redirect", "to": redirect_url})
        return source
    if isinstance(source, TemplateResponse):
        return JsonResponse(
            {"type": "template", "body": source.render().content.decode("utf-8")}
        )
    # Check for actual HttpResponse (without isinstance as we dont want to check inheritance)
    if source.__class__ == HttpResponse:
        return JsonResponse(
            {"type": "template", "body": source.content.decode("utf-8")}
        )
    return source
