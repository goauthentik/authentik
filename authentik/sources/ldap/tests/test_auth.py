"""LDAP Source tests"""
from unittest.mock import Mock, PropertyMock, patch

from django.test import TestCase

from authentik.core.models import User
from authentik.managed.manager import ObjectManager
from authentik.providers.oauth2.generators import generate_client_secret
from authentik.sources.ldap.auth import LDAPBackend
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tests.utils import mock_ad_connection

LDAP_PASSWORD = generate_client_secret()
LDAP_CONNECTION_PATCH = PropertyMock(return_value=mock_ad_connection(LDAP_PASSWORD))


class LDAPSyncTests(TestCase):
    """LDAP Sync tests"""

    def setUp(self):
        ObjectManager().run()
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="DC=AD2012,DC=LAB",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )
        self.source.property_mappings.set(LDAPPropertyMapping.objects.all())
        self.source.save()

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_auth_synced_user(self):
        """Test Cached auth"""
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
