"""Test Groups API delegated member management"""

from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestGroupsAPIDelegatedMemberManagement(APITestCase):
    """Test the delegated group member management setup documented in
    users-sources/groups/manage_groups.mdx: `view_group`, `add_user_to_group` and
    `remove_user_from_group` on the group object, plus `access_admin_interface` and
    `view_user`, assigned to a role which the delegated administrators belong to."""

    def setUp(self) -> None:
        self.actor = create_test_user()

    def test_add_member(self):
        """The documented permissions must allow adding a member to an ordinary group."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_remove_member(self):
        """The documented permissions must allow removing a member."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        group.users.add(target)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-remove-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [])

    def test_add_member_permissions_on_the_user(self):
        """The documented permissions must allow adding a member when `view_user` is granted
        on the user rather than globally."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user", target)
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_member_permissions_on_the_user_account(self):
        """The documented permissions must allow adding a member when they are assigned to
        the administrator directly rather than through a shared role."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        self.actor.assign_perms_to_managed_role("authentik_core.view_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.add_user_to_group", group)
        self.actor.assign_perms_to_managed_role("authentik_core.remove_user_from_group", group)
        self.actor.assign_perms_to_managed_role("authentik_rbac.access_admin_interface")
        self.actor.assign_perms_to_managed_role("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_member_group_with_read_only_role(self):
        """The documented permissions must allow adding a member to a group which has a role
        granting only read access, the shape a default installation ships."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        read_only = Role.objects.create(name=generate_id())
        read_only.assign_perms("authentik_core.view_user")
        read_only.assign_perms("authentik_core.view_group")
        read_only.assign_perms("authentik_rbac.access_admin_interface")
        group.roles.add(read_only)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_member_group_with_read_only_role_on_parent(self):
        """The documented permissions must allow adding a member to a group which inherits
        a role granting only read access from a parent group."""
        target = create_test_user()
        read_only = Role.objects.create(name=generate_id())
        read_only.assign_perms("authentik_core.view_user")
        parent = Group.objects.create(name=generate_id())
        parent.roles.add(read_only)
        group = Group.objects.create(name=generate_id())
        group.parents.add(parent)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_member_group_with_management_role(self):
        """The documented permissions must allow adding a member to a group whose role
        grants management permissions."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        management = Role.objects.create(name=generate_id())
        management.assign_perms("authentik_core.change_user")
        group.roles.add(management)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_member_superuser_group(self):
        """The documented permissions are not sufficient for a superuser group."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(list(group.users.all()), [])
        self.assertFalse(User.objects.get(pk=target.pk).is_superuser)

    def test_remove_member_superuser_group(self):
        """Removing a member stays available for a superuser group."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        group.users.add(target)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-remove-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [])

    def test_add_member_existing_member_superuser_group(self):
        """Re-adding an existing member stays available for a superuser group."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id(), is_superuser=True)
        group.users.add(target)
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(list(group.users.all()), [target])

    def test_add_member_role_on_the_managed_group(self):
        """The documented permissions must allow adding a member when the role carrying
        them is assigned to the managed group itself rather than to the administrators'
        group."""
        target = create_test_user()
        group = Group.objects.create(name=generate_id())
        group.users.add(self.actor)
        delegation = Role.objects.create(name=generate_id())
        group.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.post(
            reverse("authentik_api:group-add-user", kwargs={"pk": group.pk}),
            data={"pk": target.pk},
        )
        self.assertEqual(res.status_code, 204)
        self.assertCountEqual(group.users.all(), [self.actor, target])

    def test_add_member_does_not_allow_editing_the_group(self):
        """The documented permissions must not allow editing the group itself."""
        group = Group.objects.create(name=generate_id())
        admins = Group.objects.create(name=generate_id())
        self.actor.groups.add(admins)
        delegation = Role.objects.create(name=generate_id())
        admins.roles.add(delegation)
        delegation.assign_perms("authentik_core.view_group", group)
        delegation.assign_perms("authentik_core.add_user_to_group", group)
        delegation.assign_perms("authentik_core.remove_user_from_group", group)
        delegation.assign_perms("authentik_rbac.access_admin_interface")
        delegation.assign_perms("authentik_core.view_user")
        self.client.force_login(self.actor)
        res = self.client.patch(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            data={"name": generate_id()},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)
