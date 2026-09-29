"""Test time utils"""

from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from authentik.lib.utils.time import fqdn_rand, timedelta_from_string, timedelta_string_validator


class TestTimeUtils(TestCase):
    """Test time-utils"""

    def test_valid(self):
        """Test valid expression"""
        expr = "hours=3;minutes=1"
        expected = timedelta(hours=3, minutes=1)
        self.assertEqual(timedelta_from_string(expr), expected)

    def test_invalid(self):
        """Test invalid expression"""
        with self.assertRaises(ValueError):
            timedelta_from_string("foo")
        with self.assertRaises(ValueError):
            timedelta_from_string("bar=baz")

    def test_validation(self):
        """Test Django model field validator"""
        with self.assertRaises(ValidationError):
            timedelta_string_validator("foo")

    @patch("authentik.lib.utils.time.socket.gethostname", return_value="test-host")
    def test_fqdn_rand_deterministic(self, _gethostname):
        """Test schedule entropy is stable for a hostname and task"""
        self.assertEqual(fqdn_rand("test-task"), fqdn_rand("test-task"))

    @patch("authentik.lib.utils.time.socket.gethostname", return_value="test-host")
    def test_fqdn_rand_range(self, _gethostname):
        """Test schedule entropy remains within the requested range"""
        self.assertGreaterEqual(fqdn_rand("test-task"), 0)
        self.assertLess(fqdn_rand("test-task"), 60)
        self.assertGreaterEqual(fqdn_rand("test-task", 7), 0)
        self.assertLess(fqdn_rand("test-task", 7), 7)

    def test_fqdn_rand_does_not_resolve_hostname(self):
        """Test schedule entropy does not depend on DNS resolver functions"""
        with (
            patch("authentik.lib.utils.time.socket.gethostname", return_value="test-host"),
            patch(
                "authentik.lib.utils.time.socket.getfqdn",
                side_effect=AssertionError("getfqdn must not be called"),
            ) as getfqdn,
            patch(
                "authentik.lib.utils.time.socket.getaddrinfo",
                side_effect=AssertionError("getaddrinfo must not be called"),
            ) as getaddrinfo,
            patch(
                "authentik.lib.utils.time.socket.gethostbyname",
                side_effect=AssertionError("gethostbyname must not be called"),
            ) as gethostbyname,
            patch(
                "authentik.lib.utils.time.socket.gethostbyaddr",
                side_effect=AssertionError("gethostbyaddr must not be called"),
            ) as gethostbyaddr,
        ):
            self.assertEqual(fqdn_rand("test-task"), fqdn_rand("test-task"))

        getfqdn.assert_not_called()
        getaddrinfo.assert_not_called()
        gethostbyname.assert_not_called()
        gethostbyaddr.assert_not_called()
