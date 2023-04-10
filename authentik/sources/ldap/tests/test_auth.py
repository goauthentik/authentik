"""LDAP Source tests"""
from unittest.mock import MagicMock, Mock, patch

from django.db.models import Q
from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.lib.generators import generate_key
from authentik.sources.ldap.auth import LDAPBackend
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection
from authentik.sources.ldap.tests.mock_slapd import mock_slapd_connection

LDAP_PASSWORD = generate_key()


class LDAPSyncTests(TestCase):
    """LDAP Sync tests"""

    @apply_blueprint("system/sources-ldap.yaml")
    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )

    def test_auth_synced_user_ad(self):
        """Test Cached auth"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default-")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms-")
            )
        )
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync()

            user = User.objects.get(username="user0_sn")
            auth_user_by_bind = Mock(return_value=user)
            with patch(
                "authentik.sources.ldap.auth.LDAPBackend.auth_user_by_bind",
                auth_user_by_bind,
            ):
                backend = LDAPBackend()
                self.assertEqual(
                    backend.authenticate(None, username="user0_sn", password=LDAP_PASSWORD),
                    user,
                )

    def test_auth_synced_user_openldap(self):
        """Test Cached auth"""
        self.source.object_uniqueness_field = "uid"
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default OpenLDAP Mapping")
            )
        )
        self.source.save()
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync()

            user = User.objects.get(username="user0_sn")
            auth_user_by_bind = Mock(return_value=user)
            with patch(
                "authentik.sources.ldap.auth.LDAPBackend.auth_user_by_bind",
                auth_user_by_bind,
            ):
                backend = LDAPBackend()
                self.assertEqual(
                    backend.authenticate(None, username="user0_sn", password=LDAP_PASSWORD),
                    user,
                )
