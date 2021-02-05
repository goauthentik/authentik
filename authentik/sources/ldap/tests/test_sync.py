"""LDAP Source tests"""
from unittest.mock import PropertyMock, patch

from django.db.models import Q
from django.test import TestCase

from authentik.core.models import Group, User
from authentik.managed.manager import ObjectManager
from authentik.providers.oauth2.generators import generate_client_secret
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tasks import ldap_sync_all
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection
from authentik.sources.ldap.tests.mock_slapd import mock_slapd_connection

LDAP_PASSWORD = generate_client_secret()


class LDAPSyncTests(TestCase):
    """LDAP Sync tests"""

    def setUp(self):
        ObjectManager().run()
        self.source = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )

    def test_sync_users_ad(self):
        """Test user sync"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default Active Directory Mapping")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync()
            self.assertTrue(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())

    def test_sync_users_openldap(self):
        """Test user sync"""
        self.source.object_uniqueness_field = "uid"
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default OpenLDAP Mapping")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync()
            self.assertTrue(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())

    def test_sync_groups_ad(self):
        """Test group sync"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default Active Directory Mapping")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            group_sync = GroupLDAPSynchronizer(self.source)
            group_sync.sync()
            membership_sync = MembershipLDAPSynchronizer(self.source)
            membership_sync.sync()
            group = Group.objects.filter(name="test-group")
            self.assertTrue(group.exists())

    def test_sync_groups_openldap(self):
        """Test group sync"""
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default OpenLDAP Mapping")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            group_sync = GroupLDAPSynchronizer(self.source)
            group_sync.sync()
            membership_sync = MembershipLDAPSynchronizer(self.source)
            membership_sync.sync()
            group = Group.objects.filter(name="test-group")
            self.assertTrue(group.exists())

    def test_tasks_ad(self):
        """Test Scheduled tasks"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default Active Directory Mapping")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync_all.delay().get()

    def test_tasks_openldap(self):
        """Test Scheduled tasks"""
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default OpenLDAP Mapping")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync_all.delay().get()
