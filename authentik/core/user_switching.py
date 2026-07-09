"""Helpers for the user-switching browser token cookie."""

from datetime import timedelta

from django.db import models, transaction
from django.db.models import QuerySet
from django.http.request import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from jwt import PyJWTError, decode, encode

from authentik.lib.generators import generate_id
from authentik.lib.utils.crypto import get_cookie_signing_key

TOKEN_LENGTH = 32
COOKIE_NAME = "authentik_user_switching"
COOKIE_AGE = int(timedelta(days=365).total_seconds())

_SIGNING_HASH = get_cookie_signing_key()


class UserSwitchingSession(models.Model):
    """Sessions grouped by one browser's user-switching cookie."""

    token = models.CharField(max_length=64, primary_key=True)
    current_session = models.OneToOneField(
        "authentik_core.AuthenticatedSession",
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = _("User Switching Session")
        verbose_name_plural = _("User Switching Sessions")
        default_permissions = []

    def __str__(self) -> str:
        return f"User Switching Session {self.token[:10]}"


def _activate_session(session_key: str, token: str) -> None:
    """Atomically make a login current for a browser token."""
    if not token:
        return
    from authentik.core.models import AuthenticatedSession

    with transaction.atomic():
        UserSwitchingSession.objects.get_or_create(token=token)
        switching_session = UserSwitchingSession.objects.select_for_update().get(token=token)
        AuthenticatedSession.objects.filter(pk=session_key).update(
            user_switching_session=switching_session
        )
        switching_session.current_session_id = session_key
        switching_session.save(update_fields=["current_session"])


def _generate_token() -> str:
    """Generate a new opaque user switching token."""
    return generate_id(TOKEN_LENGTH)


def _validate_token(token: str | None) -> str | None:
    """Return the token if it is a well-formed opaque token, else None."""
    if not token:
        return None
    if len(token) != TOKEN_LENGTH:
        return None
    if not token.isalnum():
        return None
    return token


def _encode_cookie(token: str) -> str:
    """Encode the opaque token as a signed cookie value."""
    return encode(
        {
            "iss": "authentik",
            "sub": "user_switching",
            "user_switching": token,
        },
        _SIGNING_HASH,
    )


def _decode_cookie(raw: str | None) -> str | None:
    """Decode and validate the signed user switching cookie."""
    if not raw:
        return None
    try:
        payload = decode(raw, _SIGNING_HASH, algorithms=["HS256"])
    except PyJWTError:
        return None
    return _validate_token(payload.get("user_switching"))


def _ensure_request_token(request: HttpRequest) -> str | None:
    """Return the request's user switching token, creating one if the session
    middleware initialized the request but no token is present yet."""
    if not hasattr(request, "user_switching_token"):
        return None
    if not request.user_switching_token:
        request.user_switching_token = _generate_token()
        request.user_switching_token_needs_update = True
    return request.user_switching_token


def _reconcile_session(request: HttpRequest) -> None:
    """Restore or add switching state for an authenticated session."""
    if not hasattr(request, "session") or not request.session.session_key:
        return
    if request.user_switching_token and not request.user_switching_token_needs_update:
        return
    from authentik.core.models import AuthenticatedSession

    authenticated_session = (
        AuthenticatedSession.objects.filter(
            session_id=request.session.session_key,
            session__expires__gt=timezone.now(),
        )
        .select_related("user_switching_session")
        .first()
    )
    if not authenticated_session:
        return
    if authenticated_session.user_switching_session_id and not request.user_switching_token:
        request.user_switching_token = authenticated_session.user_switching_session_id
        request.user_switching_token_needs_update = True
        return
    if not authenticated_session.user_switching_session_id:
        token = _ensure_request_token(request)
        if token:
            _activate_session(authenticated_session.session_id, token)


def _live_sessions(token: str) -> QuerySet:
    """Return active users' unexpired logins for a browser token."""
    from authentik.core.models import AuthenticatedSession

    return AuthenticatedSession.objects.filter(
        user_switching_session_id=token,
        session__expires__gt=timezone.now(),
        user__is_active=True,
    )
