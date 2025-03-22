"""authentik access helper classes"""

from json import dumps
from typing import Any
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView, View
from structlog.stdlib import get_logger

from authentik.core.models import Application, Provider, User
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import (
    SESSION_KEY_APPLICATION_PRE,
    SESSION_KEY_PLAN,
    SESSION_KEY_POST,
)
from authentik.lib.sentry import SentryIgnoredException
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
QS_BUFFER_ID = "af_bf_id"
QS_SKIP_BUFFER = "skip_buffer"
SESSION_KEY_BUFFER = "authentik/policies/pav_buffer/%s"


class RequestValidationError(SentryIgnoredException):
    """Error raised in pre_permission_check, when a request is invalid."""

    response: HttpResponse | None

    def __init__(self, response: HttpResponse | None = None):
        super().__init__()
        if response:
            self.response = response


class BaseMixin:
    """Base Mixin class, used to annotate View Member variables"""

    request: HttpRequest


class PolicyAccessView(AccessMixin, View):
    """Mixin class for usage in Authorization views.
    Provider functions to check application access, etc"""

    provider: Provider
    application: Application

    def pre_permission_check(self):
        """Optionally hook in before permission check to check if a request is valid.
        Can raise `RequestValidationError` to return a response."""

    def resolve_provider_application(self):
        """Resolve self.provider and self.application. *.DoesNotExist Exceptions cause a normal
        AccessDenied view to be shown. An Http404 exception
        is not caught, and will return directly"""
        raise NotImplementedError

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            self.pre_permission_check()
        except RequestValidationError as exc:
            if exc.response:
                return exc.response
            return self.handle_no_permission()
        try:
            self.resolve_provider_application()
        except (Application.DoesNotExist, Provider.DoesNotExist) as exc:
            LOGGER.warning("failed to resolve application", exc=exc)
            return self.handle_no_permission_authenticated(
                PolicyResult(False, _("Failed to resolve application"))
            )
        # Check if user is unauthenticated, so we pass the application
        # for the identification stage
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        # Check permissions
        result = self.user_has_access()
        if not result.passing:
            return self.handle_no_permission_authenticated(result)
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self) -> HttpResponse:
        """User has no access and is not authenticated, so we remember the application
        they try to access and redirect to the login URL. The application is saved to show
        a hint on the Identification Stage what the user should login for."""
        if self.application:
            self.request.session[SESSION_KEY_APPLICATION_PRE] = self.application
        # Because this view might get hit with a POST request, we need to preserve that data
        # since later views might need it (mostly SAML)
        if self.request.method.lower() == "post":
            self.request.session[SESSION_KEY_POST] = self.request.POST
        return redirect_to_login(
            self.request.get_full_path(),
            self.get_login_url(),
            self.get_redirect_field_name(),
        )

    def handle_no_permission_authenticated(
        self, result: PolicyResult | None = None
    ) -> HttpResponse:
        """Function called when user has no permissions but is authenticated"""
        response = AccessDeniedResponse(self.request)
        if result:
            response.policy_result = result
        return response

    def modify_policy_request(self, request: PolicyRequest) -> PolicyRequest:
        """optionally modify the policy request"""
        return request

    def user_has_access(self, user: User | None = None) -> PolicyResult:
        """Check if user has access to application."""
        user = user or self.request.user
        policy_engine = PolicyEngine(self.application, user or self.request.user, self.request)
        policy_engine.use_cache = False
        policy_engine.request = self.modify_policy_request(policy_engine.request)
        policy_engine.build()
        result = policy_engine.result
        LOGGER.debug(
            "PolicyAccessView user_has_access",
            user=user.username,
            app=self.application.slug,
            result=result,
        )
        if not result.passing:
            for message in result.messages:
                messages.error(self.request, _(message))
        return result


def url_with_qs(url: str, **kwargs):
    """Update/set querystring of `url` with the parameters in `kwargs`. Original query string
    parameters are retained"""
    if "?" not in url:
        return url + f"?{urlencode(kwargs)}"
    url, _, qs = url.partition("?")
    qs = QueryDict(qs, mutable=True)
    qs.update(kwargs)
    return url + f"?{urlencode(qs.items())}"


class BufferView(TemplateView):
    """Buffer view"""

    template_name = "policies/buffer.html"

    def get_context_data(self, **kwargs):
        buf_id = self.request.GET.get(QS_BUFFER_ID)
        buffer = self.request.session.get(SESSION_KEY_BUFFER % buf_id)
        kwargs["method"] = buffer["method"]
        kwargs["post"] = dumps(buffer["post"])
        kwargs["check_auth_url"] = reverse("authentik_api:user-me")
        kwargs["redirect_url"] = url_with_qs(buffer["url"], **{QS_BUFFER_ID: buf_id})
        kwargs["auth_url"] = url_with_qs(buffer["url"], **{QS_SKIP_BUFFER: True})
        return super().get_context_data(**kwargs)


class BufferedPolicyAccessView(PolicyAccessView):
    """PolicyAccessView which buffers access requests in case the user is not logged in"""

    def handle_no_permission(self):
        plan: FlowPlan | None = self.request.session.get(SESSION_KEY_PLAN)
        if not plan:
            return super().handle_no_permission()
        flow = Flow.objects.filter(pk=plan.flow_pk).first()
        if not flow or flow.designation != FlowDesignation.AUTHENTICATION:
            return super().handle_no_permission()
        if self.request.GET.get(QS_SKIP_BUFFER):
            return super().handle_no_permission()
        buffer_id = str(uuid4())
        self.request.session[SESSION_KEY_BUFFER % buffer_id] = {
            "get": self.request.GET,
            "post": self.request.POST,
            "url": self.request.build_absolute_uri(self.request.get_full_path()),
            "method": self.request.method,
        }
        return redirect(
            reverse("authentik_policies:buffer")
            + "?"
            + urlencode(
                {
                    QS_BUFFER_ID: buffer_id,
                }
            )
        )

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if QS_BUFFER_ID in self.request.GET:
            self.request.session.pop(SESSION_KEY_BUFFER % self.request.GET[QS_BUFFER_ID])
        print(self.request.session.items())
        return response
