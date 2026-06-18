"""Account switch view"""

from urllib.parse import urlencode

from django.http import Http404, HttpRequest, HttpResponse
from django.utils import timezone
from django.views import View

from authentik.core.models import AuthenticatedSession
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.planner import (
    PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER,
    PLAN_CONTEXT_IS_ACCOUNT_SWITCH,
    PLAN_CONTEXT_PENDING_USER,
    FlowPlanner,
)

QS_ACCOUNT_SWITCH_STALE = "account_switch_stale"


class AccountSwitchView(View):
    """Authenticate another login held by this browser."""

    def get(self, request: HttpRequest, user_uid: str) -> HttpResponse:
        flow = request.brand.flow_account_switch
        if not flow:
            raise Http404
        context = {}
        session = self.get_browser_session(request, user_uid)
        stale_user_uid = None
        if session:
            context.update(
                {
                    PLAN_CONTEXT_PENDING_USER: session.user,
                    PLAN_CONTEXT_IS_ACCOUNT_SWITCH: True,
                }
            )
            if request.user.is_authenticated:
                context[PLAN_CONTEXT_ACCOUNT_SWITCH_FROM_USER] = request.user
        else:
            stale_user_uid = user_uid
        planner = FlowPlanner(flow)
        # The context decides which stages policies skip, so cached plans don't apply
        planner.use_cache = False
        try:
            plan = planner.plan(request, context)
        except FlowNonApplicableException:
            raise Http404 from None
        response = plan.to_redirect(request, flow)
        if stale_user_uid:
            separator = "&" if "?" in response["Location"] else "?"
            response["Location"] += separator + urlencode({QS_ACCOUNT_SWITCH_STALE: stale_user_uid})
        return response

    @staticmethod
    def get_browser_session(request: HttpRequest, user_uid: str) -> AuthenticatedSession | None:
        """Live login of this browser matching the target user, if any."""
        browser_key = getattr(request, "browser_key", None)
        if not browser_key:
            return None
        sessions = (
            AuthenticatedSession.objects.filter(
                browser_key=browser_key,
                session__expires__gt=timezone.now(),
                user__is_active=True,
            )
            .select_related("session", "user")
            .order_by("-session__last_used")
        )
        return next((session for session in sessions if session.user.uid == user_uid), None)
