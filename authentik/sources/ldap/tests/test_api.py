"""LDAP Source API tests"""

from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_key
from authentik.sources.ldap.api import LDAPSourceSerializer
from authentik.sources.ldap.models import LDAPSource

LDAP_PASSWORD = generate_key()


class LDAPAPITests(APITestCase):
    """LDAP API tests"""

    def test_sync_users_password_valid(self):
        """Check that single source with sync_users_password is valid"""
        serializer = LDAPSourceSerializer(
            data={
                "name": "foo",
                "slug": " foo",
                "server_uri": "ldaps://1.2.3.4",
                "bind_cn": "",
                "bind_password": LDAP_PASSWORD,
                "base_dn": "dc=foo",
                "sync_users_password": True,
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_sync_users_password_invalid(self):
        """Ensure only a single source with password sync can be created"""
        LDAPSource.objects.create(
            name="foo",
            slug="foo",
            server_uri="ldaps://1.2.3.4",
            bind_cn="",
            bind_password=LDAP_PASSWORD,
            base_dn="dc=foo",
            sync_users_password=True,
        )
        serializer = LDAPSourceSerializer(
            data={
                "name": "foo",
                "slug": " foo",
                "server_uri": "ldaps://1.2.3.4",
                "bind_cn": "",
                "bind_password": LDAP_PASSWORD,
                "base_dn": "dc=foo",
                "sync_users_password": False,
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_sync_users_mapping_empty(self):
        """Check that when sync_users is enabled, property mappings must be set"""
        serializer = LDAPSourceSerializer(
            data={
                "name": "foo",
                "slug": " foo",
                "server_uri": "ldaps://1.2.3.4",
                "bind_cn": "",
                "bind_password": LDAP_PASSWORD,
                "base_dn": "dc=foo",
                "sync_users": True,
                "user_property_mappings": [],
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_sync_groups_mapping_empty(self):
        """Check that when sync_groups is enabled, property mappings must be set"""
        serializer = LDAPSourceSerializer(
            data={
                "name": "foo",
                "slug": " foo",
                "server_uri": "ldaps://1.2.3.4",
                "bind_cn": "",
                "bind_password": LDAP_PASSWORD,
                "base_dn": "dc=foo",
                "sync_groups": True,
                "group_property_mappings": [],
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_sync_trigger(self):
        """Test that sync trigger endpoint sends the sync schedule"""
        user = create_test_admin_user()
        self.client.force_login(user)

        source = LDAPSource.objects.create(
            name="test-sync-trigger",
            slug="test-sync-trigger",
            server_uri="ldaps://1.2.3.4",
            bind_cn="",
            bind_password=LDAP_PASSWORD,
            base_dn="dc=foo",
        )
        spec = source.schedule_specs[0]
        spec.rel_obj = source
        spec.identifier = source.pk
        spec.update_or_create()
        with patch(
            "authentik.tasks.schedules.models.Schedule.send",
            return_value=MagicMock(),
        ) as mock_send:
            response = self.client.post(f"/api/v3/sources/ldap/{source.slug}/sync/")
        self.assertEqual(response.status_code, 201)
        mock_send.assert_called_once()
