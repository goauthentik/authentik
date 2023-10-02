"""LDAP Source tests"""
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction
from authentik.events.monitored_tasks import TaskInfo, TaskResultStatus
from authentik.lib.generators import generate_id, generate_key
from authentik.lib.utils.reflection import class_to_path
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tasks import ldap_sync, ldap_sync_all
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection
from authentik.sources.ldap.tests.mock_freeipa import mock_freeipa_connection
from authentik.sources.ldap.tests.mock_slapd import mock_slapd_connection

LDAP_PASSWORD = generate_key()


class LDAPSyncTests(TestCase):
    """LDAP Sync tests"""

    @apply_blueprint("system/sources-ldap.yaml")
    def setUp(self):
        self.source: LDAPSource = LDAPSource.objects.create(
            name="ldap",
            slug="ldap",
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )

    def test_sync_missing_page(self):
        """Test sync with missing page"""
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.delay(self.source.pk, class_to_path(UserLDAPSynchronizer), "foo").get()
        status = TaskInfo.by_name("ldap_sync:ldap:users:foo")
        self.assertEqual(status.result.status, TaskResultStatus.ERROR)

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
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync_full()
            self.assertFalse(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())
        events = Event.objects.filter(
            action=EventAction.CONFIGURATION_ERROR,
            context__message="Failed to evaluate property-mapping: 'name'",
        )
        self.assertTrue(events.exists())

    def test_sync_mapping(self):
        """Test property mappings"""
        none = LDAPPropertyMapping.objects.create(
            name=generate_id(), object_field="none", expression="return None"
        )
        byte_mapping = LDAPPropertyMapping.objects.create(
            name=generate_id(), object_field="bytes", expression="return b''"
        )
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        self.source.property_mappings.add(none, byte_mapping)
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))

        # we basically just test that the mappings don't throw errors
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync_full()

    def test_sync_users_ad(self):
        """Test user sync"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))

        # Create the user beforehand so we can set attributes and check they aren't removed
        user = User.objects.create(
            username="user0_sn",
            attributes={
                "ldap_uniq": (
                    "S-117-6648368-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-"
                    "0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-"
                    "0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-"
                    "0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0"
                ),
                "foo": "bar",
            },
        )

        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync_full()
            user = User.objects.filter(username="user0_sn").first()
            self.assertEqual(user.attributes["foo"], "bar")
            self.assertFalse(user.is_active)
            self.assertEqual(user.path, "goauthentik.io/sources/ldap/users/foo")
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
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync_full()
            self.assertTrue(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())

    def test_sync_users_freeipa_ish(self):
        """Test user sync (FreeIPA-ish), mainly testing vendor quirks"""
        self.source.object_uniqueness_field = "uid"
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        connection = MagicMock(return_value=mock_freeipa_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync_full()
            self.assertTrue(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())
            self.assertFalse(User.objects.get(username="user-nsaccountlock").is_active)

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
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            _user = create_test_admin_user()
            parent_group = Group.objects.get(name=_user.username)
            self.source.sync_parent_group = parent_group
            self.source.save()
            group_sync = GroupLDAPSynchronizer(self.source)
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source)
            membership_sync.sync_full()
            group: Group = Group.objects.filter(name="test-group").first()
            self.assertIsNotNone(group)
            self.assertEqual(group.parent, parent_group)

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
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            self.source.save()
            group_sync = GroupLDAPSynchronizer(self.source)
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source)
            membership_sync.sync_full()
            group = Group.objects.filter(name="group1")
            self.assertTrue(group.exists())

    def test_sync_groups_openldap_posix_group(self):
        """Test posix group sync"""
        self.source.object_uniqueness_field = "cn"
        self.source.group_membership_field = "memberUid"
        self.source.user_object_filter = "(objectClass=posixAccount)"
        self.source.group_object_filter = "(objectClass=posixGroup)"
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        self.source.property_mappings_group.set(
            LDAPPropertyMapping.objects.filter(managed="goauthentik.io/sources/ldap/openldap-cn")
        )
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            self.source.save()
            user_sync = UserLDAPSynchronizer(self.source)
            user_sync.sync_full()
            group_sync = GroupLDAPSynchronizer(self.source)
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source)
            membership_sync.sync_full()
            # Test if membership mapping based on memberUid works.
            posix_group = Group.objects.filter(name="group-posix").first()
            self.assertTrue(posix_group.users.filter(name="user-posix").exists())

    def test_tasks_ad(self):
        """Test Scheduled tasks"""
        self.source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        self.source.save()
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
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
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync_all.delay().get()
