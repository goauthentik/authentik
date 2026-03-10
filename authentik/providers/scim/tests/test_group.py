"""SCIM Group tests"""

from json import loads

from django.test import TestCase
from jsonschema import validate
from requests_mock import Mocker

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMMapping, SCIMProvider, SCIMProviderGroup
from authentik.providers.scim.tasks import scim_sync


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
        group.name = generate_id()
        group.save()
        self.assertEqual(mock.call_count, 3)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertEqual(mock.request_history[2].method, "PUT")

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
        self.assertEqual(mock.call_count, 3)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[2].method, "DELETE")
        self.assertEqual(mock.request_history[2].url, f"https://localhost/Groups/{scim_id}")

    @Mocker()
    def test_group_create_update_noop(self, mock: Mocker):
        """Test group creation and noop update"""
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
        conn = SCIMProviderGroup.objects.filter(group=group).first()
        conn.attributes = {
            "id": scim_id,
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "externalId": str(group.pk),
            "displayName": group.name,
        }
        conn.save()
        mock.get(
            f"https://localhost/Groups/{scim_id}",
            json={
                "id": scim_id,
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "externalId": str(group.pk),
                "displayName": group.name,
                "members": [],
            },
        )
        group.save()
        self.assertEqual(mock.call_count, 3)
        self.assertEqual(mock.request_history[0].method, "GET")
        self.assertEqual(mock.request_history[1].method, "POST")
        self.assertEqual(mock.request_history[2].method, "GET")
        self.assertNotIn("PUT", [req.method for req in mock.request_history])

    def _create_stale_provider_group(self, scim_id: str) -> Group:
        """Create a group that is outside the provider's scope (via group_filters) with an
        existing SCIMProviderGroup, simulating a previously synced group now out of scope."""
        self.app.backchannel_providers.remove(self.provider)
        anchor = Group.objects.create(name=generate_id())
        stale = Group.objects.create(name=generate_id())
        self.app.backchannel_providers.add(self.provider)

        self.provider.group_filters.set([anchor])
        SCIMProviderGroup.objects.create(provider=self.provider, group=stale, scim_id=scim_id)
        return stale

    @Mocker()
    def test_sync_cleanup_stale_group_delete(self, mock: Mocker):
        """Stale (out-of-scope) groups are deleted during full sync cleanup"""
        scim_id = generate_id()
        mock.get("https://localhost/ServiceProviderConfig", json={})

        mock.post("https://localhost/Groups", json={"id": generate_id()})
        mock.delete(f"https://localhost/Groups/{scim_id}", status_code=204)
        self._create_stale_provider_group(scim_id)

        scim_sync.send(self.provider.pk).get_result()

        delete_reqs = [r for r in mock.request_history if r.method == "DELETE"]
        self.assertEqual(len(delete_reqs), 1)
        self.assertEqual(delete_reqs[0].url, f"https://localhost/Groups/{scim_id}")
        self.assertFalse(
            SCIMProviderGroup.objects.filter(provider=self.provider, scim_id=scim_id).exists()
        )

    @Mocker()
    def test_sync_cleanup_stale_group_not_found(self, mock: Mocker):
        """Stale group cleanup handles 404 from the remote gracefully"""
        scim_id = generate_id()
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.post("https://localhost/Groups", json={"id": generate_id()})
        mock.delete(f"https://localhost/Groups/{scim_id}", status_code=404)
        self._create_stale_provider_group(scim_id)

        scim_sync.send(self.provider.pk).get_result()

        delete_reqs = [r for r in mock.request_history if r.method == "DELETE"]
        self.assertEqual(len(delete_reqs), 1)

        self.assertFalse(
            SCIMProviderGroup.objects.filter(provider=self.provider, scim_id=scim_id).exists()
        )

    @Mocker()
    def test_sync_cleanup_stale_group_transient_error(self, mock: Mocker):
        """Stale group cleanup logs and retries on transient HTTP errors"""
        scim_id = generate_id()
        mock.get("https://localhost/ServiceProviderConfig", json={})
        mock.post("https://localhost/Groups", json={"id": generate_id()})
        mock.delete(f"https://localhost/Groups/{scim_id}", status_code=429)
        self._create_stale_provider_group(scim_id)

        scim_sync.send(self.provider.pk)

        delete_reqs = [r for r in mock.request_history if r.method == "DELETE"]
        self.assertEqual(len(delete_reqs), 1)

    @Mocker()
    def test_sync_cleanup_stale_group_dry_run(self, mock: Mocker):
        """Stale group cleanup skips HTTP DELETE in dry_run mode"""
        self.provider.dry_run = True
        self.provider.save()
        scim_id = generate_id()
        mock.get("https://localhost/ServiceProviderConfig", json={})
        self._create_stale_provider_group(scim_id)

        scim_sync.send(self.provider.pk)

        delete_reqs = [r for r in mock.request_history if r.method == "DELETE"]
        self.assertEqual(len(delete_reqs), 0)
