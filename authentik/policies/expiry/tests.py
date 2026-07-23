"""Password expiry policy tests."""

from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from authentik.core.models import User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.expiry.models import PasswordExpiryPolicy
from authentik.policies.types import PolicyRequest
from authentik.stages.password.models import PasswordDevice


class TestPasswordExpiryPolicy(TestCase):
    """Password expiry behavior for password devices."""

    def test_user_without_password_device_passes(self):
        """Users without a local password have nothing to expire."""
        user = User.objects.create(username=generate_id(), name=generate_id())
        policy = PasswordExpiryPolicy.objects.create(name=generate_id(), days=30)

        self.assertTrue(policy.passes(PolicyRequest(user)).passing)

    def test_expired_password_device_becomes_unusable(self):
        """Expiring a password keeps its device and makes the hash unusable."""
        user = create_test_user()
        PasswordDevice.objects.filter(user=user).update(
            password_change_date=now() - timedelta(days=31)
        )
        user.refresh_from_db()
        policy = PasswordExpiryPolicy.objects.create(name=generate_id(), days=30)

        self.assertFalse(policy.passes(PolicyRequest(user)).passing)

        user.refresh_from_db()
        self.assertTrue(PasswordDevice.objects.filter(user=user).exists())
        self.assertFalse(user.has_usable_password())
