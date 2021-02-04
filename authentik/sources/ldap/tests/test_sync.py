"""LDAP Source tests"""
from unittest.mock import PropertyMock, patch

from django.test import TestCase

from authentik.core.models import Group, User
from authentik.managed.manager import ObjectManager
from authentik.providers.oauth2.generators import generate_client_secret
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tasks import ldap_sync_all
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
    def test_sync_users(self):
        """Test user sync"""
        user_sync = UserLDAPSynchronizer(self.source)
        user_sync.sync()
        self.assertTrue(User.objects.filter(username="user0_sn").exists())
        self.assertFalse(User.objects.filter(username="user1_sn").exists())

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_sync_groups(self):
        """Test group sync"""
        group_sync = GroupLDAPSynchronizer(self.source)
        group_sync.sync()
        membership_sync = MembershipLDAPSynchronizer(self.source)
        membership_sync.sync()
        group = Group.objects.filter(name="test-group")
        self.assertTrue(group.exists())

    @patch("authentik.sources.ldap.models.LDAPSource.connection", LDAP_CONNECTION_PATCH)
    def test_tasks(self):
        """Test Scheduled tasks"""
        ldap_sync_all.delay().get()
