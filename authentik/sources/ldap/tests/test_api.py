"""LDAP Source API tests"""

from json import loads
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.ldap.api import LDAPSourceSerializer
from authentik.sources.ldap.models import LDAPSource, LDAPSourcePropertyMapping
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection


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
                "bind_password": generate_id(),
                "base_dn": "dc=foo",
                "sync_users_password": True,
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})

    def test_sync_users_password_invalid(self):
        """Ensure only a single source with password sync can be created"""
        LDAPSource.objects.create(
            name="foo",
            slug=generate_id(),
            server_uri="ldaps://1.2.3.4",
            bind_cn="",
            bind_password=generate_id(),
            base_dn="dc=foo",
            sync_users_password=True,
        )
        serializer = LDAPSourceSerializer(
            data={
                "name": "foo",
                "slug": generate_id(),
                "server_uri": "ldaps://1.2.3.4",
                "bind_cn": "",
                "bind_password": generate_id(),
                "base_dn": "dc=foo",
                "sync_users_password": True,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "sync_users_password": [
                    ErrorDetail(
                        string="Only a single LDAP Source with password synchronization is allowed",
                        code="invalid",
                    )
                ]
            },
        )

    def test_sync_users_mapping_empty(self):
        """Check that when sync_users is enabled, property mappings must be set"""
        serializer = LDAPSourceSerializer(
            data={
                "name": "foo",
                "slug": " foo",
                "server_uri": "ldaps://1.2.3.4",
                "bind_cn": "",
                "bind_password": generate_id(),
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
                "bind_password": generate_id(),
                "base_dn": "dc=foo",
                "sync_groups": True,
                "group_property_mappings": [],
            }
        )
        self.assertFalse(serializer.is_valid())

    @apply_blueprint("system/sources-ldap.yaml")
    def test_sync_debug(self):
        user = create_test_admin_user()
        self.client.force_login(user)

        source: LDAPSource = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )
        source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        connection = MagicMock(return_value=mock_ad_connection())
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            res = self.client.get(
                reverse("authentik_api:ldapsource-debug", kwargs={"slug": source.slug})
            )
            self.assertEqual(res.status_code, 200)
            body = loads(res.content.decode())
            self.assertIn("users", body)
            self.assertIn("groups", body)
            self.assertIn("membership", body)
