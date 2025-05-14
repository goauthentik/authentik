"""Test Groups API"""

from django.urls.base import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id


class TestGroupsAPI(APITestCase):
    """Test Groups API"""

    def setUp(self) -> None:
        self.login_user = create_test_user()
        self.user = create_test_user()

    def test_list_with_users(self):
        """Test listing with users"""
        admin = create_test_admin_user()
        self.client.force_login(admin)
        response = self.client.get(reverse("authentik_api:group-list"), {"include_users": "true"})
        self.assertEqual(response.status_code, 200)

    def test_retrieve_with_users(self):
        """Test retrieve with users"""
        admin = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        self.client.force_login(admin)
        response = self.client.get(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            {"include_users": "true"},
        )
        self.assertEqual(response.status_code, 200)

    def test_add_user(self):
        """Test add_user"""
        group = Group.objects.create(name=generate_id())
        assign_perm("authentik_core.add_user_to_group", self.login_user, group)
        assign_perm("authentik_core.view_user", self.login_user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={
                "pk": self.user.pk,
            },
        )
        self.assertEqual(res.status_code, 204)
        group.refresh_from_db()
        self.assertEqual(list(group.users.all()), [self.user])

    def test_add_user_404(self):
        """Test add_user"""
        group = Group.objects.create(name=generate_id())
        assign_perm("authentik_core.add_user_to_group", self.login_user, group)
        assign_perm("authentik_core.view_user", self.login_user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={
                "pk": self.user.pk + 3,
            },
        )
        self.assertEqual(res.status_code, 404)

    def test_remove_user(self):
        """Test remove_user"""
        group = Group.objects.create(name=generate_id())
        assign_perm("authentik_core.remove_user_from_group", self.login_user, group)
        assign_perm("authentik_core.view_user", self.login_user)
        group.users.add(self.user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-remove-user", kwargs={"pk": group.pk}),
            data={
                "pk": self.user.pk,
            },
        )
        self.assertEqual(res.status_code, 204)
        group.refresh_from_db()
        self.assertEqual(list(group.users.all()), [])

    def test_remove_user_404(self):
        """Test remove_user"""
        group = Group.objects.create(name=generate_id())
        assign_perm("authentik_core.remove_user_from_group", self.login_user, group)
        assign_perm("authentik_core.view_user", self.login_user)
        group.users.add(self.user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-remove-user", kwargs={"pk": group.pk}),
            data={
                "pk": self.user.pk + 3,
            },
        )
        self.assertEqual(res.status_code, 404)

    def test_parent_self(self):
        """Test parent"""
        group = Group.objects.create(name=generate_id())
        assign_perm("view_group", self.login_user, group)
        assign_perm("change_group", self.login_user, group)
        self.client.force_login(self.login_user)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={
                "parent": group.pk,
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_superuser_no_perm(self):
        """Test creating a superuser group without permission"""
        assign_perm("authentik_core.add_group", self.login_user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "is_superuser": True},
        )
        self.assertEqual(res.status_code, 403)
        self.assertJSONEqual(
            res.content,
            {"detail": "User does not have permission to set the given superuser status."},
        )

    def test_superuser_update_object_perm(self):
        """Test updating a superuser group with object permission"""
        group = Group.objects.create(name=generate_id(), is_superuser=False)
        assign_perm("view_group", self.login_user, group)
        assign_perm("change_group", self.login_user, group)
        assign_perm("enable_group_superuser", self.login_user, group)
        self.client.force_login(self.login_user)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"is_superuser": True},
        )
        self.assertEqual(res.status_code, 200)

    def test_superuser_update_no_perm(self):
        """Test updating a superuser group without permission"""
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        assign_perm("view_group", self.login_user, group)
        assign_perm("change_group", self.login_user, group)
        self.client.force_login(self.login_user)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"is_superuser": False},
        )
        self.assertEqual(res.status_code, 403)
        self.assertJSONEqual(
            res.content,
            {"detail": "User does not have permission to set the given superuser status."},
        )

    def test_superuser_update_no_change(self):
        """Test updating a superuser group without permission
        and without changing the superuser status"""
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        assign_perm("view_group", self.login_user, group)
        assign_perm("change_group", self.login_user, group)
        self.client.force_login(self.login_user)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"name": generate_id(), "is_superuser": True},
        )
        self.assertEqual(res.status_code, 200)

    def test_superuser_create(self):
        """Test creating a superuser group with permission"""
        assign_perm("authentik_core.add_group", self.login_user)
        assign_perm("authentik_core.enable_group_superuser", self.login_user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "is_superuser": True},
        )
        self.assertEqual(res.status_code, 201)

    def test_superuser_create_no_perm(self):
        """Test creating a superuser group with no permission"""
        assign_perm("authentik_core.add_group", self.login_user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "is_superuser": True},
        )
        self.assertEqual(res.status_code, 403)
        self.assertJSONEqual(
            res.content,
            {"detail": "User does not have permission to set the given superuser status."},
        )

    def test_no_superuser_create_no_perm(self):
        """Test creating a non-superuser group with no permission"""
        assign_perm("authentik_core.add_group", self.login_user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id()},
        )
        self.assertEqual(res.status_code, 201)
