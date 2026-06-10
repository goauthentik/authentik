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
    append_user_selection_hint,
    get_selectable_users,
    get_switchable_session,
    serialize_user_selection_user,
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
    authentication = CharField()


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

    def get_users(self, hint: str = "") -> list[User]:
        """Get the users of this browser's live sessions in display order."""
        users = get_selectable_users(self.request)
        if not hint:
            return users
        return sorted(users, key=lambda user: not user_matches_hint(user, hint))

    def get_hint(self) -> str:
        """Return a suggested user identifier from the flow context or query."""
        hint = self.plan.context.get(PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT)
        if isinstance(hint, str):
            return hint
        request_hint = self.request.GET.get(QS_LOGIN_HINT)
        if isinstance(request_hint, str):
            return request_hint
        session_hint = self.request.session.get(SESSION_KEY_GET, {}).get(QS_LOGIN_HINT)
        return session_hint if isinstance(session_hint, str) else ""

    def get_requested_user_uid(self) -> str:
        """Return an explicitly requested user UID from the flow context or query."""
        user_uid = self.plan.context.get(PLAN_CONTEXT_USER_SELECTION_USER_UID)
        if isinstance(user_uid, str):
            return user_uid
        request_user_uid = self.request.GET.get(QS_USER_UID)
        if isinstance(request_user_uid, str):
            return request_user_uid
        session_user_uid = self.request.session.get(SESSION_KEY_GET, {}).get(QS_USER_UID)
        return session_user_uid if isinstance(session_user_uid, str) else ""

    def get_challenge(self) -> UserSelectionChallenge:
        """Show the current user and remembered users for this browser."""
        application = self.plan.context.get(PLAN_CONTEXT_APPLICATION, Application())
        hint = self.get_hint()
        users = [
            serialize_user_selection_user(self.request, user, hint) for user in self.get_users(hint)
        ]
        return UserSelectionChallenge(
            data={
                "component": COMPONENT,
                "application_name": application.name,
                "accounts": users,
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
        session_next_url = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, reverse("authentik_core:root-redirect")
        )
        return (
            session_next_url
            if isinstance(session_next_url, str)
            else reverse("authentik_core:root-redirect")
        )

    def redirect_to_login(self, selected_user: User | None = None) -> HttpResponse:
        """Start normal authentication for the selected user."""
        next_url = self.get_next_url()
        query = {
            NEXT_ARG_NAME: (
                append_user_selection_hint(next_url, selected_user) if selected_user else next_url
            ),
        }
        if selected_user:
            query[QS_LOGIN_HINT] = selected_user.email or selected_user.username
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
        users_by_id = {user.uuid.hex: user for user in self.get_users()}
        selected_user = users_by_id.get(selected_user_uid)
        if not selected_user:
            LOGGER.warning("selected user is not known", selected_user=selected_user_uid)
            return self.executor.stage_invalid()
        if self.request.user.is_authenticated and selected_user.pk == self.request.user.pk:
            return self.continue_current_user(selected_user)
        if target := get_switchable_session(self.request, selected_user):
            return self.switch_to_session(target)
        return self.redirect_to_login(selected_user)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Continue as the current user or authenticate as another user."""
        user_response = cast(UserSelectionChallengeResponse, response)
        action = user_response.validated_data["action"]
        selected_user_uid = user_response.validated_data.get("selected_user", "")
        if action == "continue":
            if selected_user_uid:
                return self.select_user(selected_user_uid)
            if self.request.user.is_authenticated:
                return self.continue_current_user(cast(User, self.request.user))
            return self.executor.stage_invalid()
        if selected_user_uid:
            return self.select_user(selected_user_uid)
        return self.redirect_to_login()
