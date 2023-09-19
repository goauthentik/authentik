"""Test TOTP API"""
from time import time
from urllib.parse import parse_qs, urlsplit

from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.stages.authenticator.tests import TestCase, ThrottlingTestMixin
from authentik.stages.authenticator_totp.models import TOTPDevice


class AuthenticatorTOTPStage(APITestCase):
    """Test TOTP API"""

    def test_api_delete(self):
        """Test api delete"""
        user = User.objects.create(username="foo")
        self.client.force_login(user)
        dev = TOTPDevice.objects.create(user=user)
        response = self.client.delete(
            reverse("authentik_api:totpdevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)


class TOTPDeviceMixin:
    """
    A TestCase helper that gives us a TOTPDevice to work with.
    """

    # The next ten tokens
    tokens = [
        179225,
        656163,
        839400,
        154567,
        346912,
        471576,
        45675,
        101397,
        491039,
        784503,
    ]

    # pylint: disable=invalid-name
    def setUp(self):
        """
        Create a device at the fourth time step. The current token is 154567.
        """
        self.alice = create_test_admin_user("alice", email="alice@example.com")
        self.device = self.alice.totpdevice_set.create(
            key="2a2bbba1092ffdd25a328ad1a0a5f5d61d7aacc4",
            step=30,
            t0=int(time() - (30 * 3)),
            digits=6,
            tolerance=0,
            drift=0,
        )


@override_settings(
    OTP_TOTP_SYNC=False,
    OTP_TOTP_THROTTLE_FACTOR=0,
)
class TOTPTest(TOTPDeviceMixin, TestCase):
    """TOTP tests"""

    def test_default_key(self):
        """Ensure default_key is valid"""
        device = self.alice.totpdevice_set.create()

        # Make sure we can decode the key.
        _ = device.bin_key

    def test_single(self):
        """Test single token"""
        results = [self.device.verify_token(token) for token in self.tokens]

        self.assertEqual(results, [False] * 3 + [True] + [False] * 6)

    def test_tolerance(self):
        """Test tolerance"""
        self.device.tolerance = 1
        results = [self.device.verify_token(token) for token in self.tokens]

        self.assertEqual(results, [False] * 2 + [True] * 3 + [False] * 5)

    def test_drift(self):
        """Test drift"""
        self.device.tolerance = 1
        self.device.drift = -1
        results = [self.device.verify_token(token) for token in self.tokens]

        self.assertEqual(results, [False] * 1 + [True] * 3 + [False] * 6)

    def test_sync_drift(self):
        """Test sync drift"""
        self.device.tolerance = 2
        with self.settings(OTP_TOTP_SYNC=True):
            valid = self.device.verify_token(self.tokens[5])

        self.assertTrue(valid)
        self.assertEqual(self.device.drift, 2)

    def test_no_reuse(self):
        """Test reuse"""
        verified1 = self.device.verify_token(self.tokens[3])
        verified2 = self.device.verify_token(self.tokens[3])

        self.assertEqual(self.device.last_t, 3)
        self.assertTrue(verified1)
        self.assertFalse(verified2)

    def test_config_url(self):
        """Test config_url"""
        with override_settings(OTP_TOTP_ISSUER=None):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "totp")
        self.assertEqual(parsed.path, "/alice")
        self.assertIn("secret", params)
        self.assertNotIn("issuer", params)

    def test_config_url_issuer(self):
        """Test config_url issuer"""
        with override_settings(OTP_TOTP_ISSUER="example.com"):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "totp")
        self.assertEqual(parsed.path, "/example.com%3Aalice")
        self.assertIn("secret", params)
        self.assertIn("issuer", params)
        self.assertEqual(params["issuer"][0], "example.com")

    def test_config_url_issuer_spaces(self):
        """Test config_url issuer with spaces"""
        with override_settings(OTP_TOTP_ISSUER="Very Trustworthy Source"):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "totp")
        self.assertEqual(parsed.path, "/Very%20Trustworthy%20Source%3Aalice")
        self.assertIn("secret", params)
        self.assertIn("issuer", params)
        self.assertEqual(params["issuer"][0], "Very Trustworthy Source")

    def test_config_url_issuer_method(self):
        """Test config_url issuer method"""
        with override_settings(OTP_TOTP_ISSUER=lambda d: d.user.email):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "totp")
        self.assertEqual(parsed.path, "/alice%40example.com%3Aalice")
        self.assertIn("secret", params)
        self.assertIn("issuer", params)
        self.assertEqual(params["issuer"][0], "alice@example.com")

    def test_config_url_image(self):
        """Test config_url with image"""
        image_url = "https://test.invalid/square.png"

        with override_settings(OTP_TOTP_ISSUER=None, OTP_TOTP_IMAGE=image_url):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "totp")
        self.assertEqual(parsed.path, "/alice")
        self.assertIn("secret", params)
        self.assertEqual(params["image"][0], image_url)


@override_settings(
    OTP_TOTP_THROTTLE_FACTOR=1,
)
class ThrottlingTestCase(TOTPDeviceMixin, ThrottlingTestMixin, TestCase):
    """Test TOTP Throttling"""

    def valid_token(self):
        return self.tokens[3]

    def invalid_token(self):
        return -1
