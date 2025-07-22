"""Tests for SCIM group error handling and defensive programming."""

from unittest.mock import patch

from django.test import TestCase
from requests_mock import Mocker

from authentik.core.models import Group
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.models import SCIMProvider, SCIMProviderGroup


class SCIMGroupErrorHandlingTests(TestCase):
    """Test SCIM group client error handling"""

    def setUp(self):
        self.provider = SCIMProvider.objects.create(
            name="test", base_url="https://localhost", token="token"
        )
        self.client = SCIMGroupClient(self.provider)

    @Mocker()
    def test_patch_compare_users_request_failure(self, mock: Mocker):
        """Test handling of request failures in patch_compare_users"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        # Simulate request failure
        mock.get("https://localhost/Groups/123", status_code=500)

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        # Should handle the error gracefully and return without crashing
        result = self.client.patch_compare_users(group)
        self.assertIsNone(result)

    @Mocker()
    def test_patch_compare_users_invalid_response_type(self, mock: Mocker):
        """Test handling of non-dict responses"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        # Return a string instead of expected dict
        mock.get("https://localhost/Groups/123", text="invalid response")

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        result = self.client.patch_compare_users(group)
        self.assertIsNone(result)

    @Mocker()
    def test_patch_compare_users_invalid_members_type(self, mock: Mocker):
        """Test handling of non-list members data"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.get(
            "https://localhost/Groups/123",
            json={
                "id": "123",
                "members": "invalid_members_data",  # Should be list
                "displayName": "TestGroup",
            },
        )

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        # Should handle gracefully and continue with empty members list
        with patch.object(self.client, "_patch_chunked") as mock_patch:
            mock_patch.return_value = None
            self.client.patch_compare_users(group)
            # Should not raise an exception

    @Mocker()
    def test_patch_compare_users_invalid_member_objects(self, mock: Mocker):
        """Test handling of non-dict member objects"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.get(
            "https://localhost/Groups/123",
            json={
                "id": "123",
                "members": [
                    {"value": "valid_member", "display": "Valid"},
                    "invalid_member_object",  # Should be dict
                    {"value": "another_valid", "display": "Another"},
                ],
                "displayName": "TestGroup",
            },
        )

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        # Should skip invalid members but process valid ones
        with patch.object(self.client, "_patch_chunked") as mock_patch:
            mock_patch.return_value = None
            self.client.patch_compare_users(group)
            # Should not raise an exception

    @Mocker()
    def test_patch_compare_users_member_value_conversion_error(self, mock: Mocker):
        """Test handling of errors during member value conversion"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.get(
            "https://localhost/Groups/123",
            json={
                "id": "123",
                "members": [
                    {"value": 456, "display": "User456"},  # Integer value
                ],
                "displayName": "TestGroup",
            },
        )

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        # Mock ensure_string_id to raise an exception
        with patch("authentik.providers.scim.clients.groups.ensure_string_id") as mock_convert:
            mock_convert.side_effect = Exception("Conversion error")

            with patch.object(self.client, "_patch_chunked") as mock_patch:
                mock_patch.return_value = None
                self.client.patch_compare_users(group)
                # Should handle the conversion error gracefully

    @Mocker()
    def test_patch_compare_users_validation_error(self, mock: Mocker):
        """Test handling of pydantic validation errors"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.get(
            "https://localhost/Groups/123",
            json={
                "id": "123",
                # Missing required fields to trigger validation error
                "invalid_field": "value",
            },
        )

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        result = self.client.patch_compare_users(group)
        self.assertIsNone(result)

    @Mocker()
    def test_patch_compare_users_malformed_json_response(self, mock: Mocker):
        """Test handling of malformed JSON responses"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.get("https://localhost/Groups/123", text="malformed{json")

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        result = self.client.patch_compare_users(group)
        self.assertIsNone(result)

    @Mocker()
    def test_patch_compare_users_network_timeout(self, mock: Mocker):
        """Test handling of network timeouts"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        # Simulate network timeout
        mock.get("https://localhost/Groups/123", exc=ConnectionError("Network timeout"))

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        result = self.client.patch_compare_users(group)
        self.assertIsNone(result)

    @Mocker()
    def test_patch_compare_users_with_mixed_data_types(self, mock: Mocker):
        """Test handling of mixed valid and invalid data in the same response"""
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.get(
            "https://localhost/Groups/123",
            json={
                "id": "123",
                "members": [
                    {"value": 100, "display": "User100"},  # Integer - should convert
                    {"value": "user-101", "display": "User101"},  # String - should preserve
                    "invalid_member",  # Invalid - should skip
                    {"display": "User102"},  # Missing value - should handle
                    {"value": None, "display": "User103"},  # Null value - should handle
                ],
                "displayName": "TestGroup",
            },
        )

        group = Group.objects.create(name="testgroup")
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id="123", attributes={}
        )

        with patch.object(self.client, "_patch_chunked") as mock_patch:
            mock_patch.return_value = None
            self.client.patch_compare_users(group)
            # Should process valid members and handle invalid ones gracefully

    def test_patch_compare_users_no_scim_group(self):
        """Test behavior when SCIM group doesn't exist"""
        group = Group.objects.create(name="testgroup")

        # Should return early with warning log
        result = self.client.patch_compare_users(group)
        self.assertIsNone(result)
