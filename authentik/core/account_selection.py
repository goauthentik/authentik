"""Helpers for remembering browser-local account choices."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.signing import BadSignature, SignatureExpired, dumps, loads
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import http_date

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.models import AuthenticatedSession, User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    FlowPlanner,
)
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.lib.utils.urls import is_url_absolute
from authentik.policies.engine import PolicyEngine
from authentik.root.middleware import SessionMiddleware

COOKIE_NAME_KNOWN_ACCOUNTS = "authentik_accounts"
KNOWN_ACCOUNTS_MAX = 5
KNOWN_ACCOUNTS_AGE = int(timedelta(days=365).total_seconds())
QS_ACCOUNT_UID = "account_uid"
QS_ADD_ACCOUNT = "add_account"
PLAN_CONTEXT_ACCOUNT_SWITCH_SESSION_KEY = "account_switch_session_key"
PLAN_CONTEXT_ACCOUNT_SWITCH_USER_UID = "account_switch_user_uid"
PLAN_CONTEXT_ACCOUNT_SELECTION_USER_UID = "account_selection_user_uid"
PLAN_CONTEXT_ACCOUNT_SELECTION_LOGIN_HINT = "account_selection_login_hint"


@dataclass(frozen=True)
class KnownAccount:
    """Browser-local account reference."""

    uid: str
    session_key: str


def _coerce_known_account(raw_account: object) -> KnownAccount | None:
    """Parse account cookie entries."""
    if not isinstance(raw_account, dict):
        return None
    uid = raw_account.get("uid")
    session_key = raw_account.get("session")
    if not isinstance(uid, str) or not isinstance(session_key, str):
        return None
    return KnownAccount(uid=uid, session_key=session_key)


def get_known_accounts(request: HttpRequest) -> list[KnownAccount]:
    """Return remembered accounts from the signed browser cookie."""
    raw_accounts = request.COOKIES.get(COOKIE_NAME_KNOWN_ACCOUNTS)
    if not raw_accounts:
        return []
    try:
        accounts = loads(raw_accounts, max_age=KNOWN_ACCOUNTS_AGE)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return []
    if not isinstance(accounts, list):
        return []
    known_accounts = []
    seen_accounts = set()
    for raw_account in accounts:
        account = _coerce_known_account(raw_account)
        if not account or account.uid in seen_accounts:
            continue
        seen_accounts.add(account.uid)
        known_accounts.append(account)
        if len(known_accounts) >= KNOWN_ACCOUNTS_MAX:
            break
    return known_accounts


def get_known_account_users(
    request: HttpRequest,
    extra_accounts: Iterable[str] = (),
) -> list[User]:
    """Return active accounts with a live remembered session in browser-local order."""
    known_account_ids = list(
        dict.fromkeys([*extra_accounts, *(account.uid for account in get_known_accounts(request))])
    )[:KNOWN_ACCOUNTS_MAX]
    live_account_ids = set(get_live_account_sessions(request).keys())
    live_account_ids.update(extra_accounts)
    known_account_ids = [
        account_id for account_id in known_account_ids if account_id in live_account_ids
    ]
    users = User.objects.filter(uuid__in=known_account_ids, is_active=True).exclude_anonymous()
    users_by_id = {user.uuid.hex: user for user in users}
    return [
        users_by_id[account_id]
        for account_id in known_account_ids
        if account_id in users_by_id
    ]


def get_live_account_sessions(request: HttpRequest) -> dict[str, AuthenticatedSession]:
    """Return live remembered sessions keyed by user UUID."""
    known_accounts = get_known_accounts(request)
    session_keys = [account.session_key for account in known_accounts]
    if not session_keys:
        return {}
    active_users = User.objects.filter(is_active=True).exclude_anonymous()
    sessions = (
        AuthenticatedSession.objects.select_related("session", "user")
        .filter(session__session_key__in=session_keys, session__expires__gt=timezone.now())
        .filter(user__in=active_users)
    )
    sessions_by_key = {
        session.session.session_key: session for session in sessions if session.session
    }
    live_sessions = {}
    for account in known_accounts:
        session = sessions_by_key.get(account.session_key)
        if not session or session.user.uuid.hex != account.uid:
            continue
        live_sessions.setdefault(account.uid, session)
    return live_sessions


def get_known_account_session(
    request: HttpRequest,
    account_uid: str,
) -> AuthenticatedSession | None:
    """Return a live remembered session matching a selected account."""
    for session in get_live_account_sessions(request).values():
        if session.user.uuid.hex == account_uid:
            return session
    return None


def get_live_account_session(
    account_uid: str,
    session_key: str,
) -> AuthenticatedSession | None:
    """Return a live authenticated session for a specific account."""
    active_users = User.objects.filter(uuid=account_uid, is_active=True).exclude_anonymous()
    return (
        AuthenticatedSession.objects.select_related("session", "user")
        .filter(
            session__session_key=session_key,
            session__expires__gt=timezone.now(),
            user__in=active_users,
        )
        .first()
    )


def set_session_key_cookie(
    response: HttpResponse,
    request: HttpRequest,
    session_key: str,
    user: User | AnonymousUser,
    expires_at: datetime,
) -> HttpResponse:
    """Set the browser's primary session cookie to a session key."""
    secure = SessionMiddleware.is_secure(request)
    same_site = "None" if secure else "Lax"
    max_age = max(0, int((expires_at - timezone.now()).total_seconds()))
    expires = http_date(time() + max_age)
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        SessionMiddleware.encode_session(session_key, user),
        max_age=max_age,
        expires=expires,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path=settings.SESSION_COOKIE_PATH,
        secure=secure,
        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
        samesite=same_site,
    )
    return response


def set_session_cookie(
    response: HttpResponse,
    request: HttpRequest,
    session: AuthenticatedSession,
) -> HttpResponse:
    """Set the browser's primary session cookie to an existing authenticated session."""
    return set_session_key_cookie(
        response,
        request,
        session.session.session_key,
        session.user,
        session.session.expires,
    )


def get_next_url(request: HttpRequest, next_arg_name: str) -> str:
    """Return a safe next URL from the current request."""
    next_url = request.GET.get(next_arg_name)
    if not next_url or is_url_absolute(next_url):
        return reverse("authentik_core:root-redirect")
    return next_url


def start_fresh_session(response: HttpResponse, request: HttpRequest) -> HttpResponse:
    """Set the browser's primary session cookie to a new anonymous session."""
    fresh_session = request.session.__class__(
        last_user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
    fresh_session.create()
    return set_session_key_cookie(
        response,
        request,
        fresh_session.session_key,
        AnonymousUser(),
        fresh_session.get_expiry_date(),
    )


def get_account_selection_flow(request: HttpRequest) -> Flow | None:
    """Return the brand account selection flow or the first applicable fallback."""
    brand_flow = getattr(request.brand, "flow_account_selection", None)
    if brand_flow:
        return brand_flow
    flows = Flow.objects.filter(designation=FlowDesignation.ACCOUNT_SELECTION).order_by("slug")
    for flow in flows:
        engine = PolicyEngine(flow, request.user, request)
        engine.build()
        if engine.result.passing:
            return flow
    return None


def append_account_selection_hint(url: str, user: User) -> str:
    """Append account selection hints when returning to OAuth authorize."""
    parts = urlsplit(url)
    if parts.path != reverse("authentik_providers_oauth2:authorize"):
        return url
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query[QS_ACCOUNT_UID] = user.uuid.hex
    query[QS_LOGIN_HINT] = user.email or user.username
    return urlunsplit(parts._replace(query=urlencode(query)))


def set_account_selection_context(
    flow_context: dict,
    user: User,
    session_key: str,
) -> None:
    """Store the selected account on a flow plan for later verification and switching."""
    flow_context[PLAN_CONTEXT_PENDING_USER] = user
    flow_context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = user.email or user.username
    flow_context[PLAN_CONTEXT_ACCOUNT_SWITCH_USER_UID] = user.uuid.hex
    flow_context[PLAN_CONTEXT_ACCOUNT_SWITCH_SESSION_KEY] = session_key
    if PLAN_CONTEXT_REDIRECT in flow_context:
        flow_context[PLAN_CONTEXT_REDIRECT] = append_account_selection_hint(
            flow_context[PLAN_CONTEXT_REDIRECT],
            user,
        )


def start_account_selection_flow_response(
    request: HttpRequest,
    next_url: str,
    application=None,
) -> HttpResponse | None:
    """Start the brand account selection flow."""
    flow = get_account_selection_flow(request)
    if not flow:
        return None
    context = {
        PLAN_CONTEXT_REDIRECT: next_url,
    }
    if account_uid := request.GET.get(QS_ACCOUNT_UID):
        context[PLAN_CONTEXT_ACCOUNT_SELECTION_USER_UID] = account_uid
    if login_hint := request.GET.get(QS_LOGIN_HINT):
        context[PLAN_CONTEXT_ACCOUNT_SELECTION_LOGIN_HINT] = login_hint
    if application:
        context[PLAN_CONTEXT_APPLICATION] = application
    planner = FlowPlanner(flow)
    planner.use_cache = False
    try:
        plan = planner.plan(request, context)
    except FlowNonApplicableException:
        return None
    return plan.to_redirect(request, flow)


def start_additional_account_login_response(request: HttpRequest) -> HttpResponse | None:
    """Start authentication in a fresh session so the current account stays switchable."""
    if request.GET.get(QS_ADD_ACCOUNT) != "true":
        return None
    query = request.GET.copy()
    query.pop(QS_ADD_ACCOUNT, None)
    url = reverse("authentik_flows:default-authentication")
    if query:
        url = f"{url}?{query.urlencode()}"
    return start_fresh_session(redirect(url), request)


def account_selection_authentication_response(
    request: HttpRequest,
    next_arg_name: str,
) -> HttpResponse | None:
    """Handle browser-local account actions on the default authentication route."""
    response = start_additional_account_login_response(request)
    if response is not None:
        return response
    if request.GET.get(QS_ACCOUNT_UID) or request.GET.get(QS_LOGIN_HINT):
        return start_account_selection_flow_response(request, get_next_url(request, next_arg_name))
    return None


def remember_account(response: HttpResponse, request: HttpRequest, user: User) -> HttpResponse:
    """Remember a user as selectable on this browser without authenticating them."""
    session_key = request.session.session_key
    if not session_key:
        return response
    live_account_ids = set(get_live_account_sessions(request))
    existing_accounts = [
        account
        for account in get_known_accounts(request)
        if account.uid != user.uuid.hex and account.uid in live_account_ids
    ]
    accounts = [
        KnownAccount(uid=user.uuid.hex, session_key=session_key),
        *existing_accounts,
    ][:KNOWN_ACCOUNTS_MAX]
    payload = [{"uid": account.uid, "session": account.session_key} for account in accounts]
    cookie_kwargs = {
        "path": settings.SESSION_COOKIE_PATH,
        "domain": settings.SESSION_COOKIE_DOMAIN,
        "secure": settings.SESSION_COOKIE_SECURE,
        "httponly": True,
        "samesite": settings.SESSION_COOKIE_SAMESITE,
    }
    if request.session.get_expire_at_browser_close():
        response.set_cookie(COOKIE_NAME_KNOWN_ACCOUNTS, dumps(payload), **cookie_kwargs)
    else:
        response.set_cookie(
            COOKIE_NAME_KNOWN_ACCOUNTS,
            dumps(payload),
            max_age=KNOWN_ACCOUNTS_AGE,
            **cookie_kwargs,
        )
    return response
