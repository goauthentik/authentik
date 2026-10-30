"""Test Groups API field validation"""

from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestGroupsAPIHierarchyRoleValidation(APITestCase):
    """Test that the groups API enforces permission checks on the parents, children,
    roles and users fields, and on the add_user endpoint."""

    def setUp(self) -> None:
        self.actor = create_test_user()

    def test_patch_superuser_parent_no_perm(self):
        """Adding a superuser parent without enable_group_superuser must be rejected."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(group.parents.all()), [])

    def test_patch_superuser_parent_with_perm(self):
        """Adding a superuser parent with enable_group_superuser must succeed."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser")
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.parents.all()), [parent])

    def test_patch_superuser_parent_with_object_perm(self):
        """Adding a superuser parent with enable_group_superuser on the group itself
        must succeed."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.parents.all()), [parent])

    def test_patch_non_superuser_parent_no_perm(self):
        """Adding a non-superuser parent without special permission must succeed."""
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.parents.all()), [parent])

    def test_patch_existing_superuser_parent_no_perm(self):
        """Keeping an existing superuser parent without the permission must succeed."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.parents.all()), [parent])

    def test_put_existing_superuser_parent_no_perm(self):
        """Resubmitting an existing superuser parent in a full update without the permission
        must succeed."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.put(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"name": group.name, "parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.parents.all()), [parent])

    def test_patch_inherited_superuser_parent_no_perm(self):
        """Adding a parent which inherits superuser status from its own parent
        without enable_group_superuser must be rejected."""
        superuser = Group.objects.create(name=generate_id(), is_superuser=True)
        parent = Group.objects.create(name=generate_id())
        parent.parents.add(superuser)
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(group.parents.all()), [])

    def test_create_superuser_parent_no_perm(self):
        """Creating a group with a superuser parent without enable_group_superuser
        must be rejected."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.add_group")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(parent.children.all()), [])

    def test_create_superuser_parent_with_perm(self):
        """Creating a group with a superuser parent with enable_group_superuser must succeed."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.add_group")
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        group = Group.objects.get(pk=res.data["pk"])
        self.assertEqual(list(group.parents.all()), [parent])

    def test_create_non_superuser_parent_no_perm(self):
        """Creating a group with a non-superuser parent without special permission
        must succeed."""
        parent = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.add_group")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        group = Group.objects.get(pk=res.data["pk"])
        self.assertEqual(list(group.parents.all()), [parent])

    def test_create_inherited_superuser_parent_no_perm(self):
        """Creating a group with a parent which inherits superuser status from its own
        parent without enable_group_superuser must be rejected."""
        superuser = Group.objects.create(name=generate_id(), is_superuser=True)
        parent = Group.objects.create(name=generate_id())
        parent.parents.add(superuser)
        self.actor.assign_perms_to_managed_role("authentik_core.add_group")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "parents": [str(parent.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(parent.children.all()), [])

    def test_patch_children_of_superuser_group_is_ignored(self):
        """The children field is read-only, so children cannot be attached to a superuser
        group through the groups API."""
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        child = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", parent)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", parent)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": parent.pk}),
            data={"children": [str(child.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(parent.children.all()), [])
        self.assertEqual(list(child.parents.all()), [])

    def test_patch_role_no_perm(self):
        """Assigning a new role to a group without change_role must be rejected."""
        role = Role.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"roles": [str(role.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(group.roles.all()), [])

    def test_patch_role_with_perm(self):
        """Assigning a new role to a group with change_role must succeed."""
        role = Role.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_rbac.change_role")
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"roles": [str(role.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.roles.all()), [role])

    def test_patch_role_with_object_perm(self):
        """Assigning a new role to a group with change_role on that role alone must be
        rejected."""
        role = Role.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_rbac.change_role", role)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"roles": [str(role.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(group.roles.all()), [])

    def test_patch_existing_role_no_perm(self):
        """Keeping an existing role on a group without change_role must succeed."""
        role = Role.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        group.roles.add(role)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"roles": [str(role.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.roles.all()), [role])

    def test_create_role_no_perm(self):
        """Creating a group with a role without change_role must be rejected."""
        role = Role.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.add_group")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "roles": [str(role.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(role.groups.all()), [])

    def test_create_role_with_perm(self):
        """Creating a group with a role with change_role must succeed."""
        role = Role.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.add_group")
        self.actor.assign_perms_to_managed_role("authentik_rbac.change_role")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-list"),
            data={"name": generate_id(), "roles": [str(role.pk)]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        group = Group.objects.get(pk=res.data["pk"])
        self.assertEqual(list(group.roles.all()), [role])

    def test_patch_users_superuser_group_no_perm(self):
        """Adding a member to a superuser group without enable_group_superuser must be
        rejected."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"users": [target.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(group.users.all()), [])

    def test_patch_users_superuser_group_with_perm(self):
        """Adding a member to a superuser group with enable_group_superuser must succeed."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser")
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"users": [target.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.users.all()), [target])
        self.assertTrue(User.objects.get(pk=target.pk).is_superuser)

    def test_patch_users_superuser_group_with_object_perm(self):
        """Adding a member to a superuser group with enable_group_superuser on the group
        itself must succeed."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"users": [target.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.users.all()), [target])

    def test_patch_users_inherited_superuser_group_no_perm(self):
        """Adding a member to a group which inherits superuser status without
        enable_group_superuser must be rejected."""
        target = create_test_user()
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"users": [target.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(list(group.users.all()), [])

    def test_patch_users_non_superuser_group_no_perm(self):
        """Adding a member to a group whose parent is not a superuser group without
        special permission must succeed."""
        target = create_test_user()
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"users": [target.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.users.all()), [target])
        self.assertFalse(User.objects.get(pk=target.pk).is_superuser)

    def test_patch_users_existing_member_superuser_group_no_perm(self):
        """Re-submitting an existing member of a superuser group without
        enable_group_superuser must succeed."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        group.users.add(target)
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.change_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"users": [target.pk]},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_user_superuser_group_no_perm(self):
        """Adding a member to a superuser group via the add_user endpoint without
        enable_group_superuser must be rejected."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(list(group.users.all()), [])

    def test_add_user_superuser_group_with_perm(self):
        """Adding a member to a superuser group via the add_user endpoint with
        enable_group_superuser must succeed."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])
        self.assertTrue(User.objects.get(pk=target.pk).is_superuser)

    def test_add_user_superuser_group_with_object_perm(self):
        """Adding a member to a superuser group via the add_user endpoint with
        enable_group_superuser on the group itself must succeed."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.actor.assign_perms_to_managed_role("authentik_core.enable_group_superuser", group)
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_user_inherited_superuser_group_no_perm(self):
        """Adding a member via the add_user endpoint to a group which inherits superuser
        status without enable_group_superuser must be rejected."""
        target = create_test_user()
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(list(group.users.all()), [])

    def test_add_user_non_superuser_group_no_perm(self):
        """Adding a member via the add_user endpoint to a group whose parent is not a
        superuser group without special permission must succeed."""
        target = create_test_user()
        parent = Group.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])
        self.assertFalse(User.objects.get(pk=target.pk).is_superuser)

    def test_add_user_existing_member_superuser_group_no_perm(self):
        """Re-adding an existing member of a superuser group via the add_user endpoint
        without enable_group_superuser must succeed."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        group.users.add(target)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_user_superuser_group_global_add_user_to_group(self):
        """Adding a member to a superuser group via the add_user endpoint with
        add_user_to_group held globally and no permission on the group must be rejected."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group")
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(list(group.users.all()), [])

    def test_add_user_inherited_superuser_group_global_add_user_to_group(self):
        """Adding a member via the add_user endpoint to a group which inherits superuser
        status from its parent, with add_user_to_group held globally and no permission on
        the group, must be rejected."""
        target = create_test_user()
        parent = Group.objects.create(name=generate_id(), is_superuser=True)
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group")
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(list(group.users.all()), [])
