"""LDAP membership reconciliation tests."""

from unittest.mock import MagicMock, patch

from django.db import transaction
from django.db.models.signals import m2m_changed
from django.test import TestCase

from authentik.core.models import Group, User, UserGroup
from authentik.lib.generators import generate_id
from authentik.sources.ldap.models import (
    GroupLDAPSourceConnection,
    LDAPSource,
    LDAPSourcePropertyMapping,
    UserLDAPSourceConnection,
)
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.tasks.models import Task


class LDAPMembershipSyncTests(TestCase):
    """Membership matching must tolerate single-valued LDAP attribute lists."""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            base_dn="dc=example,dc=com",
            object_uniqueness_field="uid",
        )
        self.group = Group.objects.create(name=generate_id())
        GroupLDAPSourceConnection.objects.create(
            source=self.source, group=self.group, identifier="group"
        )
        self.group_data = {
            "dn": "cn=group,dc=example,dc=com",
            "attributes": {"uid": "group", "member": []},
        }
        self.connection = MagicMock()
        self.enterContext(
            patch(
                "authentik.sources.ldap.models.LDAPSource.connection",
                return_value=self.connection,
            )
        )

    def create_connected_user(self, **kwargs):
        user = User.objects.create(**kwargs)
        UserLDAPSourceConnection.objects.create(
            source=self.source, user=user, identifier=generate_id()
        )
        return user

    def test_repeated_sync_with_list_property_mapping(self):
        """A mapping returning a list must not remove an existing LDAP membership."""
        mapping = LDAPSourcePropertyMapping.objects.create(
            name=generate_id(),
            expression="""return {
                "username": ldap.get("uid"),
                "attributes": {"distinguishedName": ldap.get("distinguishedName")},
            }""",
        )
        self.source.user_property_mappings.add(mapping)
        user_dn = "cn=user,dc=example,dc=com"
        user_data = {
            "dn": user_dn,
            "attributes": {"uid": "user", "distinguishedName": user_dn},
        }
        self.group_data["attributes"]["member"] = [user_dn]

        for membership_value in (user_dn, [user_dn], [user_dn]):
            with self.subTest(membership_value=membership_value):
                user_data["attributes"]["distinguishedName"] = membership_value
                self.assertEqual(UserLDAPSynchronizer(self.source, Task()).sync([user_data]), 1)
                user = User.objects.get(username="user")
                self.assertEqual(user.attributes["distinguishedName"], membership_value)
                MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data])
                self.assertQuerySetEqual(self.group.users.all(), [user], ordered=False)

    def test_custom_membership_attribute(self):
        """Match scalar and singleton-list identifiers without retaining departed members."""
        self.source.user_membership_attribute = "uid"
        self.source.group_membership_field = "memberUid"
        scalar_member = self.create_connected_user(
            username=generate_id(), attributes={"uid": "scalar"}
        )
        list_member = self.create_connected_user(
            username=generate_id(), attributes={"uid": ["list"]}
        )
        departed_member = self.create_connected_user(
            username=generate_id(), attributes={"uid": ["departed"]}
        )
        empty_member = self.create_connected_user(username=generate_id(), attributes={"uid": []})
        self.group.users.set([scalar_member, list_member, departed_member, empty_member])
        self.group_data["attributes"]["memberUid"] = ["scalar", "list"]

        synchronizer = MembershipLDAPSynchronizer(self.source, Task())
        for _ in range(2):
            synchronizer.sync([self.group_data])
            self.assertQuerySetEqual(
                self.group.users.all(), [scalar_member, list_member], ordered=False
            )

        self.group_data["attributes"]["memberUid"] = []
        synchronizer.sync([self.group_data])
        self.assertFalse(self.group.users.exists())

    def test_missing_membership_attribute(self):
        """Preserve the existing fallback for members without a matching attribute."""
        member = self.create_connected_user(username=generate_id())
        self.group.users.add(member)

        MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data])

        self.assertQuerySetEqual(self.group.users.all(), [member], ordered=False)

    def test_membership_pages(self):
        """Reconciling one group's page must not alter another group's membership."""
        first_dn = "cn=first,dc=example,dc=com"
        second_dn = "cn=second,dc=example,dc=com"
        first_member = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": [first_dn]}
        )
        second_member = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": second_dn}
        )
        second_group = Group.objects.create(name=generate_id())
        GroupLDAPSourceConnection.objects.create(
            source=self.source, group=second_group, identifier="second-group"
        )
        second_group_data = {
            "dn": "cn=second-group,dc=example,dc=com",
            "attributes": {"uid": "second-group", "member": [second_dn]},
        }
        self.group_data["attributes"]["member"] = [first_dn]

        synchronizer = MembershipLDAPSynchronizer(self.source, Task())
        for _ in range(2):
            synchronizer.sync([self.group_data])
            synchronizer.sync([second_group_data])
            self.assertQuerySetEqual(self.group.users.all(), [first_member], ordered=False)
            self.assertQuerySetEqual(second_group.users.all(), [second_member], ordered=False)

    def test_reverse_lookup_with_list_attribute(self):
        """Reverse LDAP searches also match a list-valued distinguished name."""
        user_dn = "cn=user,dc=example,dc=com"
        member = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": [user_dn]}
        )
        self.source.lookup_groups_from_user = True
        self.source.group_membership_field = "memberOf"
        self.connection.extend.standard.paged_search.return_value = [{"dn": user_dn}]

        MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data])

        self.assertQuerySetEqual(self.group.users.all(), [member], ordered=False)

    def test_membership_changes_preserve_signals_and_existing_rows(self):
        """Only changed memberships notify audit and outgoing sync signal receivers."""
        retained = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": "retained"}
        )
        departed = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": "departed"}
        )
        added = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": ["added"]}
        )
        retained_membership = UserGroup.objects.create(user=retained, group=self.group)
        UserGroup.objects.create(user=departed, group=self.group)
        self.group_data["attributes"]["member"] = ["retained", "added"]
        receiver = MagicMock()
        m2m_changed.connect(receiver, sender=UserGroup)
        self.addCleanup(m2m_changed.disconnect, receiver, sender=UserGroup)

        synchronizer = MembershipLDAPSynchronizer(self.source, Task())
        self.assertEqual(synchronizer.sync([self.group_data]), 3)

        self.assertEqual(
            [(call.kwargs["action"], call.kwargs["pk_set"]) for call in receiver.call_args_list],
            [
                ("pre_remove", {departed.pk}),
                ("post_remove", {departed.pk}),
                ("pre_add", {added.pk}),
                ("post_add", {added.pk}),
            ],
        )
        for call in receiver.call_args_list:
            self.assertEqual(call.kwargs["instance"], self.group)
            self.assertTrue(call.kwargs["reverse"])
            self.assertIs(call.kwargs["model"], User)
        self.assertEqual(
            set(UserGroup.objects.filter(group=self.group).values_list("user_id", flat=True)),
            {retained.pk, added.pk},
        )
        retained_membership.refresh_from_db()

        receiver.reset_mock()
        self.assertEqual(synchronizer.sync([self.group_data]), 3)
        receiver.assert_not_called()
        retained_membership.refresh_from_db()

    def test_membership_changes_are_atomic(self):
        """A failed addition rolls back removals from the same reconciliation."""
        departed = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": "departed"}
        )
        added = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": "added"}
        )
        membership = UserGroup.objects.create(user=departed, group=self.group)
        self.group_data["attributes"]["member"] = ["added"]

        with patch.object(type(self.group.users), "add", side_effect=RuntimeError("add failed")):
            with self.assertRaisesMessage(RuntimeError, "add failed"):
                with transaction.atomic():
                    MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data])

        membership.refresh_from_db()
        self.assertFalse(UserGroup.objects.filter(user=added, group=self.group).exists())

    def test_only_current_source_connections_are_matched(self):
        """Matching attributes alone do not associate users with the current LDAP source."""
        member = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": ["member"]}
        )
        unconnected = User.objects.create(
            username=generate_id(), attributes={"distinguishedName": "member"}
        )
        other_source_member = User.objects.create(
            username=generate_id(), attributes={"distinguishedName": ["member"]}
        )
        other_source = LDAPSource.objects.create(name=generate_id(), slug=generate_id())
        UserLDAPSourceConnection.objects.create(
            source=other_source, user=other_source_member, identifier=generate_id()
        )
        self.group_data["attributes"]["member"] = ["member"]

        synchronizer = MembershipLDAPSynchronizer(self.source, Task())
        for existing_members in ([], [unconnected, other_source_member]):
            with self.subTest(existing_members=existing_members):
                self.group.users.set(existing_members)
                self.assertEqual(synchronizer.sync([self.group_data]), 2)
                self.assertQuerySetEqual(self.group.users.all(), [member], ordered=False)

    def test_missing_attribute_fallback_is_source_scoped(self):
        """Only connected existing members qualify for the missing-attribute fallback."""
        retained = self.create_connected_user(username=generate_id())
        unconnected = User.objects.create(username=generate_id())
        other_source_member = User.objects.create(username=generate_id())
        other_source = LDAPSource.objects.create(name=generate_id(), slug=generate_id())
        UserLDAPSourceConnection.objects.create(
            source=other_source, user=other_source_member, identifier=generate_id()
        )
        not_a_member = self.create_connected_user(username=generate_id())
        self.group.users.set([retained, unconnected, other_source_member])

        self.assertEqual(MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data]), 2)

        self.assertQuerySetEqual(self.group.users.all(), [retained], ordered=False)
        self.assertFalse(self.group.users.filter(pk=not_a_member.pk).exists())

    def test_user_connected_to_multiple_sources(self):
        """A user connected to this source and another source is still matched once."""
        member = self.create_connected_user(
            username=generate_id(), attributes={"distinguishedName": "member"}
        )
        other_source = LDAPSource.objects.create(name=generate_id(), slug=generate_id())
        UserLDAPSourceConnection.objects.create(
            source=other_source, user=member, identifier=generate_id()
        )
        self.group_data["attributes"]["member"] = ["member"]

        self.assertEqual(MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data]), 2)

        self.assertQuerySetEqual(self.group.users.all(), [member], ordered=False)
