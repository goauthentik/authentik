"""LDAP Source model tests"""

from unittest.mock import MagicMock, Mock, call, patch

from django.test import TestCase
from ldap3 import EXTERNAL, SASL, SIMPLE
from ldap3.core.exceptions import LDAPConfigurationError

from authentik.core.tests.utils import create_test_cert
from authentik.lib.generators import generate_id
from authentik.sources.ldap.models import LDAPSource, LDAPSourceBindMethod


class LDAPModelTests(TestCase):
    """LDAP Source model tests"""

    def create_source(self, **kwargs) -> LDAPSource:
        """Create an LDAP source with common required fields."""
        source_kwargs = {
            "name": generate_id(),
            "slug": generate_id(),
            "server_uri": "ldaps://ldap.example.com",
            "base_dn": "dc=example,dc=com",
        }
        source_kwargs.update(kwargs)
        return LDAPSource.objects.create(
            **source_kwargs,
        )

    def test_server_sni(self):
        """Test that the SNI name is the bare hostname, not the full server URI"""
        source = self.create_source(
            server_uri="ldaps://ldap.example.com:636",
            sni=True,
        )
        pool = source.server()
        self.assertEqual([server.tls.sni for server in pool.servers], ["ldap.example.com"])

    def test_server_sni_multiple(self):
        """Test that each server in a pool gets its own hostname as the SNI name"""
        source = self.create_source(
            server_uri="ldaps://ldap1.example.com,ldaps://ldap2.example.com:636",
            sni=True,
        )
        pool = source.server()
        self.assertEqual(
            [server.tls.sni for server in pool.servers],
            ["ldap1.example.com", "ldap2.example.com"],
        )

    def test_server_sni_disabled(self):
        """Test that no SNI name is set when the SNI option is disabled"""
        source = self.create_source(
            server_uri="ldaps://ldap.example.com",
            sni=False,
        )
        pool = source.server()
        for server in pool.servers:
            self.assertIsNone(server.tls.sni)

    def test_simple_service_connection(self):
        """The default service connection preserves simple bind credentials."""
        source = self.create_source(bind_cn="cn=service", bind_password="password")
        with patch.object(source, "_connect_and_bind") as connection:
            source.connection()
        connection.assert_called_once_with(
            None,
            None,
            {"user": "cn=service", "password": "password"},
        )

    def test_anonymous_service_connection(self):
        """Blank credentials continue to let ldap3 select anonymous authentication."""
        source = self.create_source()
        with patch.object(source, "_connect_and_bind") as connection:
            source.connection()
        connection.assert_called_once_with(None, None, {"user": "", "password": ""})

    def test_sasl_external_service_connection(self):
        """SASL EXTERNAL derives authorization from the TLS client certificate."""
        source = self.create_source(
            client_certificate=create_test_cert(),
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
        )
        with patch.object(source, "_connect_and_bind") as connection:
            source.connection(connection_kwargs={"user": "ignored", "password": "ignored"})
        connection.assert_called_once_with(
            None,
            None,
            {
                "authentication": SASL,
                "sasl_mechanism": EXTERNAL,
                "sasl_credentials": "",
            },
        )

    def test_sasl_external_requires_client_certificate(self):
        """SASL EXTERNAL cannot run without a TLS client identity."""
        source = self.create_source(
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
        )
        with self.assertRaises(LDAPConfigurationError):
            source.connection()

    def test_sasl_external_requires_private_key(self):
        """SASL EXTERNAL rejects a certificate without its private key."""
        certificate = create_test_cert()
        certificate.key_data = ""
        certificate.save(update_fields=["key_data"])
        source = self.create_source(
            client_certificate=certificate,
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
        )
        with self.assertRaises(LDAPConfigurationError):
            source.connection()

    def test_sasl_external_requires_secure_transport(self):
        """SASL EXTERNAL rejects a plaintext LDAP connection."""
        source = self.create_source(
            server_uri="ldap://ldap.example.com",
            client_certificate=create_test_cert(),
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
        )
        with self.assertRaises(LDAPConfigurationError):
            source.connection()

    def test_sasl_external_start_tls(self):
        """SASL EXTERNAL accepts LDAP when StartTLS is enabled."""
        source = self.create_source(
            server_uri="ldap://ldap.example.com",
            start_tls=True,
            client_certificate=create_test_cert(),
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
        )
        with patch.object(source, "_connect_and_bind") as connection:
            source.connection()
        connection.assert_called_once_with(
            None,
            None,
            {
                "authentication": SASL,
                "sasl_mechanism": EXTERNAL,
                "sasl_credentials": "",
            },
        )

    def test_user_connection_always_uses_simple_bind(self):
        """User password verification never inherits the service bind method."""
        source = self.create_source(
            client_certificate=create_test_cert(),
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
        )
        with patch.object(source, "_connect_and_bind") as connection:
            source.connection_as_user("cn=user", "submitted-password")
        connection.assert_called_once_with(
            connection_kwargs={
                "user": "cn=user",
                "password": "submitted-password",
                "authentication": SIMPLE,
            }
        )

    def test_start_tls_before_bind(self):
        """StartTLS secures the connection before credentials are bound."""
        source = self.create_source(
            server_uri="ldap://ldap.example.com",
            start_tls=True,
        )
        server = MagicMock()
        connection = MagicMock()
        connection.bind.return_value = True
        connection.server.tls.certificate_file = None
        calls = Mock()
        calls.attach_mock(connection.start_tls, "start_tls")
        calls.attach_mock(connection.bind, "bind")
        with patch("authentik.sources.ldap.models.Connection", return_value=connection):
            source._connect_and_bind(server=server)
        self.assertEqual(
            calls.mock_calls,
            [call.start_tls(read_server_info=False), call.bind()],
        )
