"""Persistent password-login failure and lockout state."""

from datetime import datetime
from typing import Any

from django.db import transaction
from django.http import HttpRequest
from django.utils.timezone import now

from authentik.core.models import User, UserTypes
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.stages.password.models import UserPasswordLoginState
from authentik.events.models import Event, EventAction
from authentik.flows.models import Stage
from authentik.sources.kerberos.models import UserKerberosSourceConnection
from authentik.sources.ldap.models import LDAP_DISTINGUISHED_NAME
from authentik.stages.password import BACKEND_KERBEROS, BACKEND_LDAP
from authentik.stages.password.auth import (
    PasswordAuthenticationResult,
    PasswordAuthenticationStatus,
    authenticate,
)
from authentik.stages.password.models import PasswordStage


def is_password_lockout_enabled() -> bool:
    """Return whether password login lockout can currently be enforced."""
    return LicenseKey.cached_summary().status.is_valid


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


def password_login_locked_at(user: User) -> datetime | None:
    """Return the active password login lock timestamp for a user."""
    if not is_password_lockout_enabled() or user.pk is None:
        return None
    state = getattr(user, "password_login_state", None)
    return state.locked_at if state else None


def is_password_login_locked(user: User) -> bool:
    """Return whether an active user currently has an enforceable password-login lock."""
    if not is_password_lockout_enabled() or user.pk is None:
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
    if not is_password_lockout_enabled():
        return
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
    if not is_password_lockout_enabled() or threshold == 0:
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
            return PasswordAuthenticationStatus.NEWLY_LOCKED

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


def authenticate_password(
    request: HttpRequest,
    password_stage: PasswordStage,
    pending_user: User,
    password: str | None,
    event_stage: Stage,
) -> PasswordAuthenticationResult:
    """Authenticate a password and atomically apply the enterprise lockout policy."""
    if not is_password_lockout_enabled():
        user = authenticate(
            request,
            password_stage.backends,
            event_stage,
            username=pending_user.username,
            password=password,
        )
        return PasswordAuthenticationResult(
            (
                PasswordAuthenticationStatus.AUTHENTICATED
                if user
                else PasswordAuthenticationStatus.INVALID
            ),
            user,
        )

    user = authenticate(
        request,
        password_stage.backends,
        event_stage,
        username=pending_user.username,
        password=password,
    )
    if user is None:
        if is_password_login_locked(pending_user):
            return PasswordAuthenticationResult(PasswordAuthenticationStatus.LOCKED)
        backends = set(password_stage.backends)
        uses_ldap = BACKEND_LDAP in backends and LDAP_DISTINGUISHED_NAME in pending_user.attributes
        uses_kerberos = (
            BACKEND_KERBEROS in backends
            and UserKerberosSourceConnection.objects.filter(user=pending_user).exists()
        )
        if uses_ldap or uses_kerberos:
            return PasswordAuthenticationResult(PasswordAuthenticationStatus.INVALID)
        status = record_failed_password_attempt(
            pending_user,
            password_stage.failed_attempts_before_lockout,
            request,
            reason="failed_attempts",
            stage=password_stage,
        )
        return PasswordAuthenticationResult(status)

    status = complete_successful_password_attempt(user)
    if status is not PasswordAuthenticationStatus.AUTHENTICATED:
        return PasswordAuthenticationResult(status)
    return PasswordAuthenticationResult(status, user)
