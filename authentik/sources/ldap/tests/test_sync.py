"""LDAP Source tests"""
from unittest.mock import PropertyMock, patch

from django.db.models import Q
from django.test import TestCase

from authentik.core.models import Group, User
from authentik.events.models import Event, EventAction
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

    def test_sync_error(self):
        """Test user sync"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        mapping = LDAPPropertyMapping.objects.create(
            name="name",
            object_field="name",
            expression="q",
        )
        self.source.property_mappings.set([mapping])
        self.source.save()
        connection = PropertyMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync()
            self.assertFalse(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())
        events = Event.objects.filter(
            action=EventAction.CONFIGURATION_ERROR,
            context__message="Failed to evaluate property-mapping: name 'q' is not defined",
        )
        self.assertTrue(events.exists())

    def test_sync_users_ad(self):
        """Test user sync"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
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
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
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
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        self.source.property_mappings_group.set(
            LDAPPropertyMapping.objects.filter(managed="goauthentik.io/sources/ldap/default-name")
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
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        self.source.property_mappings_group.set(
            LDAPPropertyMapping.objects.filter(managed="goauthentik.io/sources/ldap/openldap-cn")
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            group_sync = GroupLDAPSynchronizer(self.source)
            group_sync.sync()
            membership_sync = MembershipLDAPSynchronizer(self.source)
            membership_sync.sync()
            group = Group.objects.filter(name="group1")
            self.assertTrue(group.exists())

    def test_tasks_ad(self):
        """Test Scheduled tasks"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
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
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        self.source.save()
        connection = PropertyMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync_all.delay().get()
