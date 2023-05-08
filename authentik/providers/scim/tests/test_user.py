"""SCIM User tests"""
from json import loads

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user
from jsonschema import validate
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync


class SCIMUserTests(TestCase):
    """SCIM User tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        User.objects.all().exclude(pk=get_anonymous_user().pk).delete()
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
            name=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
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
                    "familyName": "",
                    "formatted": uid,
                    "givenName": uid,
                },
                "displayName": uid,
                "photos": [],
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
            name=uid,
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
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "displayName": uid,
                "externalId": user.uid,
                "name": {
                    "familyName": "",
                    "formatted": uid,
                    "givenName": uid,
                },
                "photos": [],
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
        mock.delete("https://localhost/Users", status_code=204)
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=uid,
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
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
                    "familyName": "",
                    "formatted": uid,
                    "givenName": uid,
                },
                "displayName": uid,
                "photos": [],
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
            name=uid,
            email=f"{uid}@goauthentik.io",
        )

        scim_sync.delay(self.provider.pk).get()

        self.assertEqual(mock.call_count, 5)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertEqual(mock.request_history[-2].method, "PUT")
        self.assertJSONEqual(
            mock.request_history[1].body,
            {
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
                    "familyName": "",
                    "formatted": uid,
                    "givenName": uid,
                },
                "displayName": uid,
                "photos": [],
                "userName": uid,
            },
        )
