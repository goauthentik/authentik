"""LDAP Source model tests"""

from django.test import TestCase

from authentik.lib.generators import generate_id
from authentik.sources.ldap.models import LDAPSource


class LDAPModelTests(TestCase):
    """LDAP Source model tests"""

    def test_server_sni(self):
        """Test that the SNI name is the bare hostname, not the full server URI"""
        source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri="ldaps://ldap.example.com:636",
            base_dn="dc=example,dc=com",
            sni=True,
        )
        pool = source.server()
        self.assertEqual([server.tls.sni for server in pool.servers], ["ldap.example.com"])

    def test_server_sni_multiple(self):
        """Test that each server in a pool gets its own hostname as the SNI name"""
        source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri="ldaps://ldap1.example.com,ldaps://ldap2.example.com:636",
            base_dn="dc=example,dc=com",
            sni=True,
        )
        pool = source.server()
        self.assertEqual(
            [server.tls.sni for server in pool.servers],
            ["ldap1.example.com", "ldap2.example.com"],
        )

    def test_server_sni_disabled(self):
        """Test that no SNI name is set when the SNI option is disabled"""
        source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri="ldaps://ldap.example.com",
            base_dn="dc=example,dc=com",
            sni=False,
        )
        pool = source.server()
        for server in pool.servers:
            self.assertIsNone(server.tls.sni)
