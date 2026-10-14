"""Test cache invalidation when group membership changes"""

from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.api.applications import user_app_cache_key
from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding


class TestMembershipCacheInvalidation(APITestCase):
    """Group membership changes invalidate cached application lists"""

    def setUp(self) -> None:
        cache.clear()
        self.user = create_test_user()
        self.group = Group.objects.create(name=generate_id())
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        PolicyBinding.objects.create(target=self.app, group=self.group, order=0)
        self.client.force_login(self.user)

    def _slugs(self) -> list[str]:
        response = self.client.get(reverse("authentik_api:application-list"))
        self.assertEqual(response.status_code, 200)
        return [app["slug"] for app in response.json()["results"]]

    def _user_keys(self, user) -> list[str]:
        return cache.keys(f"{user_app_cache_key(user.pk)}*") or []

    def test_group_users_add_remove(self):
        """Adding and removing a user via group.users changes the list without other saves"""
        self.assertNotIn(self.app.slug, self._slugs())
        self.assertTrue(self._user_keys(self.user))
        self.group.users.add(self.user)
        self.assertFalse(self._user_keys(self.user))
        self.assertIn(self.app.slug, self._slugs())
        self.assertTrue(self._user_keys(self.user))
        self.group.users.remove(self.user)
        self.assertFalse(self._user_keys(self.user))
        self.assertNotIn(self.app.slug, self._slugs())

    def test_user_groups_add_remove(self):
        """Adding and removing a group via user.groups changes the list"""
        self.assertNotIn(self.app.slug, self._slugs())
        self.user.groups.add(self.group)
        self.assertIn(self.app.slug, self._slugs())
        self.user.groups.remove(self.group)
        self.assertNotIn(self.app.slug, self._slugs())

    def test_clear(self):
        """Clearing from either side invalidates the affected users"""
        self.group.users.add(self.user)
        self.assertIn(self.app.slug, self._slugs())
        self.group.users.clear()
        self.assertFalse(self._user_keys(self.user))
        self.assertNotIn(self.app.slug, self._slugs())
        self.user.groups.add(self.group)
        self.assertIn(self.app.slug, self._slugs())
        self.user.groups.clear()
        self.assertFalse(self._user_keys(self.user))
        self.assertNotIn(self.app.slug, self._slugs())

    def test_other_users_untouched(self):
        """A membership change leaves other users' keys, including pk prefixes, in place"""
        other = create_test_user()
        cache.set(user_app_cache_key(other.pk), ["x"])
        cache.set(user_app_cache_key(other.pk, page_number=1), ["x"])
        self.group.users.add(self.user)
        self.assertEqual(len(self._user_keys(other)), 2)

    def test_group_parents_change(self):
        """Changing group parents clears every cached application list"""
        child = Group.objects.create(name=generate_id())
        self.assertNotIn(self.app.slug, self._slugs())
        child.users.add(self.user)
        self._slugs()
        self.assertTrue(self._user_keys(self.user))
        child.parents.add(self.group)
        self.assertFalse(self._user_keys(self.user))
        self.assertIn(self.app.slug, self._slugs())
        child.parents.remove(self.group)
        self.assertNotIn(self.app.slug, self._slugs())
