"""group tests"""

from django.test.testcases import TestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_group, create_test_user
from authentik.lib.generators import generate_id


class TestGroups(TestCase):
    """Test group membership"""

    def test_group_membership_simple(self):
        """Test simple membership"""
        user = create_test_user()
        user2 = create_test_user()
        group = create_test_group()
        other_group = create_test_group()
        group.users.add(user)
        other_group.users.add(user)
        self.assertTrue(group.is_member(user))
        self.assertFalse(group.is_member(user2))

    def test_group_membership_parent(self):
        """Test parent membership"""
        user = create_test_user()
        user2 = create_test_user()
        parent = create_test_group()
        child = create_test_group(parent=parent)
        child.users.add(user)
        self.assertTrue(child.is_member(user))
        self.assertTrue(parent.is_member(user))
        self.assertFalse(child.is_member(user2))
        self.assertFalse(parent.is_member(user2))

    def test_group_membership_parent_extra(self):
        """Test parent membership"""
        user = create_test_user()
        user2 = create_test_user()
        parent = create_test_group()
        second = create_test_group(parent=parent)
        third = create_test_group(parent=second)
        second.users.add(user)
        self.assertTrue(parent.is_member(user))
        self.assertFalse(parent.is_member(user2))
        self.assertTrue(second.is_member(user))
        self.assertFalse(second.is_member(user2))
        self.assertFalse(third.is_member(user))
        self.assertFalse(third.is_member(user2))

    def test_group_membership_recursive(self):
        """Test group membership (recursive)"""
        user = create_test_user()
        group = create_test_group()
        group2 = create_test_group(parent=group)
        group.users.add(user)
        group.parent = group2
        group.save()
        self.assertTrue(group.is_member(user))
        self.assertTrue(group2.is_member(user))
