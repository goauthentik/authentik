"""Enterprise password login lockout tests."""

from unittest.mock import PropertyMock, patch

from django.test import TestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.stages.password.lockout import (
    lock_password_login,
    record_failed_password_attempt,
    unlock_password_login,
)
from authentik.enterprise.stages.password.models import UserPasswordLoginState
from authentik.enterprise.tests import enterprise_test
from authentik.stages.password.auth import PasswordAuthenticationStatus


class TestPasswordLockoutLicense(TestCase):
    """Test licensing behavior for password login lockout."""

    @enterprise_test()
    def test_lock_transitions_clear_cached_password_login_state(self) -> None:
        """Lock transitions remain visible on the User instance passed to the helper."""
        user = create_test_user()
        self.assertIsNone(user.password_login_locked_at)

        lock_password_login(user)
        self.assertIsNotNone(user.password_login_locked_at)

        unlock_password_login(user)
        self.assertIsNone(user.password_login_locked_at)

    @patch(
        "authentik.enterprise.models.LicenseUsageStatus.is_valid",
        PropertyMock(return_value=False),
    )
    def test_lockout_is_not_enforced_without_license(self) -> None:
        """Do not create automatic or administrative locks without a valid license."""
        user = create_test_user()

        status = record_failed_password_attempt(user, threshold=1)
        lock_password_login(user)

        self.assertIs(status, PasswordAuthenticationStatus.INVALID)
        self.assertFalse(UserPasswordLoginState.objects.filter(user=user).exists())
