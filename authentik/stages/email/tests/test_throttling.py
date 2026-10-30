"""Tests for the email attempt window shared with email OTP."""

from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.utils.timezone import now

from authentik.stages.email.throttling import email_cache_key, email_is_rate_limited


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class TestEmailRateLimit(SimpleTestCase):
    """Test window calculations without database I/O from the default PostgreSQL cache."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.email = "otp@example.com"

    def test_defaults_and_address_isolation(self):
        for _ in range(5):
            self.assertIsNone(email_is_rate_limited(self.email))
        self.assertEqual(email_is_rate_limited("OTP@example.com"), 5)
        self.assertIsNone(email_is_rate_limited("other@example.com"))
        self.assertNotIn(self.email, email_cache_key(self.email))

    def test_custom_policy_and_expiry_boundary(self):
        timestamp = now()
        with patch("authentik.stages.email.throttling.now", return_value=timestamp):
            self.assertIsNone(email_is_rate_limited(self.email, 1, "seconds=90"))
            self.assertEqual(email_is_rate_limited(self.email, 1, "seconds=90"), 2)
        with patch(
            "authentik.stages.email.throttling.now",
            return_value=timestamp + timedelta(seconds=31),
        ):
            self.assertEqual(email_is_rate_limited(self.email, 1, "seconds=90"), 1)
        with patch(
            "authentik.stages.email.throttling.now",
            return_value=timestamp + timedelta(seconds=90),
        ):
            self.assertIsNone(email_is_rate_limited(self.email, 1, "seconds=90"))

    def test_shared_history(self):
        self.assertIsNone(email_is_rate_limited(self.email, 1, "minutes=5"))
        for _ in range(4):
            self.assertIsNone(email_is_rate_limited(self.email))
        self.assertEqual(email_is_rate_limited(self.email, 1, "minutes=5"), 5)

    def test_short_policy_preserves_long_policy_history_and_ttl(self):
        timestamp = now()
        with (
            patch("authentik.stages.email.throttling.now", return_value=timestamp),
            patch("time.time", return_value=timestamp.timestamp()),
        ):
            self.assertIsNone(email_is_rate_limited(self.email, 1, "hours=1"))
        with (
            patch(
                "authentik.stages.email.throttling.now",
                return_value=timestamp + timedelta(minutes=6),
            ),
            patch("time.time", return_value=(timestamp + timedelta(minutes=6)).timestamp()),
        ):
            self.assertIsNone(email_is_rate_limited(self.email))
        with (
            patch(
                "authentik.stages.email.throttling.now",
                return_value=timestamp + timedelta(minutes=12),
            ),
            patch("time.time", return_value=(timestamp + timedelta(minutes=12)).timestamp()),
        ):
            self.assertEqual(email_is_rate_limited(self.email, 1, "hours=1"), 48)

    def test_rejected_long_policy_also_preserves_history(self):
        timestamp = now()
        with (
            patch("authentik.stages.email.throttling.now", return_value=timestamp),
            patch("time.time", return_value=timestamp.timestamp()),
        ):
            self.assertIsNone(email_is_rate_limited(self.email))
            self.assertEqual(email_is_rate_limited(self.email, 1, "hours=1"), 60)
        with (
            patch(
                "authentik.stages.email.throttling.now",
                return_value=timestamp + timedelta(minutes=6),
            ),
            patch("time.time", return_value=(timestamp + timedelta(minutes=6)).timestamp()),
        ):
            self.assertEqual(email_is_rate_limited(self.email, 1, "hours=1"), 54)

    def test_rejected_retries_do_not_extend_lockout(self):
        timestamp = now()
        with (
            patch("authentik.stages.email.throttling.now", return_value=timestamp),
            patch("time.time", return_value=timestamp.timestamp()),
        ):
            for _ in range(5):
                self.assertIsNone(email_is_rate_limited(self.email))
        for minutes in range(1, 5):
            retry_time = timestamp + timedelta(minutes=minutes)
            with (
                patch("authentik.stages.email.throttling.now", return_value=retry_time),
                patch("time.time", return_value=retry_time.timestamp()),
            ):
                self.assertEqual(email_is_rate_limited(self.email), 5 - minutes)
        boundary = timestamp + timedelta(minutes=5)
        with (
            patch("authentik.stages.email.throttling.now", return_value=boundary),
            patch("time.time", return_value=boundary.timestamp()),
        ):
            self.assertIsNone(email_is_rate_limited(self.email))
