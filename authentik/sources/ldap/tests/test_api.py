"""LDAP Source API tests"""

from rest_framework.test import APITestCase

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
