"""Tests for SCIM user client error handling."""

from unittest.mock import patch

from django.test import TestCase
from requests_mock import Mocker

from authentik.core.models import User
from authentik.lib.sync.outgoing.exceptions import ObjectExistsSyncException, StopSync
from authentik.providers.scim.clients.users import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider, SCIMProviderUser


class SCIMUserErrorHandlingTests(TestCase):
    """Test SCIM user client error handling"""

    def setUp(self):
        self.provider = SCIMProvider.objects.create(
            name="test", base_url="https://localhost", token="token"  # nosec B106
        )
        self.client = SCIMUserClient(self.provider)

    def test_ensure_string_id_integration_in_users(self):
        """Test that ensure_string_id is properly integrated in user client"""
        from authentik.lib.utils.convert import ensure_string_id

        # Test the various ID scenarios that can occur in user processing
        test_cases = [
            (123, "123"),  # Integer user ID
            ("user-456", "user-456"),  # String user ID
            (None, None),  # None ID (should be handled by validation)
            (0, "0"),  # Zero ID
            (-1, "-1"),  # Negative ID
        ]

        for original_id, expected_result in test_cases:
            result = ensure_string_id(original_id)
            self.assertEqual(result, expected_result)

    @Mocker()
    def test_create_user_with_integer_response_id(self, mock: Mocker):
        """Test user creation when SCIM provider returns integer ID"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.post(
            "https://localhost/Users",
            json={
                "id": 12345,  # Integer ID from provider
                "userName": "testuser",
                "emails": [{"primary": True, "value": "test@example.com"}],
            },
        )

        user = User.objects.create(username="testuser", email="test@example.com")

        # Should handle integer ID conversion gracefully
        result = self.client.create(user)
        self.assertIsInstance(result, SCIMProviderUser)
        self.assertEqual(result.scim_id, "12345")  # Should be converted to string

    @Mocker()
    def test_create_user_missing_id_in_response(self, mock: Mocker):
        """Test handling of missing ID in SCIM response"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.post(
            "https://localhost/Users",
            json={
                # Missing ID field
                "userName": "testuser",
                "emails": [{"primary": True, "value": "test@example.com"}],
            },
        )

        user = User.objects.create(username="testuser", email="test@example.com")

        # Should raise StopSync due to missing ID
        with self.assertRaises(StopSync) as cm:
            self.client.create(user)

        self.assertIn("missing or invalid", str(cm.exception))

    @Mocker()
    def test_create_user_empty_id_in_response(self, mock: Mocker):
        """Test handling of empty string ID in SCIM response"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.post(
            "https://localhost/Users",
            json={
                "id": "",  # Empty string ID
                "userName": "testuser",
                "emails": [{"primary": True, "value": "test@example.com"}],
            },
        )

        user = User.objects.create(username="testuser", email="test@example.com")

        # Should raise StopSync due to empty ID
        with self.assertRaises(StopSync) as cm:
            self.client.create(user)

        self.assertIn("missing or invalid", str(cm.exception))

    @Mocker()
    def test_create_user_existing_search_with_integer_id(self, mock: Mocker):
        """Test user creation when search returns existing user with integer ID"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        # First, simulate ObjectExistsSyncException
        mock.post("https://localhost/Users", status_code=409)

        # Then simulate successful search with integer ID
        mock.get(
            "https://localhost/Users",
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ListResponse"],
                "totalResults": 1,
                "Resources": [
                    {
                        "id": 98765,  # Integer ID from search
                        "userName": "testuser",
                        "emails": [{"primary": True, "value": "test@example.com"}],
                    }
                ],
            },
        )

        user = User.objects.create(username="testuser", email="test@example.com")

        # Should handle integer ID conversion in search results
        result = self.client.create(user)
        self.assertIsInstance(result, SCIMProviderUser)
        self.assertEqual(result.scim_id, "98765")  # Should be converted to string

    @Mocker()
    def test_create_user_search_no_results(self, mock: Mocker):
        """Test behavior when search returns no results after conflict"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        # First, simulate ObjectExistsSyncException
        mock.post("https://localhost/Users", status_code=409)

        # Then simulate empty search results
        mock.get(
            "https://localhost/Users",
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ListResponse"],
                "totalResults": 0,
                "Resources": [],
            },
        )

        user = User.objects.create(username="testuser", email="test@example.com")

        # Should re-raise the original ObjectExistsSyncException
        with self.assertRaises(ObjectExistsSyncException):
            self.client.create(user)

    @Mocker()
    def test_create_user_search_multiple_results(self, mock: Mocker):
        """Test behavior when search returns multiple results"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        # First, simulate ObjectExistsSyncException
        mock.post("https://localhost/Users", status_code=409)

        # Then simulate multiple search results
        mock.get(
            "https://localhost/Users",
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ListResponse"],
                "totalResults": 2,
                "Resources": [
                    {"id": "111", "userName": "testuser1"},
                    {"id": "222", "userName": "testuser2"},
                ],
            },
        )

        user = User.objects.create(username="testuser", email="test@example.com")

        # Should re-raise the original ObjectExistsSyncException
        with self.assertRaises(ObjectExistsSyncException):
            self.client.create(user)

    def test_create_user_with_conversion_error(self):
        """Test handling of ID conversion errors"""
        # This test focuses on the error handling around ensure_string_id
        with patch("authentik.providers.scim.clients.users.ensure_string_id") as mock_convert:
            mock_convert.side_effect = Exception("Conversion error")

            # Create a mock response that would normally work
            mock_response = {"id": 123, "userName": "test"}

            user = User.objects.create(username="testuser", email="test@example.com")

            # The conversion error should propagate
            with patch.object(self.client, "_request") as mock_request:
                mock_request.return_value = mock_response

                with self.assertRaises(Exception) as cm:
                    self.client.create(user)

                self.assertIn("Conversion error", str(cm.exception))

    def test_edge_cases_with_special_id_values(self):
        """Test edge cases with special ID values"""
        from authentik.lib.utils.convert import ensure_string_id

        # Test various edge cases that might appear in SCIM responses
        edge_cases = [
            (0, "0"),  # Zero
            (-1, "-1"),  # Negative
            (True, "True"),  # Boolean (subclass of int)
            (False, "False"),  # Boolean false
        ]

        for original, expected in edge_cases:
            result = ensure_string_id(original)
            self.assertEqual(result, expected)
            if original is not None:
                self.assertIsInstance(result, str)

    @Mocker()
    def test_user_creation_workflow_comprehensive(self, mock: Mocker):
        """Test comprehensive user creation workflow with various scenarios"""
        mock.get("https://localhost/ServiceProviderConfig", json={})

        # Test successful creation with integer ID
        mock.post(
            "https://localhost/Users",
            [
                {  # First call - integer ID
                    "json": {"id": 555, "userName": "user1"},
                    "status_code": 200,
                },
                {  # Second call - string ID
                    "json": {"id": "user-666", "userName": "user2"},
                    "status_code": 200,
                },
            ],
        )

        # Test user 1 with integer ID
        user1 = User.objects.create(username="user1", email="user1@test.com")
        result1 = self.client.create(user1)
        self.assertEqual(result1.scim_id, "555")

        # Test user 2 with string ID
        user2 = User.objects.create(username="user2", email="user2@test.com")
        result2 = self.client.create(user2)
        self.assertEqual(result2.scim_id, "user-666")
