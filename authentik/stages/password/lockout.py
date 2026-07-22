"""Persistent password-login failure and lockout state."""

from enum import Enum, auto
from typing import Any

from django.db import transaction
from django.http import HttpRequest
from django.utils.timezone import now

from authentik.core.models import User, UserPasswordLoginState, UserTypes
from authentik.events.models import Event, EventAction


class PasswordAuthenticationStatus(Enum):
    """Outcome of password authentication after applying the lockout policy."""

    AUTHENTICATED = auto()
    INVALID = auto()
    LAST_ATTEMPT = auto()
    LOCKED = auto()


def _user_for_update(user: User) -> User | None:
    """Return the persisted user while holding the lockout serialization lock."""
    if user.pk is None:
        return None
    return User.objects.exclude_anonymous().select_for_update().filter(pk=user.pk).first()


def _record_transition(
    user: User,
    action: EventAction,
    request: HttpRequest | None,
    **event_context: Any,
) -> None:
    """Record a password-login lock transition."""
    event = Event.new(action, **event_context)
    if request:
        event.from_http(request, user=user)
    else:
        event.set_user(user).save()


def is_password_login_locked(user: User) -> bool:
    """Return whether password login is currently locked."""
    if user.pk is None:
        return False
    return UserPasswordLoginState.objects.filter(
        user_id=user.pk,
        user__is_active=True,
        locked_at__isnull=False,
    ).exists()


def lock_password_login(
    user: User,
    request: HttpRequest | None = None,
    **event_context: Any,
) -> None:
    """Lock password login and record the transition exactly once."""
    with transaction.atomic():
        stored_user = _user_for_update(user)
        if (
            stored_user is None
            or not stored_user.is_active
            or stored_user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT
        ):
            return

        state, _ = UserPasswordLoginState.objects.get_or_create(user=stored_user)
        if state.locked_at is not None:
            return
        state.failed_attempts = 0
        state.locked_at = now()
        state.save(update_fields=("failed_attempts", "locked_at"))
        _record_transition(
            stored_user,
            EventAction.PASSWORD_LOGIN_LOCKED,
            request,
            **event_context,
        )


def unlock_password_login(
    user: User,
    request: HttpRequest | None = None,
    **event_context: Any,
) -> None:
    """Clear password-login failures and record an unlock transition when locked."""
    with transaction.atomic():
        stored_user = _user_for_update(user)
        if stored_user is None:
            return

        state = UserPasswordLoginState.objects.filter(user=stored_user).first()
        if state is None:
            return
        was_locked = state.locked_at is not None
        state.delete()
        if was_locked:
            _record_transition(
                stored_user,
                EventAction.PASSWORD_LOGIN_UNLOCKED,
                request,
                **event_context,
            )


def record_failed_password_attempt(
    user: User,
    threshold: int,
    request: HttpRequest | None = None,
    **event_context: Any,
) -> PasswordAuthenticationStatus:
    """Record one failure and return the resulting authentication status."""
    if threshold == 0:
        return PasswordAuthenticationStatus.INVALID

    with transaction.atomic():
        stored_user = _user_for_update(user)
        if (
            stored_user is None
            or not stored_user.is_active
            or stored_user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT
        ):
            return PasswordAuthenticationStatus.INVALID

        state, _ = UserPasswordLoginState.objects.get_or_create(user=stored_user)
        if state.locked_at is not None:
            return PasswordAuthenticationStatus.LOCKED

        state.failed_attempts += 1
        if state.failed_attempts >= threshold:
            state.failed_attempts = 0
            state.locked_at = now()
            state.save(update_fields=("failed_attempts", "locked_at"))
            _record_transition(
                stored_user,
                EventAction.PASSWORD_LOGIN_LOCKED,
                request,
                **event_context,
            )
            return PasswordAuthenticationStatus.LOCKED

        state.save(update_fields=("failed_attempts",))
        if state.failed_attempts == threshold - 1:
            return PasswordAuthenticationStatus.LAST_ATTEMPT
        return PasswordAuthenticationStatus.INVALID


def complete_successful_password_attempt(user: User) -> PasswordAuthenticationStatus:
    """Clear failures if password authentication is still allowed."""
    with transaction.atomic():
        stored_user = _user_for_update(user)
        if stored_user is None or not stored_user.is_active:
            return PasswordAuthenticationStatus.INVALID

        state = UserPasswordLoginState.objects.filter(user=stored_user).first()
        if state and state.locked_at is not None:
            return PasswordAuthenticationStatus.LOCKED
        if state:
            state.delete()
        return PasswordAuthenticationStatus.AUTHENTICATED
