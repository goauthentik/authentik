"""SCIM User tests"""

from json import loads

from django.test import TestCase
from django.utils.text import slugify
from jsonschema import validate
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.events.models import SystemTask
from authentik.lib.generators import generate_id
from authentik.lib.sync.outgoing.base import SAFE_METHODS
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync, sync_tasks
from authentik.tenants.models import Tenant


class SCIMUserTests(TestCase):
    """SCIM User tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        Tenant.objects.update(avatars="none")
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

    @Mocker()
    def test_user_create(self, mock: Mocker):
        """Test user creation"""
        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "displayName": f"{uid} {uid}",
                "userName": uid,
            },
        )

    @Mocker()
    def test_user_create_custom_schema(self, mock: Mocker):
        """Test user creation with custom schema"""
        schema = SCIMMapping.objects.create(
            name="custom_schema",
            expression="""return {"schemas": ["foo"]}""",
        )
        self.provider.property_mappings.add(schema)
        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User", "foo"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "displayName": f"{uid} {uid}",
                "userName": uid,
            },
        )

    @Mocker()
    def test_user_create_different_provider_same_id(self, mock: Mocker):
        """Test user creation with multiple providers that happen
        to return the same object ID"""
        # Create duplicate provider
        provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
            exclude_users_service_account=True,
        )
        app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        app.backchannel_providers.add(provider)
        provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 4)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "displayName": f"{uid} {uid}",
                "userName": uid,
            },
        )

    @Mocker()
    def test_user_create_update(self, mock: Mocker):
        """Test user creation and update"""
        scim_id = generate_id()
        mock: Mocker
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        mock.put(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        body = loads(mock.request_history[1].body)
        with open("schemas/scim-user.schema.json", encoding="utf-8") as schema:
            validate(body, loads(schema.read()))
        self.assertEqual(
            body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "displayName": f"{uid} {uid}",
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "userName": uid,
            },
        )
        user.save()
        self.assertEqual(mock.call_count, 4)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertEqual(mock.request_history[2].method, "GET")
        self.assertEqual(mock.request_history[3].method, "PUT")

    @Mocker()
    def test_user_create_delete(self, mock: Mocker):
        """Test user creation"""
        scim_id = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        mock.delete(f"https://localhost/Users/{scim_id}", status_code=204)
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "displayName": f"{uid} {uid}",
                "userName": uid,
            },
        )
        user.delete()
        self.assertEqual(mock.call_count, 4)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[3].method, "DELETE")
        self.assertEqual(mock.request_history[3].url, f"https://localhost/Users/{scim_id}")

    @Mocker()
    def test_sync_task(self, mock: Mocker):
        """Test sync tasks"""
        user_scim_id = generate_id()
        group_scim_id = generate_id()
        uid = generate_id()
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": user_scim_id,
            },
        )
        mock.put(
            f"https://localhost/Users/{user_scim_id}",
            json={
                "id": user_scim_id,
            },
        )
        mock.post(
            "https://localhost/Groups",
            json={
                "id": group_scim_id,
            },
        )
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )

        sync_tasks.trigger_single_task(self.provider, scim_sync).get()

        self.assertEqual(mock.call_count, 5)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertEqual(mock.request_history[-2].method, "PUT")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "displayName": f"{uid} {uid}",
                "userName": uid,
            },
        )

    def test_user_create_dry_run(self):
        """Test user creation (dry_run)"""
        # Update the provider before we start mocking as saving the provider triggers a full sync
        self.provider.dry_run = True
        self.provider.save()
        with Mocker() as mock:
            scim_id = generate_id()
            mock.get(
                "https://localhost/ServiceProviderConfig",
                json={},
            )
            mock.post(
                "https://localhost/Users",
                json={
                    "id": scim_id,
                },
            )
            uid = generate_id()
            User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )
            self.assertEqual(mock.call_count, 1, mock.request_history)
            self.assertEqual(mock.request_history[0].method, "GET")

    def test_sync_task_dry_run(self):
        """Test sync tasks"""
        # Update the provider before we start mocking as saving the provider triggers a full sync
        self.provider.dry_run = True
        self.provider.save()
        with Mocker() as mock:
            uid = generate_id()
            mock.get(
                "https://localhost/ServiceProviderConfig",
                json={},
            )
            User.objects.create(
                username=uid,
                name=f"{uid} {uid}",
                email=f"{uid}@goauthentik.io",
            )

            sync_tasks.trigger_single_task(self.provider, scim_sync).get()

            self.assertEqual(mock.call_count, 3)
            for request in mock.request_history:
                self.assertIn(request.method, SAFE_METHODS)
        task = SystemTask.objects.filter(uid=slugify(self.provider.name)).first()
        self.assertIsNotNone(task)
        drop_msg = task.messages[3]
        self.assertEqual(drop_msg["event"], "Dropping mutating request due to dry run")
        self.assertIsNotNone(drop_msg["attributes"]["url"])
        self.assertIsNotNone(drop_msg["attributes"]["body"])
        self.assertIsNotNone(drop_msg["attributes"]["method"])

    @Mocker()
    def test_user_create_exception_fallback(self, mock: Mocker):
        """Test user creation with exception fallback for ID validation"""
        import time

        timestamp = int(time.time() * 1000)
        scim_id = timestamp

        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        # Mock a response that will cause validation to fail
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "testuser",
                # Add invalid field to trigger validation error
                "invalid_field": "invalid_value",
            },
        )

        from authentik.providers.scim.clients.users import SCIMUserClient

        user = User.objects.create(
            username=f"testuser-{timestamp}",
            name=f"testuser-{timestamp}",
            email=f"testuser-{timestamp}@example.com",
        )

        # Clean up any existing SCIM entries
        from authentik.providers.scim.models import SCIMProviderUser

        SCIMProviderUser.objects.filter(user=user, provider=self.provider).delete()

        client = SCIMUserClient(self.provider)
        scim_user = client.create(user)

        # Should fallback to raw response.get("id")
        self.assertIsInstance(scim_user.scim_id, str)
        self.assertEqual(scim_user.scim_id, str(scim_id))

        # Cleanup
        scim_user.delete()
        user.delete()

    @Mocker()
    def test_user_create_object_exists_exception_fallback(self, mock: Mocker):
        """Test user creation with ObjectExistsSyncException and exception fallback"""
        import time

        timestamp = int(time.time() * 1000)
        scim_id = timestamp

        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={"filter": {"supported": True}},
        )
        # Mock POST to fail with ObjectExistsSyncException
        mock.post(
            "https://localhost/Users",
            status_code=409,
            json={"error": "User already exists"},
        )
        # Mock GET filter request
        mock.get(
            "https://localhost/Users?filter=userName%20eq%20testuser",
            json={
                "Resources": [
                    {
                        "id": scim_id,
                        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                        "userName": "testuser",
                        # Add invalid field to trigger validation error
                        "invalid_field": "invalid_value",
                    }
                ]
            },
        )

        from authentik.providers.scim.clients.users import SCIMUserClient

        user = User.objects.create(
            username="testuser",
            name="testuser",
            email="testuser@example.com",
        )

        # Clean up any existing SCIM entries
        from authentik.providers.scim.models import SCIMProviderUser

        SCIMProviderUser.objects.filter(user=user, provider=self.provider).delete()

        client = SCIMUserClient(self.provider)
        scim_user = client.create(user)

        # Should fallback to raw response["id"]
        self.assertIsInstance(scim_user.scim_id, str)
        self.assertEqual(scim_user.scim_id, str(scim_id))

        # Cleanup
        scim_user.delete()
        user.delete()

    @Mocker()
    def test_user_create_object_exists_no_resources(self, mock: Mocker):
        """Test user creation with ObjectExistsSyncException but no resources found"""
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={"filter": {"supported": True}},
        )
        # Mock POST to fail with ObjectExistsSyncException
        mock.post(
            "https://localhost/Users",
            status_code=409,
            json={"error": "User already exists"},
        )
        # Mock GET filter request with no resources
        mock.get(
            "https://localhost/Users?filter=userName%20eq%20testuser",
            json={"Resources": []},
        )

        from authentik.lib.sync.outgoing.exceptions import ObjectExistsSyncException
        from authentik.providers.scim.clients.users import SCIMUserClient

        user = User.objects.create(
            username="testuser",
            name="testuser",
            email="testuser@example.com",
        )

        # Clean up any existing SCIM entries
        from authentik.providers.scim.models import SCIMProviderUser

        SCIMProviderUser.objects.filter(user=user, provider=self.provider).delete()

        client = SCIMUserClient(self.provider)

        # Should re-raise the ObjectExistsSyncException
        with self.assertRaises(ObjectExistsSyncException):
            client.create(user)

        # Cleanup
        user.delete()

    @Mocker()
    def test_user_create_missing_id(self, mock: Mocker):
        """Test user creation with missing ID in response"""
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        # Mock response without ID
        mock.post(
            "https://localhost/Users",
            json={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "testuser",
                # Missing "id" field
            },
        )

        from authentik.lib.sync.outgoing.exceptions import StopSync
        from authentik.providers.scim.clients.users import SCIMUserClient

        user = User.objects.create(
            username="testuser",
            name="testuser",
            email="testuser@example.com",
        )

        # Clean up any existing SCIM entries
        from authentik.providers.scim.models import SCIMProviderUser

        SCIMProviderUser.objects.filter(user=user, provider=self.provider).delete()

        client = SCIMUserClient(self.provider)

        # Should raise StopSync for missing ID
        with self.assertRaises(StopSync):
            client.create(user)

        # Cleanup
        user.delete()

    @Mocker()
    def test_user_create_empty_id(self, mock: Mocker):
        """Test user creation with empty ID in response"""
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        # Mock response with empty ID
        mock.post(
            "https://localhost/Users",
            json={
                "id": "",
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "testuser",
            },
        )

        from authentik.lib.sync.outgoing.exceptions import StopSync
        from authentik.providers.scim.clients.users import SCIMUserClient

        user = User.objects.create(
            username="testuser",
            name="testuser",
            email="testuser@example.com",
        )

        # Clean up any existing SCIM entries
        from authentik.providers.scim.models import SCIMProviderUser

        SCIMProviderUser.objects.filter(user=user, provider=self.provider).delete()

        client = SCIMUserClient(self.provider)

        # Should raise StopSync for empty ID
        with self.assertRaises(StopSync):
            client.create(user)

        # Cleanup
        user.delete()
