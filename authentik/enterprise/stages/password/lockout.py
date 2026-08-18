"""Enterprise password lockout policy."""

from django.db import transaction
from django.http import HttpRequest
from django.utils.timezone import now

from authentik.core.models import User, UserTypes
from authentik.enterprise.license import LicenseKey
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
from authentik.stages.password.models import PasswordDevice, PasswordStage


def is_password_lockout_available() -> bool:
    """Return whether Enterprise password lockout can currently run."""
    return LicenseKey.cached_summary().status.is_valid


def is_password_locked(user: User) -> bool:
    """Return whether the user's password device is locked."""
    if not is_password_lockout_available() or user.pk is None:
        return False
    return PasswordDevice.objects.filter(user=user, locked_at__isnull=False).exists()


def record_lock_event(
    user: User,
    request: HttpRequest,
    **context: object,
) -> None:
    """Record a password lock while keeping the affected user separate from the actor."""
    Event.new(EventAction.PASSWORD_LOCKED, affected_user=user, **context).from_http(request)


def lock_password(user: User, request: HttpRequest) -> None:
    """Lock a password and clear earlier failed attempts."""
    with transaction.atomic():
        device = PasswordDevice.objects.select_for_update().filter(user=user).first()
        if device is None or device.locked:
            return
        device.failed_attempts = 0
        device.locked_at = now()
        device.save(update_fields=("failed_attempts", "locked_at"))
    record_lock_event(user, request, reason="administrator")


def record_failed_password_attempt(
    user: User,
    threshold: int,
    request: HttpRequest,
) -> PasswordAuthenticationStatus:
    """Record one failed attempt and return the resulting lockout status."""
    if threshold == 0 or user.pk is None:
        return PasswordAuthenticationStatus.INVALID
    if not user.is_active or user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
        return PasswordAuthenticationStatus.INVALID

    with transaction.atomic():
        device = PasswordDevice.objects.select_for_update().filter(user=user).first()
        if device is None:
            return PasswordAuthenticationStatus.INVALID
        if device.locked:
            return PasswordAuthenticationStatus.LOCKED

        device.failed_attempts += 1
        if device.failed_attempts >= threshold:
            device.failed_attempts = 0
            device.locked_at = now()
            device.save(update_fields=("failed_attempts", "locked_at"))
            status = PasswordAuthenticationStatus.NEWLY_LOCKED
        else:
            device.save(update_fields=("failed_attempts",))
            status = (
                PasswordAuthenticationStatus.LAST_ATTEMPT
                if device.failed_attempts == threshold - 1
                else PasswordAuthenticationStatus.INVALID
            )

    if status is PasswordAuthenticationStatus.NEWLY_LOCKED:
        record_lock_event(user, request, reason="failed_attempts", threshold=threshold)
    return status


def complete_successful_password_attempt(user: User) -> PasswordAuthenticationStatus:
    """Clear earlier failures unless another request already locked the password."""
    with transaction.atomic():
        device = PasswordDevice.objects.select_for_update().filter(user=user).first()
        if device is None:
            return PasswordAuthenticationStatus.AUTHENTICATED
        if device.locked:
            return PasswordAuthenticationStatus.LOCKED
        if device.failed_attempts:
            device.failed_attempts = 0
            device.save(update_fields=("failed_attempts",))
        return PasswordAuthenticationStatus.AUTHENTICATED


def uses_external_password(user: User, password_stage: PasswordStage) -> bool:
    """Return whether a failed backend result might be an upstream outage."""
    backends = set(password_stage.backends)
    uses_ldap = BACKEND_LDAP in backends and LDAP_DISTINGUISHED_NAME in user.attributes
    uses_kerberos = (
        BACKEND_KERBEROS in backends
        and UserKerberosSourceConnection.objects.filter(user=user).exists()
    )
    return uses_ldap or uses_kerberos


def authenticate_password(
    request: HttpRequest,
    password_stage: PasswordStage,
    pending_user: User,
    password: str | None,
    event_stage: Stage,
) -> PasswordAuthenticationResult:
    """Authenticate a password and atomically apply the lockout policy."""
    user = authenticate(
        request,
        password_stage.backends,
        event_stage,
        username=pending_user.username,
        password=password,
    )
    if not is_password_lockout_available():
        return PasswordAuthenticationResult(
            (
                PasswordAuthenticationStatus.AUTHENTICATED
                if user
                else PasswordAuthenticationStatus.INVALID
            ),
            user,
        )

    if user is None:
        if is_password_locked(pending_user):
            return PasswordAuthenticationResult(PasswordAuthenticationStatus.LOCKED)
        if uses_external_password(pending_user, password_stage):
            return PasswordAuthenticationResult(PasswordAuthenticationStatus.INVALID)
        status = record_failed_password_attempt(
            pending_user,
            password_stage.failed_attempts_before_lockout,
            request,
        )
        return PasswordAuthenticationResult(status)

    status = complete_successful_password_attempt(user)
    if status is not PasswordAuthenticationStatus.AUTHENTICATED:
        return PasswordAuthenticationResult(status)
    return PasswordAuthenticationResult(status, user)
