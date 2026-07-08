"""User switch view"""

from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View

from authentik.core.models import AuthenticatedSession, User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_USER_SWITCH_FROM_USER,
    PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION,
    PLAN_CONTEXT_USER_SWITCH_STALE_USER,
    FlowPlanner,
)
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.lib.views import bad_request_message
from authentik.policies.engine import PolicyEngine


class UserSwitchView(LoginRequiredMixin, View):
    """Authenticate another login held by this browser."""

    def get(self, request: HttpRequest, user_pk: int) -> HttpResponse:
        flow = request.brand.flow_user_switch
        if not flow:
            return bad_request_message(
                request,
                _("User switching is disabled."),
                title=_("User switching disabled"),
            )
        self.ensure_flow_applicable_to_current_user(request, flow)
        context = {}
        session = self.get_user_switching_session(request, user_pk)
        if not session:
            context[PLAN_CONTEXT_USER_SWITCH_STALE_USER] = str(user_pk)
            return self.redirect_to_flow(request, flow, context)
        context[PLAN_CONTEXT_PENDING_USER] = session.user
        # Pre-fill the identification stage so the target user doesn't have to be retyped,
        # letting a policy-free switch flow skip straight to the next stage.
        context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = session.user.username
        context[PLAN_CONTEXT_USER_SWITCH_FROM_USER] = request.user
        context[PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION] = session.session.session_key
        return self.redirect_to_flow(request, flow, context)

    @staticmethod
    def redirect_to_flow(
        request: HttpRequest,
        flow: Flow,
        context: dict[str, Any],
    ) -> HttpResponse:
        """Plan and redirect to the user switch flow."""
        planner = FlowPlanner(flow)
        # The user-switch context can change policy decisions while building the stage list.
        # Reusing a cached plan would skip that planning pass.
        planner.use_cache = False
        try:
            plan = planner.plan(request, context)
        except FlowNonApplicableException:
            raise Http404 from None
        return plan.to_redirect(request, flow)

    @staticmethod
    def ensure_flow_applicable_to_current_user(request: HttpRequest, flow: Flow) -> None:
        """Reject switch flows that the current source user cannot access."""
        engine = PolicyEngine(flow, cast(User, request.user), request)
        engine.use_cache = False
        engine.build()
        if not engine.result.passing:
            raise Http404

    @staticmethod
    def get_user_switching_session(
        request: HttpRequest, user_pk: int
    ) -> AuthenticatedSession | None:
        """Live login bound to this request's user switching token, if any."""
        user_switching_token = getattr(request, "user_switching_token", None)
        if not user_switching_token:
            return None
        return (
            AuthenticatedSession.objects.filter(
                user_switching_token=user_switching_token,
                session__expires__gt=timezone.now(),
                user__is_active=True,
                user_id=user_pk,
            )
            .select_related("session", "user")
            .order_by("-session__last_used")
            .first()
        )
