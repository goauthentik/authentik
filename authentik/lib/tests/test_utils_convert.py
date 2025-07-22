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

    def test_ensure_string_id_boolean(self):
        """Test behavior with boolean values (booleans are subclass of int in Python)"""
        # Boolean values are converted to strings because isinstance(True, int) is True
        self.assertEqual(ensure_string_id(True), "True")
        self.assertEqual(ensure_string_id(False), "False")
        self.assertIsInstance(ensure_string_id(True), str)
        self.assertIsInstance(ensure_string_id(False), str)

    def test_scim_use_case_simulation(self):
        """Test the specific SCIM use case that this function addresses"""
        # Simulate SCIM response with integer IDs (as reported in issue #15533)
        scim_response = {
            "id": 72,
            "members": [
                {"value": 53, "display": "USER53"},
                {"value": 54, "display": "USER54"},
                {"value": 55, "display": "USER55"},
            ],
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

    def test_edge_cases_and_boundary_conditions(self):
        """Test edge cases and boundary conditions for robustness"""
        # Test large integers
        large_int = 999999999999999999
        self.assertEqual(ensure_string_id(large_int), str(large_int))

        # Test negative integers
        neg_int = -123456
        self.assertEqual(ensure_string_id(neg_int), str(neg_int))

        # Test zero
        self.assertEqual(ensure_string_id(0), "0")

        # Test string that looks like integer
        self.assertEqual(ensure_string_id("123"), "123")

        # Test empty string
        self.assertEqual(ensure_string_id(""), "")

        # Test whitespace string
        self.assertEqual(ensure_string_id("  "), "  ")

    def test_type_preservation_for_non_integers(self):
        """Test that non-integer types are preserved exactly"""
        # Complex types should be returned unchanged
        complex_dict = {"nested": {"id": 123, "values": [1, 2, 3]}}
        result = ensure_string_id(complex_dict)
        self.assertIs(result, complex_dict)  # Same object reference

        # Float precision should be preserved
        float_val = 3.14159265359
        result = ensure_string_id(float_val)
        self.assertEqual(result, float_val)
        self.assertIsInstance(result, float)

    def test_real_world_scim_scenarios(self):
        """Test real-world SCIM scenarios that would use this function"""
        # Scenario 1: Creating user with integer ID response
        user_response = {"id": 12345, "userName": "testuser"}
        converted_id = ensure_string_id(user_response["id"])
        self.assertEqual(converted_id, "12345")

        # Scenario 2: Group with mixed member ID types
        group_members = [
            {"value": 100, "display": "User100"},  # Integer
            {"value": "user-101", "display": "User101"},  # String
            {"value": 102, "display": "User102"},  # Integer
        ]

        for member in group_members:
            original_value = member["value"]
            converted_value = ensure_string_id(original_value)

            if isinstance(original_value, int):
                self.assertEqual(converted_value, str(original_value))
                self.assertIsInstance(converted_value, str)
            else:
                self.assertEqual(converted_value, original_value)

        # Scenario 3: Batch processing multiple IDs
        id_batch = [1, 2, "string-3", 4, None, "5"]
        expected = ["1", "2", "string-3", "4", None, "5"]

        for original, expected_result in zip(id_batch, expected, strict=False):
            result = ensure_string_id(original)
            self.assertEqual(result, expected_result)
