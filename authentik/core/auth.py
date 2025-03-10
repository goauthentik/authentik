"""Authenticate with tokens"""

from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.http.request import HttpRequest

from authentik.core.models import Token, TokenIntents, User
from authentik.events.utils import cleanse_dict, sanitize_dict
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


class InbuiltBackend(ModelBackend):
    """Inbuilt backend"""

    def authenticate(
        self, request: HttpRequest, username: str | None, password: str | None, **kwargs: Any
    ) -> User | None:
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if not user:
            return None
        self.set_method("password", request)
        return user

    async def aauthenticate(
        self, request: HttpRequest, username: str | None, password: str | None, **kwargs: Any
    ) -> User | None:
        user = await super().aauthenticate(request, username=username, password=password, **kwargs)
        if not user:
            return None
        self.set_method("password", request)
        return user

    def set_method(self, method: str, request: HttpRequest | None, **kwargs):
        """Set method data on current flow, if possbiel"""
        if not request:
            return
        # Since we can't directly pass other variables to signals, and we want to log the method
        # and the token used, we assume we're running in a flow and set a variable in the context
        flow_plan: FlowPlan = request.session.get(SESSION_KEY_PLAN, FlowPlan(""))
        flow_plan.context.setdefault(PLAN_CONTEXT_METHOD, method)
        flow_plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
        flow_plan.context[PLAN_CONTEXT_METHOD_ARGS].update(cleanse_dict(sanitize_dict(kwargs)))
        request.session[SESSION_KEY_PLAN] = flow_plan


class TokenBackend(InbuiltBackend):
    """Authenticate with token"""

    def authenticate(
        self, request: HttpRequest, username: str | None, password: str | None, **kwargs: Any
    ) -> User | None:
        try:
            user = User._default_manager.get_by_natural_key(username)

        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password, request=request)
            return None

        tokens = Token.filter_not_expired(
            user=user, key=password, intent=TokenIntents.INTENT_APP_PASSWORD
        )
        if not tokens.exists():
            return None
        token = tokens.first()
        self.set_method("token", request, token=token)
        return token.user
