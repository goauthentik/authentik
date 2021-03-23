"""authentik multi-stage authentication engine"""
from traceback import format_tb
from typing import Any, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import View
from drf_yasg2 import openapi
from drf_yasg2.utils import no_body, swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import USER_ATTRIBUTE_DEBUG
from authentik.events.models import cleanse_dict
from authentik.flows.challenge import (
    AccessDeniedChallenge,
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    HttpChallengeResponse,
    RedirectChallenge,
    ShellChallenge,
)
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.models import ConfigurableStage, Flow, FlowDesignation, Stage
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    FlowPlan,
    FlowPlanner,
)
from authentik.lib.utils.reflection import class_to_path
from authentik.lib.utils.urls import is_url_absolute, redirect_with_qs

LOGGER = get_logger()
# Argument used to redirect user after login
NEXT_ARG_NAME = "next"
SESSION_KEY_PLAN = "authentik_flows_plan"
SESSION_KEY_APPLICATION_PRE = "authentik_flows_application_pre"
SESSION_KEY_GET = "authentik_flows_get"


@method_decorator(xframe_options_sameorigin, name="dispatch")
class FlowExecutorView(APIView):
    """Stage 1 Flow executor, passing requests to Stage Views"""

    permission_classes = [AllowAny]

    flow: Flow

    plan: Optional[FlowPlan] = None
    current_stage: Stage
    current_stage_view: View

    _logger: BoundLogger

    def setup(self, request: HttpRequest, flow_slug: str):
        super().setup(request, flow_slug=flow_slug)
        self.flow = get_object_or_404(Flow.objects.select_related(), slug=flow_slug)
        self._logger = get_logger().bind(flow_slug=flow_slug)

    def handle_invalid_flow(self, exc: BaseException) -> HttpResponse:
        """When a flow is non-applicable check if user is on the correct domain"""
        if NEXT_ARG_NAME in self.request.GET:
            if not is_url_absolute(self.request.GET.get(NEXT_ARG_NAME)):
                self._logger.debug("f(exec): Redirecting to next on fail")
                return redirect(self.request.GET.get(NEXT_ARG_NAME))
        message = exc.__doc__ if exc.__doc__ else str(exc)
        return self.stage_invalid(error_message=message)

    # pylint: disable=unused-argument
    def dispatch(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        # Early check if theres an active Plan for the current session
        if SESSION_KEY_PLAN in self.request.session:
            self.plan = self.request.session[SESSION_KEY_PLAN]
            if self.plan.flow_pk != self.flow.pk.hex:
                self._logger.warning(
                    "f(exec): Found existing plan for other flow, deleteing plan",
                )
                # Existing plan is deleted from session and instance
                self.plan = None
                self.cancel()
            self._logger.debug("f(exec): Continuing existing plan")

        # Don't check session again as we've either already loaded the plan or we need to plan
        if not self.plan:
            self._logger.debug("f(exec): No active Plan found, initiating planner")
            try:
                self.plan = self._initiate_plan()
            except FlowNonApplicableException as exc:
                self._logger.warning(
                    "f(exec): Flow not applicable to current user", exc=exc
                )
                return to_stage_response(self.request, self.handle_invalid_flow(exc))
            except EmptyFlowException as exc:
                self._logger.warning("f(exec): Flow is empty", exc=exc)
                # To match behaviour with loading an empty flow plan from cache,
                # we don't show an error message here, but rather call _flow_done()
                return self._flow_done()
            # Initial flow request, check if we have an upstream query string passed in
            request.session[SESSION_KEY_GET] = QueryDict(request.GET.get("query", ""))
        # We don't save the Plan after getting the next stage
        # as it hasn't been successfully passed yet
        next_stage = self.plan.next(self.request)
        if not next_stage:
            self._logger.debug("f(exec): no more stages, flow is done.")
            return self._flow_done()
        self.current_stage = next_stage
        self._logger.debug(
            "f(exec): Current stage",
            current_stage=self.current_stage,
            flow_slug=self.flow.slug,
        )
        stage_cls = self.current_stage.type
        self.current_stage_view = stage_cls(self)
        self.current_stage_view.args = self.args
        self.current_stage_view.kwargs = self.kwargs
        self.current_stage_view.request = request
        return super().dispatch(request)

    @swagger_auto_schema(
        responses={
            200: Challenge(),
        },
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                required=True,
                description="Querystring as received",
                type=openapi.TYPE_STRING,
            )
        ],
        operation_id="flows_executor_get",
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Get the next pending challenge from the currently active flow."""
        self._logger.debug(
            "f(exec): Passing GET",
            view_class=class_to_path(self.current_stage_view.__class__),
            stage=self.current_stage,
        )
        try:
            stage_response = self.current_stage_view.get(request, *args, **kwargs)
            return to_stage_response(request, stage_response)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception(exc)
            return to_stage_response(request, FlowErrorResponse(request, exc))

    @swagger_auto_schema(
        responses={200: Challenge()},
        request_body=ChallengeResponse(),
        operation_id="flows_executor_solve",
    )
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Solve the previously retrieved challenge and advanced to the next stage."""
        self._logger.debug(
            "f(exec): Passing POST",
            view_class=class_to_path(self.current_stage_view.__class__),
            stage=self.current_stage,
        )
        try:
            stage_response = self.current_stage_view.post(request, *args, **kwargs)
            return to_stage_response(request, stage_response)
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception(exc)
            return to_stage_response(request, FlowErrorResponse(request, exc))

    def _initiate_plan(self) -> FlowPlan:
        planner = FlowPlanner(self.flow)
        plan = planner.plan(self.request)
        self.request.session[SESSION_KEY_PLAN] = plan
        return plan

    def _flow_done(self) -> HttpResponse:
        """User Successfully passed all stages"""
        # Since this is wrapped by the ExecutorShell, the next argument is saved in the session
        # extract the next param before cancel as that cleans it
        next_param = None
        if self.plan:
            next_param = self.plan.context.get(PLAN_CONTEXT_REDIRECT)
        if not next_param:
            next_param = self.request.session.get(SESSION_KEY_GET, {}).get(
                NEXT_ARG_NAME, "authentik_core:root-redirect"
            )
        self.cancel()
        return to_stage_response(self.request, redirect_with_qs(next_param))

    def stage_ok(self) -> HttpResponse:
        """Callback called by stages upon successful completion.
        Persists updated plan and context to session."""
        self._logger.debug(
            "f(exec): Stage ok",
            stage_class=class_to_path(self.current_stage_view.__class__),
        )
        self.plan.pop()
        self.request.session[SESSION_KEY_PLAN] = self.plan
        if self.plan.stages:
            self._logger.debug(
                "f(exec): Continuing with next stage",
                reamining=len(self.plan.stages),
            )
            kwargs = self.kwargs
            kwargs.update({"flow_slug": self.flow.slug})
            return redirect_with_qs(
                "authentik_api:flow-executor", self.request.GET, **kwargs
            )
        # User passed all stages
        self._logger.debug(
            "f(exec): User passed all stages",
            context=cleanse_dict(self.plan.context),
        )
        return self._flow_done()

    def stage_invalid(self, error_message: Optional[str] = None) -> HttpResponse:
        """Callback used stage when data is correct but a policy denies access
        or the user account is disabled.

        Optionally, an exception can be passed, which will be shown if the current user
        is a superuser."""
        self._logger.debug("f(exec): Stage invalid")
        self.cancel()
        response = HttpChallengeResponse(
            AccessDeniedChallenge(
                {
                    "error_message": error_message,
                    "title": self.flow.title,
                    "type": ChallengeTypes.native.value,
                    "component": "ak-stage-access-denied",
                }
            )
        )
        return to_stage_response(self.request, response)

    def cancel(self):
        """Cancel current execution and return a redirect"""
        keys_to_delete = [
            SESSION_KEY_APPLICATION_PRE,
            SESSION_KEY_PLAN,
            SESSION_KEY_GET,
        ]
        for key in keys_to_delete:
            if key in self.request.session:
                del self.request.session[key]


class FlowErrorResponse(TemplateResponse):
    """Response class when an unhandled error occurs during a stage. Normal users
    are shown an error message, superusers are shown a full stacktrace."""

    error: Exception

    def __init__(self, request: HttpRequest, error: Exception) -> None:
        # For some reason pyright complains about keyword argument usage here
        # pyright: reportGeneralTypeIssues=false
        super().__init__(request=request, template="flows/error.html")
        self.error = error

    def resolve_context(
        self, context: Optional[dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        if not context:
            context = {}
        context["error"] = self.error
        if self._request.user and self._request.user.is_authenticated:
            if self._request.user.is_superuser or self._request.user.attributes.get(
                USER_ATTRIBUTE_DEBUG, False
            ):
                context["tb"] = "".join(format_tb(self.error.__traceback__))
        return context


class CancelView(View):
    """View which canels the currently active plan"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """View which canels the currently active plan"""
        if SESSION_KEY_PLAN in request.session:
            del request.session[SESSION_KEY_PLAN]
            LOGGER.debug("Canceled current plan")
        return redirect("authentik_core:root-redirect")


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
            "authentik_core:if-flow", request.GET, flow_slug=flow.slug
        )


def to_stage_response(request: HttpRequest, source: HttpResponse) -> HttpResponse:
    """Convert normal HttpResponse into JSON Response"""
    if isinstance(source, HttpResponseRedirect) or source.status_code == 302:
        redirect_url = source["Location"]
        # Redirects to the same URL usually indicate an Error within a form
        if request.path == redirect_url:
            return source
        LOGGER.debug("converting to redirect challenge", to=str(redirect_url))
        return HttpChallengeResponse(
            RedirectChallenge(
                {"type": ChallengeTypes.redirect, "to": str(redirect_url)}
            )
        )
    if isinstance(source, TemplateResponse):
        return HttpChallengeResponse(
            ShellChallenge(
                {
                    "type": ChallengeTypes.shell,
                    "body": source.render().content.decode("utf-8"),
                }
            )
        )
    # Check for actual HttpResponse (without isinstance as we dont want to check inheritance)
    if source.__class__ == HttpResponse:
        return HttpChallengeResponse(
            ShellChallenge(
                {
                    "type": ChallengeTypes.shell,
                    "body": source.content.decode("utf-8"),
                }
            )
        )
    return source


class ConfigureFlowInitView(LoginRequiredMixin, View):
    """Initiate planner for selected change flow and redirect to flow executor,
    or raise Http404 if no configure_flow has been set."""

    def get(self, request: HttpRequest, stage_uuid: str) -> HttpResponse:
        """Initiate planner for selected change flow and redirect to flow executor,
        or raise Http404 if no configure_flow has been set."""
        try:
            stage: Stage = Stage.objects.get_subclass(pk=stage_uuid)
        except Stage.DoesNotExist as exc:
            raise Http404 from exc
        if not isinstance(stage, ConfigurableStage):
            LOGGER.debug("Stage does not inherit ConfigurableStage", stage=stage)
            raise Http404
        if not stage.configure_flow:
            LOGGER.debug("Stage has no configure_flow set", stage=stage)
            raise Http404

        plan = FlowPlanner(stage.configure_flow).plan(
            request, {PLAN_CONTEXT_PENDING_USER: request.user}
        )
        request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=stage.configure_flow.slug,
        )
