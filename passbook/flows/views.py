"""passbook multi-factor authentication engine"""
from typing import List, Optional, Tuple

from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.http import urlencode
from django.views.generic import View
from structlog import get_logger

from passbook.core.models import Factor, User
from passbook.core.views.utils import PermissionDeniedView
from passbook.flows.exceptions import FlowNonApplicableError
from passbook.flows.models import Flow
from passbook.flows.planner import FlowPlan, FlowPlanner
from passbook.lib.config import CONFIG
from passbook.lib.utils.reflection import class_to_path, path_to_class
from passbook.lib.utils.urls import is_url_absolute
from passbook.lib.views import bad_request_message
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()
# Argument used to redirect user after login
NEXT_ARG_NAME = "next"


def _redirect_with_qs(view, get_query_set=None):
    """Wrapper to redirect whilst keeping GET Parameters"""
    target = reverse(view)
    if get_query_set:
        target += "?" + urlencode(get_query_set.items())
    return redirect(target)


class AuthenticationView(UserPassesTestMixin, View):
    """Wizard-like Multi-factor authenticator"""

    SESSION_FACTOR = "passbook_factor"
    SESSION_PENDING_FACTORS = "passbook_pending_factors"
    SESSION_PENDING_USER = "passbook_pending_user"
    SESSION_USER_BACKEND = "passbook_user_backend"
    SESSION_IS_SSO_LOGIN = "passbook_sso_login"

    pending_user: User
    pending_factors: List[Tuple[str, str]] = []

    _current_factor_class: Factor

    current_factor: Factor

    # Allow only not authenticated users to login
    def test_func(self) -> bool:
        return AuthenticationView.SESSION_PENDING_USER in self.request.session

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
            LOGGER.warning(message)
            return bad_request_message(self.request, message)
        return None

    def handle_no_permission(self) -> HttpResponse:
        # Function from UserPassesTestMixin
        if NEXT_ARG_NAME in self.request.GET:
            return redirect(self.request.GET.get(NEXT_ARG_NAME))
        if self.request.user.is_authenticated:
            return _redirect_with_qs("passbook_core:overview", self.request.GET)
        return _redirect_with_qs("passbook_core:auth-login", self.request.GET)

    def get_pending_factors(self) -> List[Tuple[str, str]]:
        """Loading pending factors from Database or load from session variable"""
        # Write pending factors to session
        if AuthenticationView.SESSION_PENDING_FACTORS in self.request.session:
            return self.request.session[AuthenticationView.SESSION_PENDING_FACTORS]
        # Get an initial list of factors which are currently enabled
        # and apply to the current user. We check policies here and block the request
        _all_factors = (
            Factor.objects.filter(enabled=True).order_by("order").select_subclasses()
        )
        pending_factors = []
        for factor in _all_factors:
            factor: Factor
            LOGGER.debug(
                "Checking if factor applies to user",
                factor=factor,
                user=self.pending_user,
            )
            policy_engine = PolicyEngine(
                factor.policies.all(), self.pending_user, self.request
            )
            policy_engine.build()
            if policy_engine.passing:
                pending_factors.append((factor.uuid.hex, factor.type))
                LOGGER.debug("Factor applies", factor=factor, user=self.pending_user)
        return pending_factors

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Check if user passes test (i.e. SESSION_PENDING_USER is set)
        user_test_result = self.get_test_func()()
        if not user_test_result:
            incorrect_domain_message = self._check_config_domain()
            if incorrect_domain_message:
                return incorrect_domain_message
            return self.handle_no_permission()
        # Extract pending user from session (only remember uid)
        self.pending_user = get_object_or_404(
            User, id=self.request.session[AuthenticationView.SESSION_PENDING_USER]
        )
        self.pending_factors = self.get_pending_factors()
        # Read and instantiate factor from session
        factor_uuid, factor_class = None, None
        if AuthenticationView.SESSION_FACTOR not in request.session:
            # Case when no factors apply to user, return error denied
            if not self.pending_factors:
                # Case when user logged in from SSO provider and no more factors apply
                if AuthenticationView.SESSION_IS_SSO_LOGIN in request.session:
                    LOGGER.debug("User authenticated with SSO, logging in...")
                    return self._user_passed()
                return self.user_invalid()
            factor_uuid, factor_class = self.pending_factors[0]
        else:
            factor_uuid, factor_class = request.session[
                AuthenticationView.SESSION_FACTOR
            ]
        # Lookup current factor object
        self.current_factor = (
            Factor.objects.filter(uuid=factor_uuid).select_subclasses().first()
        )
        # Instantiate Next Factor and pass request
        factor = path_to_class(factor_class)
        self._current_factor_class = factor(self)
        self._current_factor_class.pending_user = self.pending_user
        self._current_factor_class.request = request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass get request to current factor"""
        LOGGER.debug(
            "Passing GET",
            view_class=class_to_path(self._current_factor_class.__class__),
        )
        return self._current_factor_class.get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass post request to current factor"""
        LOGGER.debug(
            "Passing POST",
            view_class=class_to_path(self._current_factor_class.__class__),
        )
        return self._current_factor_class.post(request, *args, **kwargs)

    def user_ok(self) -> HttpResponse:
        """Redirect to next Factor"""
        LOGGER.debug(
            "Factor passed",
            factor_class=class_to_path(self._current_factor_class.__class__),
        )
        # Remove passed factor from pending factors
        current_factor_tuple = (
            self.current_factor.uuid.hex,
            class_to_path(self._current_factor_class.__class__),
        )
        if current_factor_tuple in self.pending_factors:
            self.pending_factors.remove(current_factor_tuple)
        next_factor = None
        if self.pending_factors:
            next_factor = self.pending_factors.pop()
            # Save updated pening_factor list to session
            self.request.session[
                AuthenticationView.SESSION_PENDING_FACTORS
            ] = self.pending_factors
            self.request.session[AuthenticationView.SESSION_FACTOR] = next_factor
            LOGGER.debug("Rendering Factor", next_factor=next_factor)
            return _redirect_with_qs("passbook_flows:auth-process", self.request.GET)
        # User passed all factors
        LOGGER.debug("User passed all factors, logging in", user=self.pending_user)
        return self._user_passed()

    def user_invalid(self) -> HttpResponse:
        """Show error message, user cannot login.
        This should only be shown if user authenticated successfully, but is disabled/locked/etc"""
        LOGGER.debug("User invalid")
        self.cleanup()
        return _redirect_with_qs("passbook_flows:auth-denied", self.request.GET)

    def _user_passed(self) -> HttpResponse:
        """User Successfully passed all factors"""
        backend = self.request.session[AuthenticationView.SESSION_USER_BACKEND]
        login(self.request, self.pending_user, backend=backend)
        LOGGER.debug("Logged in", user=self.pending_user)
        # Cleanup
        self.cleanup()
        next_param = self.request.GET.get(NEXT_ARG_NAME, None)
        if next_param and not is_url_absolute(next_param):
            return redirect(next_param)
        return _redirect_with_qs("passbook_core:overview")

    def cleanup(self):
        """Remove temporary data from session"""
        session_keys = [
            self.SESSION_FACTOR,
            self.SESSION_PENDING_FACTORS,
            self.SESSION_PENDING_USER,
            self.SESSION_USER_BACKEND,
        ]
        for key in session_keys:
            if key in self.request.session:
                del self.request.session[key]
        LOGGER.debug("Cleaned up sessions")


class FactorPermissionDeniedView(PermissionDeniedView):
    """User could not be authenticated"""


SESSION_KEY_PLAN = "passbook_flows_plan"


class FlowExecutorView(View):
    """Stage 1 Flow executor, passing requests to Factor Views"""

    flow: Flow

    plan: FlowPlan
    current_factor: Factor
    current_factor_view: View

    def setup(self, request: HttpRequest, flow_slug: str):
        super().setup(request, flow_slug=flow_slug)
        # TODO: Do we always need this?
        self.flow = get_object_or_404(Flow, slug=flow_slug)

    def dispatch(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        # Early check if theres an active Plan for the current session
        if SESSION_KEY_PLAN not in self.request.session:
            LOGGER.debug(
                "No active Plan found, initiating planner", flow_slug=flow_slug
            )
            try:
                self.plan = self._initiate_plan()
            except FlowNonApplicableError as exc:
                LOGGER.warning("Flow not applicable to current user", exc=exc)
                return redirect("passbook_core:index")
        else:
            LOGGER.debug("Continuing existing plan", flow_slug=flow_slug)
            self.plan = self.request.session[SESSION_KEY_PLAN]
        # We don't save the Plan after getting the next factor
        # as it hasn't been successfully passed yet
        self.current_factor = self.plan.next()
        LOGGER.debug("Current factor", current_factor=self.current_factor)
        factor_cls = path_to_class(self.current_factor.type)
        self.current_factor_view = factor_cls(self)
        # self.current_factor_view.pending_user = self.pending_user
        self.current_factor_view.request = request
        return super().dispatch(request)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass get request to current factor"""
        LOGGER.debug(
            "Passing GET", view_class=class_to_path(self.current_factor_view.__class__),
        )
        return self.current_factor_view.get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass post request to current factor"""
        LOGGER.debug(
            "Passing POST",
            view_class=class_to_path(self.current_factor_view.__class__),
        )
        return self.current_factor_view.post(request, *args, **kwargs)

    def _initiate_plan(self) -> FlowPlan:
        planner = FlowPlanner(self.flow)
        plan = planner.plan(self.request)
        self.request.session[SESSION_KEY_PLAN] = plan
        return plan
