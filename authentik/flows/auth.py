from typing import cast

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN


class FlowActive(BaseAuthentication):
    """Authenticate requests when a flow is currently active"""

    def authenticate(self, request: Request):
        plan = cast(FlowPlan | None, request.session.get(SESSION_KEY_PLAN))
        if not plan:
            return None
        return (plan.context.get(PLAN_CONTEXT_PENDING_USER, AnonymousUser()), plan)
