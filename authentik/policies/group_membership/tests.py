"""evaluator tests"""
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Group
from authentik.policies.group_membership.models import GroupMembershipPolicy
from authentik.policies.types import PolicyRequest


class TestGroupMembershipPolicy(TestCase):
    """GroupMembershipPolicy tests"""

    def setUp(self):
        self.request = PolicyRequest(user=get_anonymous_user())

    def test_invalid(self):
        """user not in group"""
        group = Group.objects.create(name="test")
        policy: GroupMembershipPolicy = GroupMembershipPolicy.objects.create(
            group=group
        )
        self.assertFalse(policy.passes(self.request).passing)

    def test_valid(self):
        """user in group"""
        group = Group.objects.create(name="test")
        group.users.add(get_anonymous_user())
        group.save()
        policy: GroupMembershipPolicy = GroupMembershipPolicy.objects.create(
            group=group
        )
        self.assertTrue(policy.passes(self.request).passing)
