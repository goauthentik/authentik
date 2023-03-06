"""SCIM User tests"""
from json import loads

from django.test import TestCase
from jsonschema import validate
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider


class SCIMUserTests(TestCase):
    """SCIM User tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
        )
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )

    def test_user_create(self):
        """Test user creation"""
        scim_id = generate_id()
        with Mocker() as mock:
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
                    "photos": [],
                    "userName": uid,
                },
            )

    def test_user_create_update(self):
        """Test user creation and update"""
        scim_id = generate_id()
        with Mocker() as mock:
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

    def test_user_create_delete(self):
        """Test user creation"""
        scim_id = generate_id()
        with Mocker() as mock:
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
                    "photos": [],
                    "userName": uid,
                },
            )
            user.delete()
            self.assertEqual(mock.call_count, 4)
            self.assertEqual(mock.request_history[0].method, "GET")
            self.assertEqual(mock.request_history[3].method, "DELETE")
            self.assertEqual(mock.request_history[3].url, f"https://localhost/Users/{scim_id}")
