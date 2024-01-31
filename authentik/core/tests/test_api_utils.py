"""Test API Utils"""

from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from authentik.core.api.utils import is_dict


class TestAPIUtils(APITestCase):
    """Test API Utils"""

    def test_is_dict(self):
        """Test is_dict"""
        self.assertIsNone(is_dict({}))
        with self.assertRaises(ValidationError):
            is_dict("foo")
