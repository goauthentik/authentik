"""SCIM Group tests"""

from json import loads

from django.test import TestCase
from jsonschema import validate
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider


class SCIMGroupTests(TestCase):
    """SCIM Group tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")]
        )
        self.provider.property_mappings_group.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")]
        )

    @Mocker()
    def test_group_create(self, mock: Mocker):
        """Test group creation"""
        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Groups",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "externalId": str(group.pk),
                "displayName": group.name,
            },
        )

    @Mocker()
    def test_group_create_update(self, mock: Mocker):
        """Test group creation and update"""
        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Groups",
            json={
                "id": scim_id,
            },
        )
        mock.put(
            "https://localhost/Groups",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        body = loads(mock.request_history[1].body)
        with open("schemas/scim-group.schema.json", encoding="utf-8") as schema:
            validate(body, loads(schema.read()))
        self.assertEqual(
            body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "externalId": str(group.pk),
                "displayName": group.name,
            },
        )
        group.save()
        self.assertEqual(mock.call_count, 4)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertEqual(mock.request_history[2].method, "GET")
        self.assertEqual(mock.request_history[3].method, "PUT")

    @Mocker()
    def test_group_create_delete(self, mock: Mocker):
        """Test group creation"""
        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Groups",
            json={
                "id": scim_id,
            },
        )
        mock.delete(f"https://localhost/Groups/{scim_id}", status_code=204)
        uid = generate_id()
        group = Group.objects.create(
            name=uid,
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "externalId": str(group.pk),
                "displayName": group.name,
            },
        )
        group.delete()
        self.assertEqual(mock.call_count, 4)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[3].method, "DELETE")
        self.assertEqual(mock.request_history[3].url, f"https://localhost/Groups/{scim_id}")

    @Mocker()
    def test_group_integer_ids(self, mock: Mocker):
        """Test group creation with integer IDs from SCIM provider"""
        scim_id = 123  # Integer ID from SCIM provider
        user_scim_id = 456  # Integer user ID from SCIM provider
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Groups",
            json={
                "id": scim_id,  # Integer ID
            },
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": user_scim_id,  # Integer ID
            },
        )

        # Create user first
        user = User.objects.create(username="testuser", email="test@example.com")

        # Create group
        group = Group.objects.create(name="testgroup")
        group.users.add(user)

        # Verify that integer IDs are handled correctly
        # The system should convert integer IDs to strings internally
        from authentik.providers.scim.models import SCIMProviderGroup, SCIMProviderUser

        scim_group = SCIMProviderGroup.objects.filter(group=group).first()
        scim_user = SCIMProviderUser.objects.filter(user=user).first()

        # Verify IDs are stored as strings
        self.assertIsInstance(scim_group.scim_id, str)
        self.assertEqual(scim_group.scim_id, str(scim_id))
        self.assertIsInstance(scim_user.scim_id, str)
        self.assertEqual(scim_user.scim_id, str(user_scim_id))

    @Mocker()
    def test_group_member_integer_values(self, mock: Mocker):
        """Test group sync with integer member values from SCIM provider (issue #15533)"""
        scim_group_id = "72"
        scim_user_ids = [53, 54, 55, 56, 57]  # Integer member values from provider

        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Groups",
            json={
                "id": scim_group_id,
            },
        )
        # Mock the GET request that was failing in the original issue
        mock.get(
            f"https://localhost/Groups/{scim_group_id}",
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": scim_group_id,
                "members": [
                    {"value": user_id, "display": f"USER{user_id}"} for user_id in scim_user_ids
                ],
                "displayName": "GROUP1",
                "externalId": "05c6f450-b1d2-4198-8e04-dad1c85c367e",
                "meta": {
                    "resourceType": "Group",
                    "created": "2025-07-13T05:58:06+00:00",
                    "lastModified": "2025-07-13T09:07:28+00:00",
                    "location": f"https://localhost/Groups/{scim_group_id}",
                },
            },
        )

        # Create group and trigger sync
        group = Group.objects.create(name="testgroup")

        # This should not raise a ValidationError anymore
        from authentik.providers.scim.clients.groups import SCIMGroupClient
        from authentik.providers.scim.models import SCIMProviderGroup

        client = SCIMGroupClient(self.provider)

        # Create the SCIM connection manually for this test
        SCIMProviderGroup.objects.create(
            provider=self.provider, group=group, scim_id=scim_group_id, attributes={}
        )

        # This call should work without ValidationError
        try:
            client.patch_compare_users(group)
        except Exception as e:
            self.fail(f"patch_compare_users raised {type(e).__name__} unexpectedly: {e}")

    def test_ensure_string_id_integration(self):
        """Test that the ensure_string_id utility is properly integrated"""
        from authentik.lib.utils.convert import ensure_string_id

        # Test the exact scenario from issue #15533
        test_cases = [
            53,
            54,
            55,
            56,
            57,  # Integer member values from the issue
            72,  # Group ID from the issue
            "string-id",  # String ID should pass through
            None,  # None should remain None
        ]

        expected_results = [
            "53",
            "54",
            "55",
            "56",
            "57",  # Integers converted to strings
            "72",  # Group ID converted
            "string-id",  # String unchanged
            None,  # None unchanged
        ]

        for test_value, expected in zip(test_cases, expected_results, strict=False):
            result = ensure_string_id(test_value)
            self.assertEqual(result, expected)

            # Test type validation
            if expected is not None:
                self.assertIsInstance(result, (str, type(None)))

    def test_scim_group_creation_with_integer_ids(self):
        """Test SCIM group creation process handles integer IDs correctly"""
        from authentik.lib.utils.convert import ensure_string_id

        # Simulate the group creation process with integer responses
        mock_group_response = {
            "id": 999,  # Integer ID that should be converted
            "displayName": "Test Group",
            "members": [
                {"value": 111, "display": "User111"},
                {"value": 222, "display": "User222"},
            ],
        }

        # Test that our utility function handles this correctly
        converted_group_id = ensure_string_id(mock_group_response["id"])
        self.assertEqual(converted_group_id, "999")
        self.assertIsInstance(converted_group_id, str)

        # Test member conversions
        for member in mock_group_response["members"]:
            original_value = member["value"]
            converted_value = ensure_string_id(original_value)
            self.assertEqual(converted_value, str(original_value))
            self.assertIsInstance(converted_value, str)
