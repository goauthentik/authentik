"""Tests for authentik.lib.utils.convert"""

from django.test import TestCase

from authentik.lib.utils.convert import ensure_string_id


class TestConvertUtils(TestCase):
    """Test convert utility functions"""

    def test_ensure_string_id_integer(self):
        """Test that integers are converted to strings"""
        self.assertEqual(ensure_string_id(123), "123")
        self.assertEqual(ensure_string_id(0), "0")
        self.assertEqual(ensure_string_id(-42), "-42")

    def test_ensure_string_id_string(self):
        """Test that strings are returned as-is"""
        self.assertEqual(ensure_string_id("456"), "456")
        self.assertEqual(ensure_string_id("test_id"), "test_id")
        self.assertEqual(ensure_string_id(""), "")

    def test_ensure_string_id_none(self):
        """Test that None is returned as None"""
        self.assertIsNone(ensure_string_id(None))

    def test_ensure_string_id_other_types(self):
        """Test behavior with other data types"""
        # Float should be returned as-is (not converted)
        self.assertEqual(ensure_string_id(12.34), 12.34)
        # List should be returned as-is
        self.assertEqual(ensure_string_id([1, 2, 3]), [1, 2, 3])
        # Dict should be returned as-is
        test_dict = {"id": 123}
        self.assertEqual(ensure_string_id(test_dict), test_dict)
        # Boolean should be returned as-is
        self.assertEqual(ensure_string_id(True), True)
        self.assertEqual(ensure_string_id(False), False)

    def test_scim_use_case_simulation(self):
        """Test the specific SCIM use case that this function addresses"""
        # Simulate SCIM response with integer IDs (as reported in issue #15533)
        scim_response = {
            "id": 72,
            "members": [
                {"value": 53, "display": "USER53"},
                {"value": 54, "display": "USER54"},
                {"value": 55, "display": "USER55"},
            ]
        }

        # Test group ID conversion
        converted_id = ensure_string_id(scim_response["id"])
        self.assertEqual(converted_id, "72")
        self.assertIsInstance(converted_id, str)

        # Test member value conversion
        for member in scim_response["members"]:
            converted_value = ensure_string_id(member["value"])
            self.assertIsInstance(converted_value, str)
            self.assertEqual(converted_value, str(member["value"]))
