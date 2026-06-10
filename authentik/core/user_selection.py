"""Helpers for selecting between the sessions a browser holds.

Every login creates its own Session/AuthenticatedSession pair; all pairs created by the
same browser share the AuthenticatedSession.browser_key stamped from the browser cookie
(see authentik.root.middleware). These helpers list those logins and decide whether the
browser may switch to one of them without re-authenticating.
"""

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone

from authentik.common.oauth.constants import PROMPT_SELECT_ACCOUNT, QS_LOGIN_HINT
from authentik.core.models import AuthenticatedSession, User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_REDIRECT, FlowPlanner
from authentik.lib.avatars import get_avatar
from authentik.policies.engine import PolicyEngine

QS_USER_UID = "user_uid"
PLAN_CONTEXT_USER_SELECTION_USER_UID = "user_selection_user_uid"
PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT = "user_selection_login_hint"
USER_SELECTION_QUERY_CONTEXT = (
    (QS_USER_UID, PLAN_CONTEXT_USER_SELECTION_USER_UID),
    (QS_LOGIN_HINT, PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT),
)


class UserSelectionAuthentication(StrEnum):
    """Whether selecting the user switches to a live session or requires authentication."""

    AUTHENTICATED = "authenticated"
    REMEMBERED = "remembered"


USER_SELECTION_AUTHENTICATION_CHOICES = tuple(
    (choice.value, choice.name) for choice in UserSelectionAuthentication
)


@dataclass(frozen=True, slots=True)
class SelectableUser:
    """A user the browser knows about, plus the current request's ability to use it."""

    user: User
    is_current: bool
    switchable_session: AuthenticatedSession | None = None

    @property
    def uid(self) -> str:
        """Stable public identifier used by user-selection callers."""
        return self.user.uuid.hex

    @property
    def authentication(self) -> UserSelectionAuthentication:
        """Return whether selecting this user can continue without authentication."""
        if self.is_current or self.switchable_session is not None:
            return UserSelectionAuthentication.AUTHENTICATED
        return UserSelectionAuthentication.REMEMBERED


def user_matches_hint(user: User, hint: str) -> bool:
    """Check whether a user matches the supplied login hint."""
    return hint in {user.uuid.hex, user.email, user.username}


def request_selected_current_user(request: HttpRequest) -> bool:
    """Return true when the request carries the selected active account."""
    selected_user_uid = request.GET.get(QS_USER_UID)
    return bool(
        request.user.is_authenticated
        and selected_user_uid
        and selected_user_uid == request.user.uuid.hex
    )


def get_browser_sessions(request: HttpRequest) -> QuerySet[AuthenticatedSession]:
    """Live logins created by this browser, most recently used first."""
    browser_key = getattr(request, "browser_key", None)
    if not browser_key:
        return AuthenticatedSession.objects.none()
    return (
        AuthenticatedSession.objects.filter(
            browser_key=browser_key,
            session__expires__gt=timezone.now(),
            user__is_active=True,
        )
        .select_related("session", "user")
        .order_by("-session__last_used")
    )


def get_selectable_accounts(request: HttpRequest) -> list[SelectableUser]:
    """Users this browser can select between, current user first, one entry per user."""
    users: dict[str, SelectableUser] = {}
    can_switch_sessions = request.user.is_authenticated
    if request.user.is_authenticated:
        current_user = SelectableUser(request.user, is_current=True)
        users[current_user.uid] = current_user
    for session in get_browser_sessions(request):
        selectable = SelectableUser(
            session.user,
            is_current=False,
            switchable_session=session if can_switch_sessions else None,
        )
        users.setdefault(
            selectable.uid,
            selectable,
        )
    return list(users.values())


def serialize_selectable_user(
    request: HttpRequest,
    selectable: SelectableUser,
    hint: str | None = None,
) -> dict[str, object]:
    """Serialize a selectable user for user selection surfaces."""
    user = selectable.user
    data = {
        "uid": selectable.uid,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "avatar": get_avatar(user, request),
        "is_current": selectable.is_current,
        "authentication": selectable.authentication,
    }
    if hint is not None:
        data["is_hint"] = bool(hint and user_matches_hint(user, hint))
    return data


def get_user_selection_flow(request: HttpRequest) -> Flow | None:
    """Return the brand user selection flow or the first applicable fallback."""
    brand_flow = getattr(request.brand, "flow_user_selection", None)
    if brand_flow:
        return brand_flow
    flows = Flow.objects.filter(designation=FlowDesignation.USER_SELECTION).order_by("slug")
    for flow in flows:
        engine = PolicyEngine(flow, request.user, request)
        engine.build()
        if engine.result.passing:
            return flow
    return None


def append_user_selection_hint(url: str, user: User) -> str:
    """Append user selection hints when returning to OAuth authorize."""
    parts = urlsplit(url)
    if parts.path != reverse("authentik_providers_oauth2:authorize"):
        return url
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key in {QS_USER_UID, QS_LOGIN_HINT}:
            continue
        if key == "prompt":
            prompts = [prompt for prompt in value.split() if prompt != PROMPT_SELECT_ACCOUNT]
            if prompts:
                query.append((key, " ".join(prompts)))
            continue
        query.append((key, value))
    query.extend(
        [
            (QS_USER_UID, user.uuid.hex),
            (QS_LOGIN_HINT, user.email or user.username),
        ]
    )
    return urlunsplit(parts._replace(query=urlencode(query)))


def start_user_selection_flow_response(
    request: HttpRequest,
    next_url: str,
    application=None,
) -> HttpResponse | None:
    """Start the configured user selection flow."""
    flow = get_user_selection_flow(request)
    if not flow:
        return None
    context = {
        PLAN_CONTEXT_REDIRECT: next_url,
    }
    for query_key, context_key in USER_SELECTION_QUERY_CONTEXT:
        if value := request.GET.get(query_key):
            context[context_key] = value
    if application:
        context[PLAN_CONTEXT_APPLICATION] = application
    planner = FlowPlanner(flow)
    planner.use_cache = False
    try:
        plan = planner.plan(request, context)
    except FlowNonApplicableException:
        return None
    return plan.to_redirect(request, flow)
