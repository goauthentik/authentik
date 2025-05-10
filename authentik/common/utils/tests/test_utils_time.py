"""Test time utils"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from authentik.common.utils.time import timedelta_from_string, timedelta_string_validator


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
