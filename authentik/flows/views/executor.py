"""authentik multi-stage authentication engine"""
from copy import deepcopy
from typing import Optional

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import View
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, PolymorphicProxySerializer, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from sentry_sdk import capture_exception
from sentry_sdk.api import set_tag
from sentry_sdk.hub import Hub
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction, cleanse_dict
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    FlowErrorChallenge,
    HttpChallengeResponse,
    RedirectChallenge,
    ShellChallenge,
    WithUserInfoChallenge,
)
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.models import (
    ConfigurableStage,
    Flow,
    FlowDeniedAction,
    FlowDesignation,
    FlowStageBinding,
    FlowToken,
    Stage,
)
from authentik.flows.planner import (
    CACHE_PREFIX,
    PLAN_CONTEXT_IS_RESTORED,
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    FlowPlan,
    FlowPlanner,
)
from authentik.flows.stage import AccessDeniedChallengeView, StageView
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.reflection import all_subclasses, class_to_path
from authentik.lib.utils.urls import is_url_absolute, redirect_with_qs
from authentik.policies.engine import PolicyEngine
from authentik.tenants.models import Tenant

LOGGER = get_logger()
# Argument used to redirect user after login
NEXT_ARG_NAME = "next"
SESSION_KEY_PLAN = "authentik/flows/plan"
SESSION_KEY_APPLICATION_PRE = "authentik/flows/application_pre"
SESSION_KEY_GET = "authentik/flows/get"
SESSION_KEY_POST = "authentik/flows/post"
SESSION_KEY_HISTORY = "authentik/flows/history"
QS_KEY_TOKEN = "flow_token"  # nosec


def challenge_types():
    """This is a workaround for PolymorphicProxySerializer not accepting a callable for
    `serializers`. This function returns a class which is an iterator, which returns the
    subclasses of Challenge, and Challenge itself."""

    class Inner(dict):
        """dummy class with custom callback on .items()"""

        def items(self):
            mapping = {}
            classes = all_subclasses(Challenge)
            classes.remove(WithUserInfoChallenge)
            for cls in classes:
                mapping[cls().fields["component"].default] = cls
            return mapping.items()

    return Inner()


def challenge_response_types():
    """This is a workaround for PolymorphicProxySerializer not accepting a callable for
    `serializers`. This function returns a class which is an iterator, which returns the
    subclasses of Challenge, and Challenge itself."""

    class Inner(dict):
        """dummy class with custom callback on .items()"""

        def items(self):
            mapping = {}
            classes = all_subclasses(ChallengeResponse)
            for cls in classes:
                mapping[cls(stage=None).fields["component"].default] = cls
            return mapping.items()

    return Inner()


class InvalidStageError(SentryIgnoredException):
    """Error raised when a challenge from a stage is not valid"""


@method_decorator(xframe_options_sameorigin, name="dispatch")
class FlowExecutorView(APIView):
    """Flow executor, passing requests to Stage Views"""

    permission_classes = [AllowAny]

    flow: Flow

    plan: Optional[FlowPlan] = None
    current_binding: FlowStageBinding
    current_stage: Stage
    current_stage_view: View

    _logger: BoundLogger

    def setup(self, request: HttpRequest, flow_slug: str):
        super().setup(request, flow_slug=flow_slug)
        self.flow = get_object_or_404(Flow.objects.select_related(), slug=flow_slug)
        self._logger = get_logger().bind(flow_slug=flow_slug)
        set_tag("authentik.flow", self.flow.slug)

    def handle_invalid_flow(self, exc: FlowNonApplicableException) -> HttpResponse:
        """When a flow is non-applicable check if user is on the correct domain"""
        if self.flow.denied_action in [
            FlowDeniedAction.CONTINUE,
            FlowDeniedAction.MESSAGE_CONTINUE,
        ]:
            next_url = self.request.GET.get(NEXT_ARG_NAME)
            if next_url and not is_url_absolute(next_url):
                self._logger.debug("f(exec): Redirecting to next on fail")
                return to_stage_response(self.request, redirect(next_url))
        if self.flow.denied_action == FlowDeniedAction.CONTINUE:
            return to_stage_response(
                self.request, redirect(reverse("authentik_core:root-redirect"))
            )
        return to_stage_response(self.request, self.stage_invalid(error_message=exc.messages))

    def _check_flow_token(self, key: str) -> Optional[FlowPlan]:
        """Check if the user is using a flow token to restore a plan"""
        token: Optional[FlowToken] = FlowToken.filter_not_expired(key=key).first()
        if not token:
            return None
        plan = None
        try:
            plan = token.plan
        except (AttributeError, EOFError, ImportError, IndexError) as exc:
            LOGGER.warning("f(exec): Failed to restore token plan", exc=exc)
        finally:
            token.delete()
        if not isinstance(plan, FlowPlan):
            return None
        plan.context[PLAN_CONTEXT_IS_RESTORED] = token
        self._logger.debug("f(exec): restored flow plan from token", plan=plan)
        return plan

    # pylint: disable=too-many-return-statements
    def dispatch(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        with Hub.current.start_span(
            op="authentik.flow.executor.dispatch", description=self.flow.slug
        ) as span:
            span.set_data("authentik Flow", self.flow.slug)
            get_params = QueryDict(request.GET.get("query", ""))
            if QS_KEY_TOKEN in get_params:
                plan = self._check_flow_token(get_params[QS_KEY_TOKEN])
                if plan:
                    self.request.session[SESSION_KEY_PLAN] = plan
            # Early check if there's an active Plan for the current session
            if SESSION_KEY_PLAN in self.request.session:
                self.plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
                if self.plan.flow_pk != self.flow.pk.hex:
                    self._logger.warning(
                        "f(exec): Found existing plan for other flow, deleting plan",
                        other_flow=self.plan.flow_pk,
                    )
                    # Existing plan is deleted from session and instance
                    self.plan = None
                    self.cancel()
                self._logger.debug("f(exec): Continuing existing plan")

            # Don't check session again as we've either already loaded the plan or we need to plan
            if not self.plan:
                request.session[SESSION_KEY_HISTORY] = []
                self._logger.debug("f(exec): No active Plan found, initiating planner")
                try:
                    self.plan = self._initiate_plan()
                except FlowNonApplicableException as exc:
                    self._logger.warning("f(exec): Flow not applicable to current user", exc=exc)
                    return self.handle_invalid_flow(exc)
                except EmptyFlowException as exc:
                    self._logger.warning("f(exec): Flow is empty", exc=exc)
                    # To match behaviour with loading an empty flow plan from cache,
                    # we don't show an error message here, but rather call _flow_done()
                    return self._flow_done()
            # Initial flow request, check if we have an upstream query string passed in
            request.session[SESSION_KEY_GET] = get_params
            # We don't save the Plan after getting the next stage
            # as it hasn't been successfully passed yet
            try:
                # This is the first time we actually access any attribute on the selected plan
                # if the cached plan is from an older version, it might have different attributes
                # in which case we just delete the plan and invalidate everything
                next_binding = self.plan.next(self.request)
            except Exception as exc:  # pylint: disable=broad-except
                self._logger.warning(
                    "f(exec): found incompatible flow plan, invalidating run", exc=exc
                )
                keys = cache.keys(f"{CACHE_PREFIX}*")
                cache.delete_many(keys)
                return self.stage_invalid()
            if not next_binding:
                self._logger.debug("f(exec): no more stages, flow is done.")
                return self._flow_done()
            self.current_binding = next_binding
            self.current_stage = next_binding.stage
            self._logger.debug(
                "f(exec): Current stage",
                current_stage=self.current_stage,
                flow_slug=self.flow.slug,
            )
            try:
                stage_cls = self.current_stage.type
            except NotImplementedError as exc:
                self._logger.debug("Error getting stage type", exc=exc)
                return self.stage_invalid()
            self.current_stage_view = stage_cls(self)
            self.current_stage_view.args = self.args
            self.current_stage_view.kwargs = self.kwargs
            self.current_stage_view.request = request
            try:
                return super().dispatch(request)
            except InvalidStageError as exc:
                return self.stage_invalid(str(exc))

    def handle_exception(self, exc: Exception) -> HttpResponse:
        """Handle exception in stage execution"""
        if settings.DEBUG or settings.TEST:
            raise exc
        capture_exception(exc)
        self._logger.warning(exc)
        Event.new(
            action=EventAction.SYSTEM_EXCEPTION,
            message=exception_to_string(exc),
        ).from_http(self.request)
        challenge = FlowErrorChallenge(self.request, exc)
        challenge.is_valid(raise_exception=True)
        return to_stage_response(self.request, HttpChallengeResponse(challenge))

    @extend_schema(
        responses={
            200: PolymorphicProxySerializer(
                component_name="ChallengeTypes",
                serializers=challenge_types(),
                resource_type_field_name="component",
            ),
        },
        request=OpenApiTypes.NONE,
        parameters=[
            OpenApiParameter(
                name="query",
                location=OpenApiParameter.QUERY,
                required=True,
                description="Querystring as received",
                type=OpenApiTypes.STR,
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
            with Hub.current.start_span(
                op="authentik.flow.executor.stage",
                description=class_to_path(self.current_stage_view.__class__),
            ) as span:
                span.set_data("Method", "GET")
                span.set_data("authentik Stage", self.current_stage_view)
                span.set_data("authentik Flow", self.flow.slug)
                stage_response = self.current_stage_view.get(request, *args, **kwargs)
                return to_stage_response(request, stage_response)
        except Exception as exc:  # pylint: disable=broad-except
            return self.handle_exception(exc)

    @extend_schema(
        responses={
            200: PolymorphicProxySerializer(
                component_name="ChallengeTypes",
                serializers=challenge_types(),
                resource_type_field_name="component",
            ),
        },
        request=PolymorphicProxySerializer(
            component_name="FlowChallengeResponse",
            serializers=challenge_response_types(),
            resource_type_field_name="component",
        ),
        parameters=[
            OpenApiParameter(
                name="query",
                location=OpenApiParameter.QUERY,
                required=True,
                description="Querystring as received",
                type=OpenApiTypes.STR,
            )
        ],
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
            with Hub.current.start_span(
                op="authentik.flow.executor.stage",
                description=class_to_path(self.current_stage_view.__class__),
            ) as span:
                span.set_data("Method", "POST")
                span.set_data("authentik Stage", self.current_stage_view)
                span.set_data("authentik Flow", self.flow.slug)
                stage_response = self.current_stage_view.post(request, *args, **kwargs)
                return to_stage_response(request, stage_response)
        except Exception as exc:  # pylint: disable=broad-except
            return self.handle_exception(exc)

    def _initiate_plan(self) -> FlowPlan:
        planner = FlowPlanner(self.flow)
        plan = planner.plan(self.request)
        self.request.session[SESSION_KEY_PLAN] = plan
        try:
            # Call the has_stages getter to check that
            # there are no issues with the class we might've gotten
            # from the cache. If there are errors, just delete all cached flows
            _ = plan.has_stages
        except Exception:  # pylint: disable=broad-except
            keys = cache.keys(f"{CACHE_PREFIX}*")
            cache.delete_many(keys)
            return self._initiate_plan()
        return plan

    def restart_flow(self, keep_context=False) -> HttpResponse:
        """Restart the currently active flow, optionally keeping the current context"""
        planner = FlowPlanner(self.flow)
        default_context = None
        if keep_context:
            default_context = self.plan.context
        plan = planner.plan(self.request, default_context)
        self.request.session[SESSION_KEY_PLAN] = plan
        kwargs = self.kwargs
        kwargs.update({"flow_slug": self.flow.slug})
        return redirect_with_qs("authentik_api:flow-executor", self.request.GET, **kwargs)

    def _flow_done(self) -> HttpResponse:
        """User Successfully passed all stages"""
        # Since this is wrapped by the ExecutorShell, the next argument is saved in the session
        # extract the next param before cancel as that cleans it
        if self.plan and PLAN_CONTEXT_REDIRECT in self.plan.context:
            # The context `redirect` variable can only be set by
            # an expression policy or authentik itself, so we don't
            # check if its an absolute URL or a relative one
            self.cancel()
            return to_stage_response(
                self.request, redirect(self.plan.context.get(PLAN_CONTEXT_REDIRECT))
            )
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
        if isinstance(self.current_stage_view, StageView):
            self.current_stage_view.cleanup()
        self.request.session.get(SESSION_KEY_HISTORY, []).append(deepcopy(self.plan))
        self.plan.pop()
        self.request.session[SESSION_KEY_PLAN] = self.plan
        if self.plan.bindings:
            self._logger.debug(
                "f(exec): Continuing with next stage",
                remaining=len(self.plan.bindings),
            )
            kwargs = self.kwargs
            kwargs.update({"flow_slug": self.flow.slug})
            return redirect_with_qs("authentik_api:flow-executor", self.request.GET, **kwargs)
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
        challenge_view = AccessDeniedChallengeView(self, error_message)
        challenge_view.request = self.request
        return to_stage_response(self.request, challenge_view.get(self.request))

    def cancel(self):
        """Cancel current execution and return a redirect"""
        keys_to_delete = [
            SESSION_KEY_APPLICATION_PRE,
            SESSION_KEY_PLAN,
            SESSION_KEY_GET,
            # We might need the initial POST payloads for later requests
            # SESSION_KEY_POST,
            # We don't delete the history on purpose, as a user might
            # still be inspecting it.
            # It's only deleted on a fresh executions
            # SESSION_KEY_HISTORY,
        ]
        self._logger.debug("f(exec): cleaning up")
        for key in keys_to_delete:
            if key in self.request.session:
                del self.request.session[key]


class CancelView(View):
    """View which canels the currently active plan"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """View which canels the currently active plan"""
        if SESSION_KEY_PLAN in request.session:
            del request.session[SESSION_KEY_PLAN]
            LOGGER.debug("Canceled current plan")
        return redirect("authentik_flows:default-invalidation")


class ToDefaultFlow(View):
    """Redirect to default flow matching by designation"""

    designation: Optional[FlowDesignation] = None

    def flow_by_policy(self, request: HttpRequest, **flow_filter) -> Optional[Flow]:
        """Get a Flow by `**flow_filter` and check if the request from `request` can access it."""
        flows = Flow.objects.filter(**flow_filter).order_by("slug")
        for flow in flows:
            engine = PolicyEngine(flow, request.user, request)
            engine.build()
            result = engine.result
            if result.passing:
                LOGGER.debug("flow_by_policy: flow passing", flow=flow)
                return flow
            LOGGER.warning("flow_by_policy: flow not passing", flow=flow, messages=result.messages)
        LOGGER.debug("flow_by_policy: no flow found", filters=flow_filter)
        return None

    def get_flow(self) -> Flow:
        """Get a flow for the selected designation"""
        tenant: Tenant = self.request.tenant
        flow = None
        # First, attempt to get default flow from tenant
        if self.designation == FlowDesignation.AUTHENTICATION:
            flow = tenant.flow_authentication
            # Check if we have a default flow from application
            application: Optional[Application] = self.request.session.get(
                SESSION_KEY_APPLICATION_PRE
            )
            if application and application.provider and application.provider.authentication_flow:
                flow = application.provider.authentication_flow
        elif self.designation == FlowDesignation.INVALIDATION:
            flow = tenant.flow_invalidation
        if flow:
            return flow
        # If no flow was set, get the first based on slug and policy
        flow = self.flow_by_policy(self.request, designation=self.designation)
        if flow:
            return flow
        # If we still don't have a flow, 404
        raise Http404

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        flow = self.get_flow()
        # If user already has a pending plan, clear it so we don't have to later.
        if SESSION_KEY_PLAN in self.request.session:
            plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
            if plan.flow_pk != flow.pk.hex:
                LOGGER.warning(
                    "f(def): Found existing plan for other flow, deleting plan",
                    flow_slug=flow.slug,
                )
                del self.request.session[SESSION_KEY_PLAN]
        return redirect_with_qs("authentik_core:if-flow", request.GET, flow_slug=flow.slug)


def to_stage_response(request: HttpRequest, source: HttpResponse) -> HttpResponse:
    """Convert normal HttpResponse into JSON Response"""
    if isinstance(source, HttpResponseRedirect) or source.status_code == 302:
        redirect_url = source["Location"]
        # Redirects to the same URL usually indicate an Error within a form
        if request.get_full_path() == redirect_url:
            return source
        LOGGER.debug(
            "converting to redirect challenge",
            to=str(redirect_url),
            current=request.path,
        )
        return HttpChallengeResponse(
            RedirectChallenge(
                {
                    "type": ChallengeTypes.REDIRECT,
                    "to": str(redirect_url),
                }
            )
        )
    if isinstance(source, TemplateResponse):
        return HttpChallengeResponse(
            ShellChallenge(
                {
                    "type": ChallengeTypes.SHELL,
                    "body": source.render().content.decode("utf-8"),
                }
            )
        )
    # Check for actual HttpResponse (without isinstance as we don't want to check inheritance)
    if source.__class__ == HttpResponse:
        return HttpChallengeResponse(
            ShellChallenge(
                {
                    "type": ChallengeTypes.SHELL,
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

        try:
            plan = FlowPlanner(stage.configure_flow).plan(
                request, {PLAN_CONTEXT_PENDING_USER: request.user}
            )
        except FlowNonApplicableException:
            LOGGER.warning("Flow not applicable to user")
            raise Http404
        request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=stage.configure_flow.slug,
        )
