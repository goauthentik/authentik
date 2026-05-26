"""authentik account selection stage."""

from urllib.parse import urlencode

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.fields import BooleanField, CharField, ChoiceField
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.account_selection import (
    PLAN_CONTEXT_ACCOUNT_SELECTION_LOGIN_HINT,
    PLAN_CONTEXT_ACCOUNT_SELECTION_USER_UID,
    PLAN_CONTEXT_ACCOUNT_SWITCH_SESSION_KEY,
    PLAN_CONTEXT_ACCOUNT_SWITCH_USER_UID,
    QS_ACCOUNT_UID,
    QS_ADD_ACCOUNT,
    get_known_account_session,
    get_known_account_users,
    get_live_account_session,
    set_account_selection_context,
    set_session_cookie,
    start_fresh_session,
)
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Application, AuthenticatedSession, User
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_REDIRECT
from authentik.flows.stage import ChallengeStageView, StageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET
from authentik.lib.avatars import get_avatar

LOGGER = get_logger()
COMPONENT = "ak-stage-account-selection"


class AccountSelectionChallengeUser(PassiveSerializer):
    """Account shown by the account selection stage."""

    uid = CharField()
    username = CharField()
    name = CharField(allow_blank=True)
    email = CharField(allow_blank=True)
    avatar = CharField()
    is_current = BooleanField()
    is_hint = BooleanField()


def user_matches_hint(user: User, hint: str) -> bool:
    """Check whether an account matches the supplied login hint."""
    return hint in {user.uuid.hex, user.email, user.username}


class AccountSelectionChallenge(Challenge):
    """Challenge for selecting a browser-local account."""

    component = CharField(default=COMPONENT)
    application_name = CharField(allow_blank=True)
    accounts = AccountSelectionChallengeUser(many=True)


class AccountSelectionChallengeResponse(ChallengeResponse):
    """Account selection response."""

    component = CharField(default=COMPONENT)
    action = ChoiceField(choices=["continue", "login", "switch"])
    selected_account = CharField(required=False, allow_blank=True)


class AccountSelectionStageView(ChallengeStageView):
    """Prompt the user to select a browser-local account."""

    response_class = AccountSelectionChallengeResponse

    def get_account_users(self, hint: str = "") -> list[User]:
        """Get known users for this browser session in display order."""
        current_account = []
        if self.request.user.is_authenticated:
            current_account.append(self.request.user.uuid.hex)
        users = get_known_account_users(self.request, current_account)
        if not hint:
            return users
        return sorted(users, key=lambda user: not user_matches_hint(user, hint))

    def get_account_hint(self) -> str:
        """Return a suggested account identifier from the flow context or query."""
        return (
            self.executor.plan.context.get(PLAN_CONTEXT_ACCOUNT_SELECTION_LOGIN_HINT)
            or self.request.session.get(SESSION_KEY_GET, {}).get(QS_LOGIN_HINT)
            or ""
        )

    def get_requested_account_uid(self) -> str:
        """Return an explicitly requested account UID from the flow context or query."""
        return (
            self.executor.plan.context.get(PLAN_CONTEXT_ACCOUNT_SELECTION_USER_UID)
            or self.request.session.get(SESSION_KEY_GET, {}).get(QS_ACCOUNT_UID)
            or ""
        )

    def serialize_account(self, user: User, hint: str = "") -> dict[str, object]:
        """Serialize a selectable account."""
        is_current = (
            self.request.user.is_authenticated
            and not isinstance(self.request.user, AnonymousUser)
            and user.pk == self.request.user.pk
        )
        return {
            "uid": user.uuid.hex,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "avatar": get_avatar(user, self.request),
            "is_current": is_current,
            "is_hint": bool(hint and user_matches_hint(user, hint)),
        }

    def get_challenge(self) -> AccountSelectionChallenge:
        """Show the current account and live remembered accounts for this browser."""
        application = self.executor.plan.context.get(PLAN_CONTEXT_APPLICATION, Application())
        hint = self.get_account_hint()
        accounts = [self.serialize_account(user, hint) for user in self.get_account_users(hint)]
        return AccountSelectionChallenge(
            data={
                "component": COMPONENT,
                "application_name": application.name,
                "accounts": accounts,
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Auto-select an account when authentik requested a specific account UID."""
        selected_account = self.get_requested_account_uid()
        if selected_account:
            return self.switch_to_account(selected_account)
        return super().get(request, *args, **kwargs)

    def get_next_url(self) -> str:
        """Return the flow's final destination."""
        next_url = self.executor.plan.context.get(PLAN_CONTEXT_REDIRECT)
        if next_url:
            return next_url
        return self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, reverse("authentik_core:root-redirect")
        )

    def use_another_account(self) -> HttpResponse:
        """Start login for an account that is not currently remembered."""
        query = {
            NEXT_ARG_NAME: self.get_next_url(),
            QS_ADD_ACCOUNT: "true",
        }
        url = reverse("authentik_flows:default-authentication")
        self.executor.cancel()
        return start_fresh_session(redirect(f"{url}?{urlencode(query)}"), self.request)

    def get_current_account_session(self, selected_user: User) -> AuthenticatedSession | None:
        """Return the current authenticated session if it belongs to the selected user."""
        if not self.request.user.is_authenticated or selected_user.pk != self.request.user.pk:
            return None
        return (
            AuthenticatedSession.objects.select_related("session", "user")
            .filter(session__session_key=self.request.session.session_key, user=selected_user)
            .first()
        )

    def switch_to_account(self, selected_account: str) -> HttpResponse:
        """Store the selected account on the flow context."""
        users_by_id = {user.uuid.hex: user for user in self.get_account_users()}
        selected_user = users_by_id.get(selected_account)
        if not selected_user:
            LOGGER.warning("selected account is not known", selected_account=selected_account)
            return self.executor.stage_invalid()
        account_session = self.get_current_account_session(selected_user)
        if not account_session:
            account_session = get_known_account_session(self.request, account_uid=selected_account)
        if not account_session or not account_session.session:
            return self.executor.stage_invalid()
        set_account_selection_context(
            self.executor.plan.context,
            selected_user,
            account_session.session.session_key,
        )
        return self.executor.stage_ok()

    def challenge_valid(self, response: AccountSelectionChallengeResponse) -> HttpResponse:
        """Continue, switch to a remembered account, or use another account."""
        action = response.validated_data["action"]
        if action == "login":
            return self.use_another_account()
        return self.switch_to_account(response.validated_data.get("selected_account", ""))


class AccountSwitchStageView(StageView):
    """Activate the account selected by an earlier Account Selection stage."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Switch the primary browser session after the account selection flow passed."""
        account_uid = self.executor.plan.context.get(PLAN_CONTEXT_ACCOUNT_SWITCH_USER_UID)
        session_key = self.executor.plan.context.get(PLAN_CONTEXT_ACCOUNT_SWITCH_SESSION_KEY)
        if not isinstance(account_uid, str) or not isinstance(session_key, str):
            return self.executor.stage_invalid()
        account_session = get_live_account_session(account_uid, session_key)
        if not account_session:
            return self.executor.stage_invalid()
        response = self.executor.stage_ok()
        request.session.save()
        request.session.modified = False
        return set_session_cookie(response, request, account_session)
