"""LDAP Source tests"""

from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id, generate_key
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.reflection import class_to_path
from authentik.sources.ldap.models import (
    GroupLDAPSourceConnection,
    LDAPSource,
    LDAPSourcePropertyMapping,
    UserLDAPSourceConnection,
)
from authentik.sources.ldap.sync.forward_delete_users import DELETE_CHUNK_SIZE
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.tasks import ldap_sync, ldap_sync_page
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection
from authentik.sources.ldap.tests.mock_freeipa import mock_freeipa_connection
from authentik.sources.ldap.tests.mock_slapd import (
    group_in_slapd_cn,
    group_in_slapd_uid,
    mock_slapd_connection,
    user_in_slapd_cn,
    user_in_slapd_uid,
)
from authentik.tasks.models import Task

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
            ldap_sync_page.send(self.source.pk, class_to_path(UserLDAPSynchronizer), "foo")

    def test_sync_error(self):
        """Test user sync"""
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        mapping = LDAPSourcePropertyMapping.objects.create(
            name="name",
            expression="q",
        )
        self.source.user_property_mappings.set([mapping])
        self.source.save()
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source, Task())
            with self.assertRaises(StopSync):
                user_sync.sync_full()
            self.assertFalse(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())
        events = Event.objects.filter(
            action=EventAction.CONFIGURATION_ERROR,
            context__message="Failed to evaluate property mapping: 'name'",
            context__mapping__pk=mapping.pk.hex,
        )
        self.assertTrue(events.exists())

    def test_sync_mapping(self):
        """Test property mappings"""
        none = LDAPSourcePropertyMapping.objects.create(
            name=generate_id(), expression="return None"
        )
        byte_mapping = LDAPSourcePropertyMapping.objects.create(
            name=generate_id(), expression="return b''"
        )
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        self.source.user_property_mappings.add(none, byte_mapping)
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))

        # we basically just test that the mappings don't throw errors
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()

    def test_sync_users_ad(self):
        """Test user sync"""
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
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
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()
            user = User.objects.filter(username="user0_sn").first()
            self.assertEqual(user.attributes["foo"], "bar")
            self.assertFalse(user.is_active)
            self.assertEqual(user.path, "goauthentik.io/sources/ldap/users/foo")
            self.assertFalse(User.objects.filter(username="user1_sn").exists())

    def test_sync_users_openldap(self):
        """Test user sync"""
        self.source.object_uniqueness_field = "uid"
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()
            self.assertTrue(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())

    def test_sync_users_freeipa_ish(self):
        """Test user sync (FreeIPA-ish), mainly testing vendor quirks"""
        self.source.object_uniqueness_field = "uid"
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        connection = MagicMock(return_value=mock_freeipa_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()
            self.assertTrue(User.objects.filter(username="user0_sn").exists())
            self.assertFalse(User.objects.filter(username="user1_sn").exists())
            self.assertFalse(User.objects.get(username="user-nsaccountlock").is_active)

    def test_sync_groups_freeipa_memberOf(self):
        """Test group sync when membership is derived from memberOf user attribute"""
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.lookup_groups_from_user = True
        self.source.group_membership_field = "memberOf"
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        self.source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                managed="goauthentik.io/sources/ldap/openldap-cn"
            )
        )
        connection = MagicMock(return_value=mock_freeipa_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()
            group_sync = GroupLDAPSynchronizer(self.source, Task())
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source, Task())
            membership_sync.sync_full()

            self.assertTrue(
                User.objects.filter(username="user4_sn").exists(), "User does not exist"
            )
            # Test if membership mapping based on memberOf works.
            memberof_group = Group.objects.filter(name="reverse-lookup-group")
            self.assertTrue(memberof_group.exists(), "Group does not exist")
            self.assertTrue(
                memberof_group.first().users.filter(username="user4_sn").exists(),
                "User not a member of the group",
            )

    def test_sync_groups_ad(self):
        """Test group sync"""
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        self.source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                managed="goauthentik.io/sources/ldap/default-name"
            )
        )
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            _user = create_test_admin_user()
            parent_group = Group.objects.get(name=_user.username)
            self.source.sync_parent_group = parent_group
            self.source.save()
            group_sync = GroupLDAPSynchronizer(self.source, Task())
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source, Task())
            membership_sync.sync_full()
            group: Group = Group.objects.filter(name="test-group").first()
            self.assertIsNotNone(group)
            self.assertEqual(group.parent, parent_group)

    def test_sync_groups_openldap(self):
        """Test group sync"""
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        self.source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                managed="goauthentik.io/sources/ldap/openldap-cn"
            )
        )
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            self.source.save()
            group_sync = GroupLDAPSynchronizer(self.source, Task())
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source, Task())
            membership_sync.sync_full()
            group = Group.objects.filter(name="group1")
            self.assertTrue(group.exists())

    def test_sync_groups_openldap_posix_group(self):
        """Test posix group sync"""
        self.source.object_uniqueness_field = "cn"
        self.source.group_membership_field = "memberUid"
        self.source.user_object_filter = "(objectClass=posixAccount)"
        self.source.group_object_filter = "(objectClass=posixGroup)"
        self.source.user_membership_attribute = "uid"
        self.source.user_property_mappings.set(
            [
                *LDAPSourcePropertyMapping.objects.filter(
                    Q(managed__startswith="goauthentik.io/sources/ldap/default")
                    | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
                ).all(),
                LDAPSourcePropertyMapping.objects.create(
                    name="name",
                    expression='return {"attributes": {"uid": list_flatten(ldap.get("uid"))}}',
                ),
            ]
        )
        self.source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                managed="goauthentik.io/sources/ldap/openldap-cn"
            )
        )
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            self.source.save()
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()
            group_sync = GroupLDAPSynchronizer(self.source, Task())
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source, Task())
            membership_sync.sync_full()
            # Test if membership mapping based on memberUid works.
            posix_group = Group.objects.filter(name="group-posix").first()
            self.assertTrue(posix_group.users.filter(name="user-posix").exists())

    def test_sync_groups_openldap_posix_group_nonstandard_membership_attribute(self):
        """Test posix group sync"""
        self.source.object_uniqueness_field = "cn"
        self.source.group_membership_field = "memberUid"
        self.source.user_object_filter = "(objectClass=posixAccount)"
        self.source.group_object_filter = "(objectClass=posixGroup)"
        self.source.user_membership_attribute = "cn"
        self.source.user_property_mappings.set(
            [
                *LDAPSourcePropertyMapping.objects.filter(
                    Q(managed__startswith="goauthentik.io/sources/ldap/default")
                    | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
                ).all(),
                LDAPSourcePropertyMapping.objects.create(
                    name="name",
                    expression='return {"attributes": {"cn": list_flatten(ldap.get("cn"))}}',
                ),
            ]
        )
        self.source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                managed="goauthentik.io/sources/ldap/openldap-cn"
            )
        )
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            self.source.save()
            user_sync = UserLDAPSynchronizer(self.source, Task())
            user_sync.sync_full()
            group_sync = GroupLDAPSynchronizer(self.source, Task())
            group_sync.sync_full()
            membership_sync = MembershipLDAPSynchronizer(self.source, Task())
            membership_sync.sync_full()
            # Test if membership mapping based on memberUid works.
            posix_group = Group.objects.filter(name="group-posix").first()
            self.assertTrue(posix_group.users.filter(name="user-posix").exists())

    def test_tasks_ad(self):
        """Test Scheduled tasks"""
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms")
            )
        )
        self.source.save()
        connection = MagicMock(return_value=mock_ad_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)

    def test_tasks_openldap(self):
        """Test Scheduled tasks"""
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap")
            )
        )
        self.source.save()
        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)

    def test_user_deletion(self):
        """Test user deletion"""
        user = User.objects.create_user(username="not-in-the-source")
        UserLDAPSourceConnection.objects.create(
            user=user, source=self.source, identifier="not-in-the-source"
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertFalse(User.objects.filter(username="not-in-the-source").exists())

    def test_user_deletion_still_in_source(self):
        """Test that user is not deleted if it's still in the source"""
        username = user_in_slapd_cn
        identifier = user_in_slapd_uid
        user = User.objects.create_user(username=username)
        UserLDAPSourceConnection.objects.create(
            user=user, source=self.source, identifier=identifier
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertTrue(User.objects.filter(username=username).exists())

    def test_user_deletion_no_sync(self):
        """Test that user is not deleted if sync_users is False"""
        user = User.objects.create_user(username="not-in-the-source")
        UserLDAPSourceConnection.objects.create(
            user=user, source=self.source, identifier="not-in-the-source"
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.sync_users = False
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertTrue(User.objects.filter(username="not-in-the-source").exists())

    def test_user_deletion_no_delete(self):
        """Test that user is not deleted if delete_not_found_objects is False"""
        user = User.objects.create_user(username="not-in-the-source")
        UserLDAPSourceConnection.objects.create(
            user=user, source=self.source, identifier="not-in-the-source"
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertTrue(User.objects.filter(username="not-in-the-source").exists())

    def test_group_deletion(self):
        """Test group deletion"""
        group = Group.objects.create(name="not-in-the-source")
        GroupLDAPSourceConnection.objects.create(
            group=group, source=self.source, identifier="not-in-the-source"
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertFalse(Group.objects.filter(name="not-in-the-source").exists())

    def test_group_deletion_still_in_source(self):
        """Test that group is not deleted if it's still in the source"""
        groupname = group_in_slapd_cn
        identifier = group_in_slapd_uid
        group = Group.objects.create(name=groupname)
        GroupLDAPSourceConnection.objects.create(
            group=group, source=self.source, identifier=identifier
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertTrue(Group.objects.filter(name=groupname).exists())

    def test_group_deletion_no_sync(self):
        """Test that group is not deleted if sync_groups is False"""
        group = Group.objects.create(name="not-in-the-source")
        GroupLDAPSourceConnection.objects.create(
            group=group, source=self.source, identifier="not-in-the-source"
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.sync_groups = False
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertTrue(Group.objects.filter(name="not-in-the-source").exists())

    def test_group_deletion_no_delete(self):
        """Test that group is not deleted if delete_not_found_objects is False"""
        group = Group.objects.create(name="not-in-the-source")
        GroupLDAPSourceConnection.objects.create(
            group=group, source=self.source, identifier="not-in-the-source"
        )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)
        self.assertTrue(Group.objects.filter(name="not-in-the-source").exists())

    def test_batch_deletion(self):
        """Test batch deletion"""
        BATCH_SIZE = DELETE_CHUNK_SIZE + 1
        for i in range(BATCH_SIZE):
            user = User.objects.create_user(username=f"not-in-the-source-{i}")
            group = Group.objects.create(name=f"not-in-the-source-{i}")
            group.users.add(user)
            UserLDAPSourceConnection.objects.create(
                user=user, source=self.source, identifier=f"not-in-the-source-{i}-user"
            )
            GroupLDAPSourceConnection.objects.create(
                group=group, source=self.source, identifier=f"not-in-the-source-{i}-group"
            )
        self.source.object_uniqueness_field = "uid"
        self.source.group_object_filter = "(objectClass=groupOfNames)"
        self.source.delete_not_found_objects = True
        self.source.save()

        connection = MagicMock(return_value=mock_slapd_connection(LDAP_PASSWORD))
        with patch("authentik.sources.ldap.models.LDAPSource.connection", connection):
            ldap_sync.send(self.source.pk)

        self.assertFalse(User.objects.filter(username__startswith="not-in-the-source").exists())
        self.assertFalse(Group.objects.filter(name__startswith="not-in-the-source").exists())
