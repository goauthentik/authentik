"""group tests"""
from django.test.testcases import TestCase

from authentik.core.models import Group, User


class TestGroups(TestCase):
    """Test group membership"""

    def test_group_membership_simple(self):
        """Test simple membership"""
        user = User.objects.create(username="user")
        user2 = User.objects.create(username="user2")
        group = Group.objects.create(name="group")
        group.users.add(user)
        self.assertTrue(group.is_member(user))
        self.assertFalse(group.is_member(user2))

    def test_group_membership_parent(self):
        """Test parent membership"""
        user = User.objects.create(username="user")
        user2 = User.objects.create(username="user2")
        first = Group.objects.create(name="first")
        second = Group.objects.create(name="second", parent=first)
        second.users.add(user)
        self.assertTrue(first.is_member(user))
        self.assertFalse(first.is_member(user2))

    def test_group_membership_parent_extra(self):
        """Test parent membership"""
        user = User.objects.create(username="user")
        user2 = User.objects.create(username="user2")
        first = Group.objects.create(name="first")
        second = Group.objects.create(name="second", parent=first)
        third = Group.objects.create(name="third", parent=second)
        second.users.add(user)
        self.assertTrue(first.is_member(user))
        self.assertFalse(first.is_member(user2))
        self.assertFalse(third.is_member(user))
        self.assertFalse(third.is_member(user2))
