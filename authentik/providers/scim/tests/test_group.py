"""SCIM Group tests"""
from json import loads

from django.test import TestCase
from jsonschema import validate
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider


class SCIMGroupTests(TestCase):
    """SCIM Group tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        self.provider: SCIMProvider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            token=generate_id(),
        )
        self.provider.property_mappings.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")]
        )
        self.provider.property_mappings_group.set(
            [SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")]
        )

    def test_group_create(self):
        """Test group creation"""
        scim_id = generate_id()
        with Mocker() as mock:
            mock: Mocker
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
                {"externalId": str(group.pk), "displayName": group.name},
            )

    def test_group_create_update(self):
        """Test group creation and update"""
        scim_id = generate_id()
        with Mocker() as mock:
            mock: Mocker
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
                {"externalId": str(group.pk), "displayName": group.name},
            )
            group.save()
            self.assertEqual(mock.call_count, 4)
            self.assertEqual(mock.request_history[0].method, "GET")
            self.assertEqual(mock.request_history[1].method, "POST")
            self.assertEqual(mock.request_history[2].method, "GET")
            self.assertEqual(mock.request_history[3].method, "PUT")

    def test_group_create_delete(self):
        """Test group creation"""
        scim_id = generate_id()
        with Mocker() as mock:
            mock: Mocker
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
            mock.delete("https://localhost/Groups", status_code=204)
            uid = generate_id()
            group = Group.objects.create(
                name=uid,
            )
            self.assertEqual(mock.call_count, 2)
            self.assertEqual(mock.request_history[0].method, "GET")
            self.assertEqual(mock.request_history[1].method, "POST")
            self.assertJSONEqual(
                mock.request_history[1].body,
                {"externalId": str(group.pk), "displayName": group.name},
            )
            group.delete()
            self.assertEqual(mock.call_count, 4)
            self.assertEqual(mock.request_history[0].method, "GET")
            self.assertEqual(mock.request_history[3].method, "DELETE")
            self.assertEqual(mock.request_history[3].url, f"https://localhost/Groups/{scim_id}")
