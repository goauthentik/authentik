"""Helpers for selecting between the sessions a browser holds.

Every login creates its own Session/AuthenticatedSession pair; all pairs created by the
same browser share the AuthenticatedSession.browser_key stamped from the browser cookie
(see authentik.root.middleware). These helpers list those logins and decide whether the
browser may switch to one of them without re-authenticating.
"""

from enum import StrEnum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils import timezone

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.models import AuthenticatedSession, User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_REDIRECT, FlowPlanner
from authentik.lib.avatars import get_avatar
from authentik.policies.engine import PolicyEngine

QS_USER_UID = "user_uid"
PLAN_CONTEXT_USER_SELECTION_USER_UID = "user_selection_user_uid"
PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT = "user_selection_login_hint"


class UserSelectionAuthentication(StrEnum):
    """Whether selecting the user switches to a live session or requires authentication."""

    AUTHENTICATED = "authenticated"
    REMEMBERED = "remembered"


def user_matches_hint(user: User, hint: str) -> bool:
    """Check whether a user matches the supplied login hint."""
    return hint in {user.uuid.hex, user.email, user.username}


def _is_current_user(request: HttpRequest, user: User) -> bool:
    """Return true when the request is authenticated as the given user."""
    return request.user.is_authenticated and user.pk == request.user.pk


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


def get_selectable_users(request: HttpRequest) -> list[User]:
    """Users this browser can select between, current user first, one entry per user."""
    users: dict[str, User] = {}
    if request.user.is_authenticated:
        users[request.user.uuid.hex] = request.user
    for session in get_browser_sessions(request):
        users.setdefault(session.user.uuid.hex, session.user)
    return list(users.values())


def get_switchable_session(request: HttpRequest, user: User) -> AuthenticatedSession | None:
    """Return the browser's most recently used live session for the given user, if the
    request may switch to it without re-authenticating.

    Switching requires an authenticated request on top of the browser cookie: a browser
    that is signed out of all accounts (or an attacker holding only the browser cookie)
    has to present credentials again."""
    if not request.user.is_authenticated:
        return None
    return get_browser_sessions(request).filter(user=user).first()


def serialize_user_selection_user(
    request: HttpRequest,
    user: User,
    hint: str | None = None,
) -> dict[str, object]:
    """Serialize a selectable user for user selection surfaces."""
    is_current = _is_current_user(request, user)
    switchable = is_current or get_switchable_session(request, user) is not None
    data = {
        "uid": user.uuid.hex,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "avatar": get_avatar(user, request),
        "is_current": is_current,
        "authentication": (
            UserSelectionAuthentication.AUTHENTICATED
            if switchable
            else UserSelectionAuthentication.REMEMBERED
        ),
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
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key not in {QS_USER_UID, QS_LOGIN_HINT}
    ]
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
    if user_uid := request.GET.get(QS_USER_UID):
        context[PLAN_CONTEXT_USER_SELECTION_USER_UID] = user_uid
    if login_hint := request.GET.get(QS_LOGIN_HINT):
        context[PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT] = login_hint
    if application:
        context[PLAN_CONTEXT_APPLICATION] = application
    planner = FlowPlanner(flow)
    planner.use_cache = False
    try:
        plan = planner.plan(request, context)
    except FlowNonApplicableException:
        return None
    return plan.to_redirect(request, flow)
