"""LDAP Source API tests"""

from json import loads
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_user
from authentik.lib.generators import generate_id
from authentik.sources.ldap.api.sources import LDAPSourceSerializer
from authentik.sources.ldap.models import (
    LDAPSource,
    LDAPSourceBindMethod,
    LDAPSourcePropertyMapping,
)
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection


class LDAPAPITests(APITestCase):
    """LDAP API tests"""

    def source_data(self, **kwargs):
        """Build serializer data for an LDAP source."""
        data = {
            "name": "foo",
            "slug": generate_id(),
            "server_uri": "ldaps://1.2.3.4",
            "base_dn": "dc=foo",
        }
        data.update(kwargs)
        return data

    def external_source_data(self, **kwargs):
        """Build serializer data for a SASL EXTERNAL source."""
        data = self.source_data(
            name="external",
            server_uri="ldap://ldap.example.com",
            start_tls=True,
            client_certificate=create_test_cert().pk,
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
            base_dn="dc=example,dc=com",
            sync_users_password=False,
        )
        data.update(kwargs)
        return data

    def test_sasl_external_valid(self):
        """SASL EXTERNAL accepts a client certificate over StartTLS."""
        serializer = LDAPSourceSerializer(data=self.external_source_data())
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})

    def test_sasl_external_valid_ldaps(self):
        """SASL EXTERNAL accepts a client certificate over LDAPS."""
        serializer = LDAPSourceSerializer(
            data=self.external_source_data(
                server_uri="ldaps://ldap.example.com",
                start_tls=False,
            )
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})

    def test_sasl_external_requires_certificate(self):
        """SASL EXTERNAL requires a client certificate and private key."""
        serializer = LDAPSourceSerializer(data=self.external_source_data(client_certificate=None))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "client_certificate": [
                    ErrorDetail(
                        string=("SASL EXTERNAL requires a client certificate with a private key."),
                        code="invalid",
                    )
                ]
            },
        )

    def test_sasl_external_rejects_plaintext(self):
        """SASL EXTERNAL rejects LDAP without StartTLS."""
        serializer = LDAPSourceSerializer(data=self.external_source_data(start_tls=False))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "server_uri": [
                    ErrorDetail(
                        string=(
                            "SASL EXTERNAL requires ldap:// with StartTLS or ldaps:// without "
                            "StartTLS."
                        ),
                        code="invalid",
                    )
                ]
            },
        )

    def test_sasl_external_rejects_start_tls_over_ldaps(self):
        """SASL EXTERNAL rejects StartTLS when the URI already uses LDAPS."""
        serializer = LDAPSourceSerializer(
            data=self.external_source_data(server_uri="ldaps://ldap.example.com")
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "server_uri": [
                    ErrorDetail(
                        string=(
                            "SASL EXTERNAL requires ldap:// with StartTLS or ldaps:// without "
                            "StartTLS."
                        ),
                        code="invalid",
                    )
                ]
            },
        )

    def test_sasl_external_rejects_mixed_server_schemes(self):
        """Every server in a SASL EXTERNAL pool must use the same secure transport."""
        serializer = LDAPSourceSerializer(
            data=self.external_source_data(
                server_uri="ldap://ldap.example.com,ldaps://ldap.example.net"
            )
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "server_uri": [
                    ErrorDetail(
                        string=(
                            "SASL EXTERNAL requires ldap:// with StartTLS or ldaps:// without "
                            "StartTLS."
                        ),
                        code="invalid",
                    )
                ]
            },
        )

    def test_sasl_external_partial_update(self):
        """Partial updates validate changed fields against existing source fields."""
        source = LDAPSource.objects.create(
            **self.source_data(
                name="external",
                server_uri="ldap://ldap.example.com",
                start_tls=True,
                client_certificate=create_test_cert(),
                service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
                base_dn="dc=example,dc=com",
                sync_users_password=False,
            )
        )
        serializer = LDAPSourceSerializer(
            source,
            data={"start_tls": False},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "server_uri": [
                    ErrorDetail(
                        string=(
                            "SASL EXTERNAL requires ldap:// with StartTLS or ldaps:// without "
                            "StartTLS."
                        ),
                        code="invalid",
                    )
                ]
            },
        )

    def test_sync_users_password_valid(self):
        """Check that single source with sync_users_password is valid"""
        serializer = LDAPSourceSerializer(
            data=self.source_data(
                slug=" foo",
                bind_cn="",
                bind_password=generate_id(),
                sync_users_password=True,
            )
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})

    def test_sync_users_password_invalid(self):
        """Ensure only a single source with password sync can be created"""
        LDAPSource.objects.create(
            **self.source_data(
                bind_cn="",
                bind_password=generate_id(),
                sync_users_password=True,
            )
        )
        serializer = LDAPSourceSerializer(
            data=self.source_data(
                bind_cn="",
                bind_password=generate_id(),
                sync_users_password=True,
            )
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
            data=self.source_data(
                slug=" foo",
                bind_cn="",
                bind_password=generate_id(),
                sync_users=True,
                user_property_mappings=[],
            )
        )
        self.assertFalse(serializer.is_valid())

    def test_sync_groups_mapping_empty(self):
        """Check that when sync_groups is enabled, property mappings must be set"""
        serializer = LDAPSourceSerializer(
            data=self.source_data(
                slug=" foo",
                bind_cn="",
                bind_password=generate_id(),
                sync_groups=True,
                group_property_mappings=[],
            )
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

    def _create_debug_source(self) -> LDAPSource:
        return LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )

    @apply_blueprint("system/sources-ldap.yaml")
    def test_debug_denied_for_anonymous(self):
        """debug must enforce RBAC: an anonymous caller may not read LDAP data."""
        source = self._create_debug_source()
        # NOTE: no self.client.force_login() -> caller is AnonymousUser
        connection = MagicMock(return_value=mock_ad_connection())
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            res = self.client.get(
                reverse("authentik_api:ldapsource-debug", kwargs={"slug": source.slug})
            )
        self.assertEqual(res.status_code, 403)

    @apply_blueprint("system/sources-ldap.yaml")
    def test_debug_denied_for_unauthorized_user(self):
        """debug must enforce RBAC: a user without view_ldapsource may not read LDAP data."""
        source = self._create_debug_source()
        # Authenticated, but holds no permission on the source object
        self.client.force_login(create_test_user())
        connection = MagicMock(return_value=mock_ad_connection())
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            res = self.client.get(
                reverse("authentik_api:ldapsource-debug", kwargs={"slug": source.slug})
            )
        self.assertEqual(res.status_code, 403)
