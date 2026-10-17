from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.storage import FlowExecution


class FlowActive(BaseAuthentication):
    """Authenticate requests when a flow is currently active"""

    def authenticate(self, request: Request):
        plan = FlowExecution(request).plan
        if not plan:
            return None
        return (plan.context.get(PLAN_CONTEXT_PENDING_USER, AnonymousUser()), plan)
