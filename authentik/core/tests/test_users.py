"""user tests"""

from django.test.testcases import TestCase

from authentik.core.models import User
from authentik.events.models import Event
from authentik.lib.generators import generate_id


class TestUsers(TestCase):
    """Test user"""

    def test_user_managed_role(self):
        """Test user managed role"""
        perm = "authentik_core.view_user"
        user = User.objects.create(username=generate_id())
        user.assign_perms_to_managed_role(perm)
        self.assertEqual(user.roles.count(), 1)
        self.assertTrue(user.has_perm(perm))
        user.remove_perms_from_managed_role(perm)
        self.assertFalse(user.has_perm(perm))

    def test_user_ak_groups(self):
        """Test user.ak_groups is a proxy for user.groups"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(user.ak_groups, user.groups)

    def test_user_ak_groups_event(self):
        """Test user.ak_groups creates exactly one event"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(Event.objects.count(), 0)
        user.ak_groups.all()
        self.assertEqual(Event.objects.count(), 1)
        user.ak_groups.all()
        self.assertEqual(Event.objects.count(), 1)
