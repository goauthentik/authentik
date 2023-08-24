"""group tests"""
from django.test.testcases import TestCase

from authentik.core.models import Group, User
from authentik.lib.generators import generate_id


class TestGroups(TestCase):
    """Test group membership"""

    def test_group_membership_simple(self):
        """Test simple membership"""
        user = User.objects.create(username=generate_id())
        user2 = User.objects.create(username=generate_id())
        group = Group.objects.create(name=generate_id())
        other_group = Group.objects.create(name=generate_id())
        group.users.add(user)
        other_group.users.add(user)
        self.assertTrue(group.is_member(user))
        self.assertFalse(group.is_member(user2))

    def test_group_membership_parent(self):
        """Test parent membership"""
        user = User.objects.create(username=generate_id())
        user2 = User.objects.create(username=generate_id())
        parent = Group.objects.create(name=generate_id())
        child = Group.objects.create(name=generate_id(), parent=parent)
        child.users.add(user)
        self.assertTrue(child.is_member(user))
        self.assertTrue(parent.is_member(user))
        self.assertFalse(child.is_member(user2))
        self.assertFalse(parent.is_member(user2))

    def test_group_membership_parent_extra(self):
        """Test parent membership"""
        user = User.objects.create(username=generate_id())
        user2 = User.objects.create(username=generate_id())
        parent = Group.objects.create(name=generate_id())
        second = Group.objects.create(name=generate_id(), parent=parent)
        third = Group.objects.create(name=generate_id(), parent=second)
        second.users.add(user)
        self.assertTrue(parent.is_member(user))
        self.assertFalse(parent.is_member(user2))
        self.assertTrue(second.is_member(user))
        self.assertFalse(second.is_member(user2))
        self.assertFalse(third.is_member(user))
        self.assertFalse(third.is_member(user2))

    def test_group_membership_recursive(self):
        """Test group membership (recursive)"""
        user = User.objects.create(username=generate_id())
        group = Group.objects.create(name=generate_id())
        group2 = Group.objects.create(name=generate_id(), parent=group)
        group.users.add(user)
        group.parent = group2
        group.save()
        self.assertTrue(group.is_member(user))
        self.assertTrue(group2.is_member(user))
