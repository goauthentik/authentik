from typing import Any, List, Optional, Tuple

from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, reverse
from django.views.generic import View
from structlog import get_logger

from passbook.core.models import Factor, User
from passbook.core.views.utils import PermissionDeniedView
from passbook.flows.executor.base import FlowExecutor
from passbook.flows.executor.state import FlowState
from passbook.flows.models import Flow
from passbook.lib.config import CONFIG
from passbook.lib.utils.http import redirect_with_qs
from passbook.lib.utils.reflection import class_to_path, path_to_class
from passbook.lib.utils.urls import is_url_absolute
from passbook.lib.views import bad_request_message
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()
SESSION_STATE_KEY = "passbook_flows_state"
NEXT_ARG_NAME = "next"


def check_config_domain(request: HttpRequest) -> Optional[HttpResponse]:
    """Checks if current request's domain matches configured Domain, and
    adds a warning if not."""
    current_domain = request.get_host()
    if ":" in current_domain:
        current_domain, _ = current_domain.split(":")
    config_domain = CONFIG.y("domain")
    if current_domain != config_domain:
        message = (
            f"Current domain of '{current_domain}' doesn't "
            f"match configured domain of '{config_domain}'."
        )
        LOGGER.warning(message)
        return bad_request_message(request, message)
    return None


def bootstrap_http_executor(request: HttpRequest, pending_user: User):
    """Bootstrap HttpExecutor by creating the initial state in the user's session"""
    state = FlowState(
        pending_user_pk=pending_user.pk,
        flow_pk=Flow.objects.filter(designation="auth").first().pk,
    )
    request.session[SESSION_STATE_KEY] = state


class HttpExecutor(FlowExecutor):

    request: HttpRequest

    def state_restore(self):
        self._state = self.request.session[SESSION_STATE_KEY]
        LOGGER.debug("HTTP_EX(state): state_restore", state=self._state)

    def state_persist(self):
        self.request.session[SESSION_STATE_KEY] = self._state
        LOGGER.debug("HTTP_EX(state): state_persist", state=self._state)

    def state_cleanup(self):
        del self.request.session[SESSION_STATE_KEY]
        LOGGER.debug("HTTP_EX(state): state_clear")


class HttpExecutorView(HttpExecutor, View):
    """Wizard-like Multi-factor authenticator"""

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

    def handle_no_state(self) -> HttpResponse:
        if NEXT_ARG_NAME in self.request.GET:
            return redirect_with_qs(self.request.GET.get(NEXT_ARG_NAME))
        if self.request.user.is_authenticated:
            return redirect_with_qs("passbook_core:overview", self.request.GET)
        return redirect_with_qs("passbook_core:auth-login", self.request.GET)

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Check if user passes test (i.e. SESSION_PENDING_USER is set)
        user_test_result = SESSION_STATE_KEY in self.request.session
        if not user_test_result:
            incorrect_domain_message = self._check_config_domain()
            if incorrect_domain_message:
                return incorrect_domain_message
            return self.handle_no_state()

        self.state_restore()

        # Lookup current factor object
        self.current_factor = self.get_next_factor()
        if not self.current_factor:
            self.passed()
            next_param = self.request.GET.get(NEXT_ARG_NAME, None)
            if next_param and not is_url_absolute(next_param):
                return redirect(next_param)
            return redirect_with_qs("passbook_core:overview")
        # Instantiate Next Factor and pass request
        self._current_factor_class = self.current_factor.factor_class(self)
        self._current_factor_class.pending_user = self.pending_user
        self._current_factor_class.request = request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass get request to current factor"""
        LOGGER.debug(
            "HTTP_EX: forwarding GET", factor=self._current_factor_class.__class__,
        )
        return self._current_factor_class.get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """pass post request to current factor"""
        LOGGER.debug(
            "HTTP_EX: forwarding POST", factor=self._current_factor_class.__class__,
        )
        return self._current_factor_class.post(request, *args, **kwargs)

    def user_ok(self) -> HttpResponse:
        """Redirect to next Factor"""
        self.factor_passed()
        LOGGER.debug("HTTP_EX: Redirecting to next factor")
        return redirect_with_qs("passbook_core:flows-execute", self.request.GET)

    def user_invalid(self) -> HttpResponse:
        """Show error message, user cannot login.
        This should only be shown if user authenticated successfully, but is disabled/locked/etc"""
        LOGGER.debug("HTTP_EX: User invalid")
        self.factor_failed()
        return redirect_with_qs("passbook_core:auth-denied", self.request.GET)

    def passed(self):
        super().passed()
        login(
            self.request,
            self.pending_user,
            backend=self._state.user_authentication_backend,
        )


class FactorPermissionDeniedView(PermissionDeniedView):
    """User could not be authenticated"""
