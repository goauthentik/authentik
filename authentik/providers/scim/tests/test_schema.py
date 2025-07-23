"""SCIM Schema tests"""

from django.test import TestCase

from authentik.providers.scim.clients.schema import Group, User


class SCIMSchemaTests(TestCase):
    """SCIM Schema tests"""

    def test_group_member_integer_values_conversion(self):
        """Test that integer member values are converted to strings"""
        # Test with integer member values
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "123",
            "displayName": "Test Group",
            "members": [
                {"value": 123, "display": "User 123"},
                {"value": 456, "display": "User 456"},
                {"value": "789", "display": "User 789"},  # String value should remain unchanged
            ],
        }

        group = Group.model_validate(group_data)

        # Verify that integer values were converted to strings
        self.assertEqual(len(group.members), 3)
        self.assertEqual(group.members[0].value, "123")
        self.assertEqual(group.members[1].value, "456")
        self.assertEqual(group.members[2].value, "789")  # String value unchanged

    def test_group_member_none_values(self):
        """Test that None members are handled correctly"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "123",
            "displayName": "Test Group",
            "members": None,
        }

        group = Group.model_validate(group_data)
        self.assertIsNone(group.members)

    def test_group_member_empty_list(self):
        """Test that empty member list is handled correctly"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "123",
            "displayName": "Test Group",
            "members": [],
        }

        group = Group.model_validate(group_data)
        self.assertEqual(group.members, [])

    def test_group_member_mixed_types(self):
        """Test that mixed member types are handled correctly"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "123",
            "displayName": "Test Group",
            "members": [
                {"value": 123, "display": "User 123"},
                {"value": "456", "display": "User 456"},
                {"value": 789, "display": "User 789"},
                {"value": "abc", "display": "User abc"},
            ],
        }

        group = Group.model_validate(group_data)

        # Verify that integer values were converted to strings
        self.assertEqual(len(group.members), 4)
        self.assertEqual(group.members[0].value, "123")
        self.assertEqual(group.members[1].value, "456")
        self.assertEqual(group.members[2].value, "789")
        self.assertEqual(group.members[3].value, "abc")

    def test_group_member_no_value_field(self):
        """Test that members without value field are handled correctly"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "123",
            "displayName": "Test Group",
            "members": [
                {"display": "User 123"},
                {"value": 456, "display": "User 456"},
            ],
        }

        group = Group.model_validate(group_data)

        # Verify that only members with value field are processed
        self.assertEqual(len(group.members), 2)
        self.assertIsNone(group.members[0].value)  # No value field, should be None
        self.assertEqual(group.members[1].value, "456")  # Integer value converted to string

    def test_user_integer_id_conversion(self):
        """Test that integer user IDs are converted to strings"""
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": 123,  # Integer ID
            "userName": "testuser",
            "displayName": "Test User",
        }

        user = User.model_validate(user_data)

        # Verify that integer ID was converted to string
        self.assertEqual(user.id, "123")

    def test_user_string_id_unchanged(self):
        """Test that string user IDs remain unchanged"""
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "123",  # String ID
            "userName": "testuser",
            "displayName": "Test User",
        }

        user = User.model_validate(user_data)

        # Verify that string ID remains unchanged
        self.assertEqual(user.id, "123")

    def test_group_integer_id_conversion(self):
        """Test that integer group IDs are converted to strings"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": 456,  # Integer ID
            "displayName": "Test Group",
        }

        group = Group.model_validate(group_data)

        # Verify that integer ID was converted to string
        self.assertEqual(group.id, "456")

    def test_group_string_id_unchanged(self):
        """Test that string group IDs remain unchanged"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "456",  # String ID
            "displayName": "Test Group",
        }

        group = Group.model_validate(group_data)

        # Verify that string ID remains unchanged
        self.assertEqual(group.id, "456")
