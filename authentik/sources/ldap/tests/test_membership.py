"""LDAP membership reconciliation tests."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.core.models import Group, User
from authentik.lib.generators import generate_id
from authentik.sources.ldap.models import (
    GroupLDAPSourceConnection,
    LDAPSource,
    LDAPSourcePropertyMapping,
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
        scalar_member = User.objects.create(username=generate_id(), attributes={"uid": "scalar"})
        list_member = User.objects.create(username=generate_id(), attributes={"uid": ["list"]})
        departed_member = User.objects.create(
            username=generate_id(), attributes={"uid": ["departed"]}
        )
        empty_member = User.objects.create(username=generate_id(), attributes={"uid": []})
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
        member = User.objects.create(username=generate_id())
        self.group.users.add(member)

        MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data])

        self.assertQuerySetEqual(self.group.users.all(), [member], ordered=False)

    def test_membership_pages(self):
        """Reconciling one group's page must not alter another group's membership."""
        first_dn = "cn=first,dc=example,dc=com"
        second_dn = "cn=second,dc=example,dc=com"
        first_member = User.objects.create(
            username=generate_id(), attributes={"distinguishedName": [first_dn]}
        )
        second_member = User.objects.create(
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
        member = User.objects.create(
            username=generate_id(), attributes={"distinguishedName": [user_dn]}
        )
        self.source.lookup_groups_from_user = True
        self.source.group_membership_field = "memberOf"
        self.connection.extend.standard.paged_search.return_value = [{"dn": user_dn}]

        MembershipLDAPSynchronizer(self.source, Task()).sync([self.group_data])

        self.assertQuerySetEqual(self.group.users.all(), [member], ordered=False)
