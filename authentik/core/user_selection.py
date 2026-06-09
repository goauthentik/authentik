"""Helpers for browser-local user selection."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.signing import BadSignature, SignatureExpired, dumps, loads
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.models import User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_REDIRECT, FlowPlanner
from authentik.lib.avatars import get_avatar
from authentik.policies.engine import PolicyEngine

COOKIE_NAME_KNOWN_USERS = "authentik_users"
KNOWN_USERS_MAX = 5
KNOWN_USERS_AGE = int(timedelta(days=365).total_seconds())
QS_USER_UID = "user_uid"
PLAN_CONTEXT_USER_SELECTION_USER_UID = "user_selection_user_uid"
PLAN_CONTEXT_USER_SELECTION_LOGIN_HINT = "user_selection_login_hint"


class UserSelectionAuthentication(StrEnum):
    """How strongly the current browser request is authenticated as a remembered user."""

    AUTHENTICATED = "authenticated"
    REMEMBERED = "remembered"


@dataclass(frozen=True)
class KnownUser:
    """Browser-local user reference."""

    uid: str


def _coerce_known_user(raw_user: object) -> KnownUser | None:
    """Parse remembered-user cookie entries."""
    if not isinstance(raw_user, dict):
        return None
    uid = raw_user.get("uid")
    if not isinstance(uid, str):
        return None
    return KnownUser(uid=uid)


def user_matches_hint(user: User, hint: str) -> bool:
    """Check whether a user matches the supplied login hint."""
    return hint in {user.uuid.hex, user.email, user.username}


def _is_current_user(request: HttpRequest, user: User) -> bool:
    """Return true when the request is authenticated as the given user."""
    return (
        request.user.is_authenticated
        and not isinstance(request.user, AnonymousUser)
        and user.pk == request.user.pk
    )


def serialize_user_selection_user(
    request: HttpRequest,
    user: User,
    hint: str | None = None,
) -> dict[str, object]:
    """Serialize a browser-local user for user selection surfaces."""
    is_current = _is_current_user(request, user)
    data = {
        "uid": user.uuid.hex,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "avatar": get_avatar(user, request),
        "is_current": is_current,
        "authentication": (
            UserSelectionAuthentication.AUTHENTICATED
            if is_current
            else UserSelectionAuthentication.REMEMBERED
        ),
    }
    if hint is not None:
        data["is_hint"] = bool(hint and user_matches_hint(user, hint))
    return data


def get_known_users(request: HttpRequest) -> list[KnownUser]:
    """Return remembered users from the signed browser cookie."""
    raw_users = request.COOKIES.get(COOKIE_NAME_KNOWN_USERS)
    if not raw_users:
        return []
    try:
        users = loads(raw_users, max_age=KNOWN_USERS_AGE)
    except BadSignature, SignatureExpired, TypeError, ValueError:
        return []
    if not isinstance(users, list):
        return []
    known_users = []
    seen_users = set()
    for raw_user in users:
        user = _coerce_known_user(raw_user)
        if not user or user.uid in seen_users:
            continue
        seen_users.add(user.uid)
        known_users.append(user)
        if len(known_users) >= KNOWN_USERS_MAX:
            break
    return known_users


def get_user_selection_users(
    request: HttpRequest,
    extra_users: Iterable[str] = (),
) -> list[User]:
    """Return active remembered users in browser-local order."""
    known_user_ids = list(
        dict.fromkeys([*extra_users, *(user.uid for user in get_known_users(request))])
    )[:KNOWN_USERS_MAX]
    users = User.objects.filter(uuid__in=known_user_ids, is_active=True).exclude_anonymous()
    users_by_id = {user.uuid.hex: user for user in users}
    return [users_by_id[user_id] for user_id in known_user_ids if user_id in users_by_id]


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


def remember_user(response: HttpResponse, request: HttpRequest, user: User) -> HttpResponse:
    """Remember a user as selectable on this browser without authenticating as them."""
    existing_users = [
        known_user for known_user in get_known_users(request) if known_user.uid != user.uuid.hex
    ]
    users = [KnownUser(uid=user.uuid.hex), *existing_users][:KNOWN_USERS_MAX]
    payload = [{"uid": known_user.uid} for known_user in users]
    cookie_kwargs = {
        "path": settings.SESSION_COOKIE_PATH,
        "domain": settings.SESSION_COOKIE_DOMAIN,
        "secure": settings.SESSION_COOKIE_SECURE,
        "httponly": True,
        "samesite": settings.SESSION_COOKIE_SAMESITE,
    }
    if request.session.get_expire_at_browser_close():
        response.set_cookie(COOKIE_NAME_KNOWN_USERS, dumps(payload), **cookie_kwargs)
    else:
        response.set_cookie(
            COOKIE_NAME_KNOWN_USERS,
            dumps(payload),
            max_age=KNOWN_USERS_AGE,
            **cookie_kwargs,
        )
    return response
