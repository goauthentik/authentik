"""authentik user selection stage."""

from typing import Any, cast
from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.fields import BooleanField, CharField, ChoiceField
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Application, AuthenticatedSession, User
from authentik.core.sessions import SessionStore
from authentik.core.user_selection import (
    PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT,
    PLAN_CONTEXT_USER_SELECTION_USER_UID,
    QS_USER_UID,
    USER_SELECTION_AUTHENTICATION_CHOICES,
    SelectableUser,
    append_user_selection_hint,
    get_selectable_accounts,
    get_user_login_hint,
    serialize_selectable_user,
    user_matches_hint,
)
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_REDIRECT, FlowPlan
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET
from authentik.root.middleware import ClientIPMiddleware

LOGGER = get_logger()
COMPONENT = "ak-stage-user-selection"


class UserSelectionChallengeUser(PassiveSerializer):
    """User shown by the user selection stage."""

    uid = CharField()
    username = CharField()
    name = CharField(allow_blank=True)
    email = CharField(allow_blank=True)
    avatar = CharField()
    is_current = BooleanField()
    is_hint = BooleanField()
    authentication = ChoiceField(choices=USER_SELECTION_AUTHENTICATION_CHOICES)


class UserSelectionChallenge(Challenge):
    """Challenge for selecting a browser-local user."""

    component = CharField(default=COMPONENT)
    application_name = CharField(allow_blank=True)
    accounts = UserSelectionChallengeUser(many=True)


class UserSelectionChallengeResponse(ChallengeResponse):
    """User selection response."""

    component = CharField(default=COMPONENT)
    action = ChoiceField(choices=["continue", "login"])
    selected_user = CharField(required=False, allow_blank=True)


class UserSelectionStageView(ChallengeStageView):
    """Prompt the user to select a browser-local user."""

    response_class = UserSelectionChallengeResponse

    @property
    def plan(self) -> FlowPlan:
        """Return the active flow plan."""
        return cast(FlowPlan, self.executor.plan)

    def get_accounts(self, hint: str = "") -> list[SelectableUser]:
        """Get this browser's selectable accounts in display order."""
        accounts = get_selectable_accounts(self.request)
        if not hint:
            return accounts
        return sorted(accounts, key=lambda account: not user_matches_hint(account.user, hint))

    def get_selection_value(self, context_key: str, query_key: str) -> str:
        """Return a user-selection value from the active plan, request, or saved GET state."""
        context_value = self.plan.context.get(context_key)
        if isinstance(context_value, str):
            return context_value
        request_value = self.request.GET.get(query_key)
        if isinstance(request_value, str):
            return request_value
        session_value = self.request.session.get(SESSION_KEY_GET, {}).get(query_key)
        return session_value if isinstance(session_value, str) else ""

    def get_hint(self) -> str:
        """Return a suggested user identifier from the flow context or query."""
        return self.get_selection_value(PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT, QS_LOGIN_HINT)

    def get_requested_user_uid(self) -> str:
        """Return an explicitly requested user UID from the flow context or query."""
        return self.get_selection_value(PLAN_CONTEXT_USER_SELECTION_USER_UID, QS_USER_UID)

    def get_challenge(self) -> UserSelectionChallenge:
        """Show the current user and remembered users for this browser."""
        application = self.plan.context.get(PLAN_CONTEXT_APPLICATION, Application())
        hint = self.get_hint()
        accounts = [
            serialize_selectable_user(self.request, account, hint)
            for account in self.get_accounts(hint)
        ]
        return UserSelectionChallenge(
            data={
                "component": COMPONENT,
                "application_name": application.name,
                "accounts": accounts,
            }
        )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Auto-select a user when authentik requested a specific user UID."""
        selected_user = self.get_requested_user_uid()
        if selected_user:
            return self.select_user(selected_user)
        return super().get(request, *args, **kwargs)

    def get_next_url(self) -> str:
        """Return the flow's final destination."""
        next_url = self.plan.context.get(PLAN_CONTEXT_REDIRECT)
        if isinstance(next_url, str) and next_url:
            return next_url
        fallback_url = reverse("authentik_core:root-redirect")
        session_next_url = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, fallback_url
        )
        return session_next_url if isinstance(session_next_url, str) else fallback_url

    def redirect_to_login(self, selected_user: User | None = None) -> HttpResponse:
        """Start normal authentication for the selected user."""
        next_url = self.get_next_url()
        query = {
            NEXT_ARG_NAME: (
                append_user_selection_hint(next_url, selected_user) if selected_user else next_url
            ),
        }
        if selected_user:
            query[QS_LOGIN_HINT] = get_user_login_hint(selected_user)
        url = reverse("authentik_flows:default-authentication")
        self.executor.cancel()  # type: ignore[no-untyped-call]
        return redirect(f"{url}?{urlencode(query)}")

    def continue_current_user(self, selected_user: User) -> HttpResponse:
        """Continue the flow as the already-authenticated selected user."""
        if PLAN_CONTEXT_REDIRECT in self.plan.context:
            self.plan.context[PLAN_CONTEXT_REDIRECT] = append_user_selection_hint(
                self.plan.context[PLAN_CONTEXT_REDIRECT],
                selected_user,
            )
        return self.executor.stage_ok()

    def switch_to_session(self, target: AuthenticatedSession) -> HttpResponse:
        """Make the target login this browser's active session. The session cookie is
        reissued by the session middleware from the swapped request.session."""
        next_url = append_user_selection_hint(self.get_next_url(), target.user)
        self.executor.cancel()
        # The flow ends here, on the old session; persist the cancellation before
        # detaching from it, as the middleware only saves the swapped-in session.
        self.request.session.save()
        self.request.session = SessionStore(
            target.session.session_key,
            last_ip=ClientIPMiddleware.get_client_ip(self.request),
            last_user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
            browser_key=self.request.browser_key,
        )
        self.request.session.modified = True
        self.request.user = target.user
        return redirect(next_url)

    def select_user(self, selected_user_uid: str) -> HttpResponse:
        """Continue as the current user, switch to a live session of the selected user,
        or fall back to authenticating as them."""
        accounts_by_id = {account.uid: account for account in self.get_accounts()}
        selected = accounts_by_id.get(selected_user_uid)
        if not selected:
            LOGGER.warning("selected user is not known", selected_user=selected_user_uid)
            return self.executor.stage_invalid()
        selected_user = selected.user
        if self.request.user.is_authenticated and selected_user.pk == self.request.user.pk:
            return self.continue_current_user(selected_user)
        if selected.switchable_session:
            return self.switch_to_session(selected.switchable_session)
        return self.redirect_to_login(selected_user)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Continue as the current user or authenticate as another user."""
        user_response = cast(UserSelectionChallengeResponse, response)
        action = user_response.validated_data["action"]
        selected_user_uid = user_response.validated_data.get("selected_user", "")
        if selected_user_uid:
            return self.select_user(selected_user_uid)
        if action == "continue":
            if self.request.user.is_authenticated:
                return self.continue_current_user(cast(User, self.request.user))
            return self.executor.stage_invalid()
        return self.redirect_to_login()
