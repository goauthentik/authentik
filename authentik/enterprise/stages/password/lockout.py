"""Licensed policy for creating password locks after failed attempts."""

from django.utils.timezone import now

from authentik.core.models import User
from authentik.enterprise.license import LicenseKey
from authentik.events.models import Event, EventAction
from authentik.sources.kerberos.models import UserKerberosSourceConnection
from authentik.sources.ldap.models import LDAP_DISTINGUISHED_NAME, LDAPSource
from authentik.stages.password import BACKEND_KERBEROS, BACKEND_LDAP
from authentik.stages.password.lockout import PasswordLockoutResult
from authentik.stages.password.models import PasswordDevice


class PasswordLockoutMixin:
    """Count failures while the caller holds the password device's row lock."""

    def record_failure(self, device: PasswordDevice) -> PasswordLockoutResult:
        if not LicenseKey.cached_summary().status.is_valid:
            return PasswordLockoutResult()
        devices = PasswordDevice.objects.filter(pk=device.pk)
        threshold = self.password_stage.failed_attempts_before_lockout
        if threshold == 0 or self._uses_external_password(device.user):
            return PasswordLockoutResult()

        attempts = device.failed_attempts + 1
        if attempts < threshold:
            devices.update(failed_attempts=attempts)
            return PasswordLockoutResult(last_attempt=attempts == threshold - 1)

        devices.update(failed_attempts=0, locked_at=now())
        Event.new(
            EventAction.AUTHENTICATOR_LOCKED,
            affected_user=device.user,
            authenticator=device,
            reason="failed_attempts",
            threshold=threshold,
        ).from_http(self.request)
        return PasswordLockoutResult(lockout_reached=True)

    def _uses_external_password(self, user: User) -> bool:
        """Return whether the user's password is verified by an external system."""
        backends = self.password_stage.backends
        if (
            BACKEND_LDAP in backends
            and LDAP_DISTINGUISHED_NAME in user.attributes
            and LDAPSource.objects.filter(enabled=True).exists()
        ):
            return True
        return (
            BACKEND_KERBEROS in backends
            and UserKerberosSourceConnection.objects.filter(
                user=user, source__enabled=True
            ).exists()
        )
