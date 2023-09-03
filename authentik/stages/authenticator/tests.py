"""Base authenticator tests"""
from datetime import timedelta
from threading import Thread

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.utils import timezone
from freezegun import freeze_time

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.stages.authenticator import match_token, user_has_device, verify_token
from authentik.stages.authenticator.models import Device, VerifyNotAllowed


class TestThread(Thread):
    "Django testing quirk: threads have to close their DB connections."

    __test__ = False

    def run(self):
        super().run()
        connection.close()


class ThrottlingTestMixin:
    """
    Generic tests for throttled devices.

    Any concrete device implementation that uses throttling should define a
    TestCase subclass that includes this as a base class. This will help verify
    a correct integration of ThrottlingMixin.

    Subclasses are responsible for populating self.device with a device to test
    as well as implementing methods to generate tokens to test with.

    """

    device: Device

    def valid_token(self):
        """Returns a valid token to pass to our device under test."""
        raise NotImplementedError()

    def invalid_token(self):
        """Returns an invalid token to pass to our device under test."""
        raise NotImplementedError()

    #
    # Tests
    #

    def test_delay_imposed_after_fail(self):
        """Test delay imposed after fail"""
        verified1 = self.device.verify_token(self.invalid_token())
        self.assertFalse(verified1)
        verified2 = self.device.verify_token(self.valid_token())
        self.assertFalse(verified2)

    def test_delay_after_fail_expires(self):
        """Test delay after fail expires"""
        verified1 = self.device.verify_token(self.invalid_token())
        self.assertFalse(verified1)
        with freeze_time() as frozen_time:
            # With default settings initial delay is 1 second
            frozen_time.tick(delta=timedelta(seconds=1.1))
            verified2 = self.device.verify_token(self.valid_token())
            self.assertTrue(verified2)

    def test_throttling_failure_count(self):
        """Test throttling failure count"""
        self.assertEqual(self.device.throttling_failure_count, 0)
        for _ in range(0, 5):
            self.device.verify_token(self.invalid_token())
            # Only the first attempt will increase throttling_failure_count,
            # the others will all be within 1 second of first
            # and therefore not count as attempts.
            self.assertEqual(self.device.throttling_failure_count, 1)

    def test_verify_is_allowed(self):
        """Test verify allowed"""
        # Initially should be allowed
        verify_is_allowed1, data1 = self.device.verify_is_allowed()
        self.assertEqual(verify_is_allowed1, True)
        self.assertEqual(data1, None)

        # After failure, verify is not allowed
        with freeze_time():
            self.device.verify_token(self.invalid_token())
            verify_is_allowed2, data2 = self.device.verify_is_allowed()
            self.assertEqual(verify_is_allowed2, False)
            self.assertEqual(
                data2,
                {
                    "reason": VerifyNotAllowed.N_FAILED_ATTEMPTS,
                    "failure_count": 1,
                    "locked_until": timezone.now() + timezone.timedelta(seconds=1),
                },
            )

        # After a successful attempt, should be allowed again
        with freeze_time() as frozen_time:
            frozen_time.tick(delta=timedelta(seconds=1.1))
            self.device.verify_token(self.valid_token())

            verify_is_allowed3, data3 = self.device.verify_is_allowed()
            self.assertEqual(verify_is_allowed3, True)
            self.assertEqual(data3, None)


@override_settings(OTP_STATIC_THROTTLE_FACTOR=0)
class APITestCase(TestCase):
    """Test API"""

    def setUp(self):
        self.alice = create_test_admin_user("alice")
        self.bob = create_test_admin_user("bob")
        device = self.alice.staticdevice_set.create()
        self.valid = generate_id(length=16)
        device.token_set.create(token=self.valid)

    def test_user_has_device(self):
        """Test user_has_device"""
        with self.subTest(user="anonymous"):
            self.assertFalse(user_has_device(AnonymousUser()))
        with self.subTest(user="alice"):
            self.assertTrue(user_has_device(self.alice))
        with self.subTest(user="bob"):
            self.assertFalse(user_has_device(self.bob))

    def test_verify_token(self):
        """Test verify_token"""
        device = self.alice.staticdevice_set.first()

        verified = verify_token(self.alice, device.persistent_id, "bogus")
        self.assertIsNone(verified)

        verified = verify_token(self.alice, device.persistent_id, self.valid)
        self.assertIsNotNone(verified)

    def test_match_token(self):
        """Test match_token"""
        verified = match_token(self.alice, "bogus")
        self.assertIsNone(verified)

        verified = match_token(self.alice, self.valid)
        self.assertEqual(verified, self.alice.staticdevice_set.first())


@override_settings(OTP_STATIC_THROTTLE_FACTOR=0)
class ConcurrencyTestCase(TransactionTestCase):
    """Test concurrent verifications"""

    def setUp(self):
        self.alice = create_test_admin_user("alice")
        self.bob = create_test_admin_user("bob")
        self.valid = generate_id(length=16)
        for user in [self.alice, self.bob]:
            device = user.staticdevice_set.create()
            device.token_set.create(token=self.valid)

    def test_verify_token(self):
        """Test verify_token in a thread"""

        class VerifyThread(Thread):
            """Verifier thread"""

            __test__ = False

            def __init__(self, user, device_id, token):
                super().__init__()

                self.user = user
                self.device_id = device_id
                self.token = token

                self.verified = None

            def run(self):
                self.verified = verify_token(self.user, self.device_id, self.token)
                connection.close()

        device = self.alice.staticdevice_set.get()
        threads = [VerifyThread(device.user, device.persistent_id, self.valid) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sum(1 for t in threads if t.verified is not None), 1)

    def test_match_token(self):
        """Test match_token in a thread"""

        class VerifyThread(Thread):
            """Verifier thread"""

            __test__ = False

            def __init__(self, user, token):
                super().__init__()

                self.user = user
                self.token = token

                self.verified = None

            def run(self):
                self.verified = match_token(self.user, self.token)
                connection.close()

        threads = [VerifyThread(self.alice, self.valid) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sum(1 for t in threads if t.verified is not None), 1)
