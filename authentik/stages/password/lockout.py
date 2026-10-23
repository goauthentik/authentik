"""Password-lock enforcement shared by standalone and embedded password stages."""

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.http import HttpRequest

from authentik.core.models import SERVICE_ACCOUNT_TYPES, User
from authentik.core.signals import login_failed
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.stages.password.models import PasswordDevice, PasswordStage

PLAN_CONTEXT_LOCKED_ATTEMPTS = "goauthentik.io/stages/password/locked_attempts"


@dataclass(frozen=True)
class PasswordLockoutResult:
    """Authentication result and optional messages for the current flow."""

    user: User | None = None
    last_attempt: bool = False
    lockout_reached: bool = False


class PasswordLockoutBase:
    """Enforce existing locks even without Enterprise or a valid license."""

    def __init__(self, password_stage: PasswordStage, request: HttpRequest):
        self.password_stage = password_stage
        self.request = request

    def apply(
        self, pending_user: User, user: User | None, context: dict[str, Any]
    ) -> PasswordLockoutResult:
        if pending_user.pk is None or pending_user.type in SERVICE_ACCOUNT_TYPES:
            return PasswordLockoutResult(user)
        with transaction.atomic():
            device = PasswordDevice.objects.select_for_update().filter(user=pending_user).first()
            if device is None:
                return PasswordLockoutResult(user)
            if device.locked:
                # A lock may have been set while a backend was authenticating.
                if user is not None:
                    login_failed.send(
                        sender=__name__,
                        credentials={"username": pending_user.username},
                        request=self.request,
                        stage=self.password_stage,
                    )
                return PasswordLockoutResult(lockout_reached=self._count_locked(context))
            if user is not None:
                if device.failed_attempts:
                    PasswordDevice.objects.filter(pk=device.pk).update(failed_attempts=0)
                return PasswordLockoutResult(user)
            return self.record_failure(device)

    def record_failure(self, device: PasswordDevice) -> PasswordLockoutResult:
        """Without Enterprise, authentication does not create new locks."""
        return PasswordLockoutResult()

    def _count_locked(self, context: dict[str, Any]) -> bool:
        """Show the lockout message only after this flow reaches its attempt limit."""
        key = f"{PLAN_CONTEXT_LOCKED_ATTEMPTS}/{self.password_stage.pk}"
        attempts = context.get(key, 0) + 1
        context[key] = attempts
        threshold = (
            self.password_stage.failed_attempts_before_lockout
            or self.password_stage.failed_attempts_before_cancel
        )
        return threshold > 0 and attempts >= threshold


class PasswordLockout(
    ConditionalInheritance("authentik.enterprise.stages.password.lockout.PasswordLockoutMixin"),
    PasswordLockoutBase,
):
    """Enforce password locks, with optional licensed failure counting."""
