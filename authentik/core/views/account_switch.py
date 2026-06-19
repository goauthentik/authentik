"""Account switch view"""

from typing import Any
from urllib.parse import urlencode

from django.http import Http404, HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View

from authentik.core.models import AuthenticatedSession
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow
from authentik.flows.planner import (
    PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER,
    PLAN_CONTEXT_PENDING_USER,
    FlowPlanner,
)

QS_ACCOUNT_SWITCH_STALE = "account_switch_stale"


class AccountSwitchView(View):
    """Authenticate another login held by this browser."""

    def get(self, request: HttpRequest, user_pk: int) -> HttpResponse:
        flow = request.brand.flow_account_switch
        if not flow:
            return TemplateResponse(
                request,
                "if/error.html",
                {
                    "title": _("Account switching disabled"),
                    "message": _("Account switching is disabled."),
                },
                status=400,
            )
        if not request.user.is_authenticated:
            return TemplateResponse(
                request,
                "if/error.html",
                {
                    "title": _("Account switching unavailable"),
                    "message": _("Account switching requires an active session."),
                },
                status=400,
            )
        context = {}
        session = self.get_browser_session(request, user_pk)
        if not session:
            return self.redirect_to_flow(request, flow, context, stale_user_pk=user_pk)
        context[PLAN_CONTEXT_PENDING_USER] = session.user
        context[PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER] = request.user
        return self.redirect_to_flow(request, flow, context)

    @staticmethod
    def redirect_to_flow(
        request: HttpRequest,
        flow: Flow,
        context: dict[str, Any],
        stale_user_pk: int | None = None,
    ) -> HttpResponse:
        """Plan and redirect to the account switch flow."""
        planner = FlowPlanner(flow)
        # The account-switch context can change policy decisions while building the stage list.
        # Reusing a cached plan would skip that planning pass.
        planner.use_cache = False
        try:
            plan = planner.plan(request, context)
        except FlowNonApplicableException:
            raise Http404 from None
        response = plan.to_redirect(request, flow)
        if stale_user_pk:
            separator = "&" if "?" in response["Location"] else "?"
            response["Location"] += separator + urlencode({QS_ACCOUNT_SWITCH_STALE: stale_user_pk})
        return response

    @staticmethod
    def get_browser_session(request: HttpRequest, user_pk: int) -> AuthenticatedSession | None:
        """Live login of this browser matching the target user, if any."""
        browser_key = getattr(request, "browser_key", None)
        if not browser_key:
            return None
        return (
            AuthenticatedSession.objects.filter(
                browser_key=browser_key,
                session__expires__gt=timezone.now(),
                user__is_active=True,
                user_id=user_pk,
            )
            .select_related("session", "user")
            .order_by("-session__last_used")
            .first()
        )
