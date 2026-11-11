"""LDAP Provider API tests"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import (
    create_test_admin_user,
    create_test_flow,
    create_test_user,
)
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.ldap.models import LDAPProvider


class TestLDAPProviderAPI(APITestCase):
    """LDAP Provider API tests"""

    def test_outpost_application(self):
        """Test outpost-like provider retrieval (direct connection)"""
        provider = LDAPProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        user = create_test_admin_user()
        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:ldapprovideroutpost-list"))
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertEqual(data["pagination"]["count"], 1)
        self.assertEqual(len(data["results"]), 1)

    def test_outpost_application_backchannel(self):
        """Test outpost-like provider retrieval (backchannel connection)"""
        provider = LDAPProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        app.backchannel_providers.add(provider)
        user = create_test_admin_user()
        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:ldapprovideroutpost-list"))
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertEqual(data["pagination"]["count"], 1)
        self.assertEqual(len(data["results"]), 1)


class TestLDAPSearchVisibility(APITestCase):
    """Test the search_visibility endpoint used by `limit_search_to_application_access`"""

    def setUp(self):
        self.admin = create_test_admin_user()
        self.provider = LDAPProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            limit_search_to_application_access=True,
        )
        self.app = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=self.provider,
        )
        self.parent = Group.objects.create(name=generate_id())
        self.allowed_group = Group.objects.create(name=generate_id())
        self.allowed_group.parents.add(self.parent)
        self.other_group = Group.objects.create(name=generate_id())
        self.allowed = create_test_user()
        self.allowed_group.users.add(self.allowed)
        self.other = create_test_user()
        self.other_group.users.add(self.other)

    def _get(self) -> dict:
        self.client.force_login(self.admin)
        res = self.client.get(
            reverse(
                "authentik_api:ldapprovideroutpost-search-visibility",
                kwargs={"pk": self.provider.pk},
            )
        )
        self.assertEqual(res.status_code, 200)
        return loads(res.content.decode())

    def test_no_bindings(self):
        """Without bindings every user can access the application, so every user is visible"""
        data = self._get()
        self.assertIn(self.allowed.pk, data["users"])
        self.assertIn(self.other.pk, data["users"])
        self.assertIn(str(self.other_group.pk), data["groups"])

    def test_group_binding(self):
        """A group binding limits users to members, and groups to theirs plus ancestors"""
        PolicyBinding.objects.create(target=self.app, group=self.allowed_group, order=0)
        data = self._get()
        self.assertIn(self.allowed.pk, data["users"])
        self.assertNotIn(self.other.pk, data["users"])
        self.assertIn(str(self.allowed_group.pk), data["groups"])
        self.assertIn(str(self.parent.pk), data["groups"])
        self.assertNotIn(str(self.other_group.pk), data["groups"])

    def test_child_group_binding(self):
        """Binding a parent group includes members of its descendants"""
        PolicyBinding.objects.create(target=self.app, group=self.parent, order=0)
        data = self._get()
        self.assertIn(self.allowed.pk, data["users"])
        self.assertNotIn(self.other.pk, data["users"])

    def test_backchannel_application(self):
        """The backchannel application's bindings are used when set"""
        self.app.provider = None
        self.app.save()
        backchannel_app = Application.objects.create(name=generate_id(), slug=generate_id())
        backchannel_app.backchannel_providers.add(self.provider)
        PolicyBinding.objects.create(target=backchannel_app, user=self.other, order=0)
        data = self._get()
        self.assertEqual(data["users"], [self.other.pk])

    def test_permission_denied(self):
        """Viewing the provider alone is not enough to list visible users"""
        user = create_test_user()
        user.assign_perms_to_managed_role(
            "authentik_providers_ldap.view_ldapprovider", self.provider
        )
        self.client.force_login(user)
        res = self.client.get(
            reverse(
                "authentik_api:ldapprovideroutpost-search-visibility",
                kwargs={"pk": self.provider.pk},
            )
        )
        self.assertEqual(res.status_code, 403)
