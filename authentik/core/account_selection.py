"""Helpers for remembering browser-local account choices."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import time

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
from authentik.lib.utils.urls import is_url_absolute
from authentik.root.middleware import SessionMiddleware

COOKIE_NAME_KNOWN_ACCOUNTS = "authentik_accounts"
KNOWN_ACCOUNTS_MAX = 5
KNOWN_ACCOUNTS_AGE = int(timedelta(days=365).total_seconds())
QS_ACCOUNT_UID = "account_uid"
QS_ADD_ACCOUNT = "add_account"


@dataclass(frozen=True)
class KnownAccount:
    """Browser-local account reference."""

    uid: str
    session_key: str | None = None


def _coerce_known_account(raw_account: object) -> KnownAccount | None:
    """Parse account cookie entries, accepting the legacy UUID-only format."""
    if isinstance(raw_account, str):
        return KnownAccount(uid=raw_account)
    if not isinstance(raw_account, dict):
        return None
    uid = raw_account.get("uid")
    session_key = raw_account.get("session")
    if not isinstance(uid, str):
        return None
    if session_key is not None and not isinstance(session_key, str):
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
    known_accounts = [account for account in get_known_accounts(request) if account.session_key]
    session_keys = [account.session_key for account in known_accounts if account.session_key]
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
    account_uid: str | None = None,
    login_hint: str | None = None,
) -> AuthenticatedSession | None:
    """Return a live remembered session matching a selected account."""
    if not account_uid and not login_hint:
        return None
    for session in get_live_account_sessions(request).values():
        if account_uid and session.user.uuid.hex != account_uid:
            continue
        if login_hint and login_hint not in {session.user.email, session.user.username}:
            continue
        return session
    return None


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


def switch_known_account_response(
    request: HttpRequest,
    next_arg_name: str,
) -> HttpResponse | None:
    """Switch to a live browser-local account session before starting authentication."""
    account_session = get_known_account_session(
        request,
        account_uid=request.GET.get(QS_ACCOUNT_UID),
        login_hint=request.GET.get(QS_LOGIN_HINT),
    )
    if not account_session:
        return None
    next_url = request.GET.get(next_arg_name)
    if not next_url or is_url_absolute(next_url):
        next_url = reverse("authentik_core:root-redirect")
    return set_session_cookie(redirect(next_url), request, account_session)


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
    return switch_known_account_response(request, next_arg_name)


def remember_account(response: HttpResponse, request: HttpRequest, user: User) -> HttpResponse:
    """Remember a user as selectable on this browser without authenticating them."""
    live_account_ids = set(get_live_account_sessions(request))
    existing_accounts = [
        account
        for account in get_known_accounts(request)
        if account.uid != user.uuid.hex and account.uid in live_account_ids
    ]
    accounts = [
        KnownAccount(uid=user.uuid.hex, session_key=request.session.session_key),
        *existing_accounts,
    ][:KNOWN_ACCOUNTS_MAX]
    payload = [
        {"uid": account.uid, "session": account.session_key}
        if account.session_key
        else account.uid
        for account in accounts
    ]
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
