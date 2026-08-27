"""Enterprise password lockout policy."""

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.http import HttpRequest
from django.utils.timezone import now

from authentik.core.models import User, UserTypes
from authentik.enterprise.license import LicenseKey
from authentik.events.models import Event, EventAction
from authentik.sources.kerberos.models import UserKerberosSourceConnection
from authentik.sources.ldap.models import LDAP_DISTINGUISHED_NAME
from authentik.stages.password import BACKEND_KERBEROS, BACKEND_LDAP
from authentik.stages.password.models import PasswordDevice, PasswordStage

PLAN_CONTEXT_LOCKED_ATTEMPTS = "goauthentik.io/stages/password/locked_attempts"

SERVICE_ACCOUNT_TYPES = (UserTypes.SERVICE_ACCOUNT, UserTypes.INTERNAL_SERVICE_ACCOUNT)


@dataclass(frozen=True)
class PasswordLockoutResult:
    """Outcome of the lockout policy for one authentication attempt."""

    user: User | None = None
    # The user is one failed attempt away from being locked.
    last_attempt: bool = False
    # The flow has reached the point where it ends with the stage's lockout message.
    lockout_reached: bool = False


class PasswordLockout:
    """Lock a user's password after repeated failed authentication attempts."""

    def __init__(self, password_stage: PasswordStage, request: HttpRequest):
        self.password_stage = password_stage
        self.request = request

    @staticmethod
    def is_available() -> bool:
        """Return whether Enterprise password lockout can currently run."""
        return LicenseKey.cached_summary().status.is_valid

    @staticmethod
    def lock(user: User, request: HttpRequest):
        """Lock a password on behalf of an administrator."""
        with transaction.atomic():
            device = PasswordDevice.objects.select_for_update().filter(user=user).first()
            if device is None or device.locked:
                return
            device.failed_attempts = 0
            device.locked_at = now()
            device.save()
        Event.new(
            EventAction.PASSWORD_LOCKED, affected_user=user, reason="administrator"
        ).from_http(request)

    def apply(
        self, pending_user: User, user: User | None, context: dict[str, Any]
    ) -> PasswordLockoutResult:
        """Apply the lockout policy to one authentication attempt.

        `user` is the result of authenticating `pending_user`'s credentials; a locked
        password refuses authentication even when those credentials were correct."""
        if not self.is_available() or pending_user.pk is None:
            return PasswordLockoutResult(user)

        threshold = self.password_stage.failed_attempts_before_lockout
        newly_locked = False
        with transaction.atomic():
            device = PasswordDevice.objects.select_for_update().filter(user=pending_user).first()
            if device is None:
                return PasswordLockoutResult(user)
            if device.locked:
                return PasswordLockoutResult(None, lockout_reached=self._count_locked(context))
            if user is not None:
                if device.failed_attempts:
                    device.failed_attempts = 0
                    device.save()
                return PasswordLockoutResult(user)
            if threshold == 0 or pending_user.type in SERVICE_ACCOUNT_TYPES:
                return PasswordLockoutResult(None)
            if self._uses_external_password(pending_user):
                # A failed LDAP or Kerberos result might be an upstream outage.
                return PasswordLockoutResult(None)

            device.failed_attempts += 1
            if device.failed_attempts >= threshold:
                device.failed_attempts = 0
                device.locked_at = now()
                newly_locked = True
            device.save()

        if newly_locked:
            Event.new(
                EventAction.PASSWORD_LOCKED,
                affected_user=pending_user,
                reason="failed_attempts",
                threshold=threshold,
            ).from_http(self.request)
            return PasswordLockoutResult(None, lockout_reached=True)
        return PasswordLockoutResult(None, last_attempt=device.failed_attempts == threshold - 1)

    def _uses_external_password(self, user: User) -> bool:
        """Return whether the user's password is verified by an external system."""
        backends = set(self.password_stage.backends)
        if BACKEND_LDAP in backends and LDAP_DISTINGUISHED_NAME in user.attributes:
            return True
        return (
            BACKEND_KERBEROS in backends
            and UserKerberosSourceConnection.objects.filter(user=user).exists()
        )

    def _count_locked(self, context: dict[str, Any]) -> bool:
        """Count an attempt against a locked password and return whether to reveal the lock.

        The lock is only revealed once the flow would have locked (or cancelled) anyway,
        so an already-locked account is not distinguishable any earlier."""
        key = f"{PLAN_CONTEXT_LOCKED_ATTEMPTS}/{self.password_stage.pk}"
        attempts = context.get(key, 0) + 1
        context[key] = attempts
        threshold = (
            self.password_stage.failed_attempts_before_lockout
            or self.password_stage.failed_attempts_before_cancel
        )
        return threshold > 0 and attempts >= threshold
