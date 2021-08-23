"""Authenticate with tokens"""

from typing import Any, Optional

from django.contrib.auth.backends import ModelBackend
from django.http.request import HttpRequest

from authentik.core.models import Token, TokenIntents, User
from authentik.flows.planner import FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


class InbuiltBackend(ModelBackend):
    """Inbuilt backend"""

    def authenticate(
        self, request: HttpRequest, username: Optional[str], password: Optional[str], **kwargs: Any
    ) -> Optional[User]:
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if not user:
            return None
        # Since we can't directly pass other variables to signals, and we want to log the method
        # and the token used, we assume we're running in a flow and set a variable in the context
        flow_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        flow_plan.context[PLAN_CONTEXT_METHOD] = "password"
        request.session[SESSION_KEY_PLAN] = flow_plan
        return user


class TokenBackend(ModelBackend):
    """Authenticate with token"""

    def authenticate(
        self, request: HttpRequest, username: Optional[str], password: Optional[str], **kwargs: Any
    ) -> Optional[User]:
        try:
            user = User._default_manager.get_by_natural_key(username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
            return None
        tokens = Token.filter_not_expired(
            user=user, key=password, intent=TokenIntents.INTENT_APP_PASSWORD
        )
        if not tokens.exists():
            return None
        token = tokens.first()
        # Since we can't directly pass other variables to signals, and we want to log the method
        # and the token used, we assume we're running in a flow and set a variable in the context
        flow_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        flow_plan.context[PLAN_CONTEXT_METHOD] = "app_password"
        flow_plan.context[PLAN_CONTEXT_METHOD_ARGS] = {"token": token}
        request.session[SESSION_KEY_PLAN] = flow_plan
        return token.user
