"""Persistent password-login lockout state."""

from enum import Enum, auto

from django.db import transaction
from django.http import HttpRequest

from authentik.core.models import User, UserTypes
from authentik.stages.password.models import PasswordStage


class PasswordAttemptResult(Enum):
    """Result of applying the configured lockout policy to a failed attempt."""

    NOT_RECORDED = auto()
    RECORDED = auto()
    LAST_ATTEMPT = auto()
    LOCKED = auto()


def is_password_login_locked(user: User) -> bool:
    """Return whether password login is locked in the database."""
    if user.pk is None:
        return False
    return User.objects.filter(pk=user.pk, password_login_locked_at__isnull=False).exists()


def record_failed_password_attempt(
    user: User,
    stage: PasswordStage,
    request: HttpRequest | None = None,
) -> PasswordAttemptResult:
    """Record a failed password attempt and lock the user at the configured limit."""
    if stage.failed_attempts_before_lockout == 0 or user.pk is None:
        return PasswordAttemptResult.NOT_RECORDED

    with transaction.atomic():
        stored_user = (
            User.objects.exclude_anonymous().select_for_update().filter(pk=user.pk).first()
        )
        if (
            stored_user is None
            or not stored_user.is_active
            or stored_user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT
        ):
            return PasswordAttemptResult.NOT_RECORDED
        if stored_user.password_login_locked_at is not None:
            return PasswordAttemptResult.LOCKED

        failed_attempts = stored_user.password_login_failed_attempts + 1
        if failed_attempts >= stage.failed_attempts_before_lockout:
            stored_user.lock_password_login(
                request=request,
                reason="failed_attempts",
                stage=stage,
            )
            return PasswordAttemptResult.LOCKED

        User.objects.filter(pk=stored_user.pk).update(
            password_login_failed_attempts=failed_attempts
        )
        if failed_attempts == stage.failed_attempts_before_lockout - 1:
            return PasswordAttemptResult.LAST_ATTEMPT
        return PasswordAttemptResult.RECORDED


def reset_failed_password_attempts(user: User) -> bool:
    """Reset failed attempts if password authentication is still allowed."""
    if user.pk is None:
        return False

    with transaction.atomic():
        stored_user = User.objects.select_for_update().get(pk=user.pk)
        if not stored_user.is_active or stored_user.password_login_locked_at is not None:
            return False
        if stored_user.password_login_failed_attempts:
            User.objects.filter(pk=user.pk).update(password_login_failed_attempts=0)

    user.password_login_failed_attempts = 0
    return True
