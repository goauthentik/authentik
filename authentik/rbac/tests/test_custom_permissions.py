from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase
from django.urls import reverse
from guardian.models import RoleModelPermission
from rest_framework.test import APITestCase

from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import CUSTOM_PERMISSION_PREFIX, CustomPermission, Role


class TestBuiltinPermissions(SimpleTestCase):
    """The prefix of custom permissions is not used by authentik"""

    def test_no_builtin_uses_custom_prefix(self):
        builtin = [
            f"{model._meta.label_lower}.{codename}"
            for model in apps.get_models()
            for codename in self.builtin_codenames(model)
            if codename.startswith(CUSTOM_PERMISSION_PREFIX)
        ]
        self.assertEqual(builtin, [], f"Codenames prefixed {CUSTOM_PERMISSION_PREFIX} are reserved")

    @staticmethod
    def builtin_codenames(model) -> list[str]:
        defaults = [
            f"{action}_{model._meta.model_name}" for action in model._meta.default_permissions
        ]
        return defaults + [codename for codename, name in model._meta.permissions]


class TestCustomPermissions(APITestCase):
    def setUp(self):
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.client.force_login(self.user)
        self.list_url = reverse("authentik_api:custompermission-list")

    def create(self, codename: str = "custom_rename", model=Group) -> CustomPermission:
        return CustomPermission.objects.create(
            codename=codename,
            name=generate_id(),
            content_type=ContentType.objects.get_for_model(model),
        )

    def detail_url(self, permission: CustomPermission) -> str:
        return reverse("authentik_api:custompermission-detail", kwargs={"pk": permission.pk})

    def test_create(self):
        data = {"codename": "custom_rename", "name": "Can rename", "model": "authentik_core.group"}
        self.assertEqual(self.client.post(self.list_url, data).status_code, 403)
        self.role.assign_perms("authentik_rbac.add_custompermission")
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["permission"], "authentik_core.custom_rename")

    def test_codename_rules(self):
        self.role.assign_perms("authentik_rbac.add_custompermission")
        for codename in ["rename", "custom_", "custom_Rename", "custom_a.b", "custom_" + "a" * 94]:
            data = {"codename": codename, "name": "x", "model": "authentik_core.group"}
            self.assertEqual(self.client.post(self.list_url, data).status_code, 400, codename)

    def test_unique_per_model(self):
        self.create()
        self.role.assign_perms("authentik_rbac.add_custompermission")
        data = {"codename": "custom_rename", "name": "Rename", "model": "authentik_core.group"}
        self.assertEqual(self.client.post(self.list_url, data).status_code, 400)
        data["model"] = "authentik_core.application"
        self.assertEqual(self.client.post(self.list_url, data).status_code, 201)

    def test_codename_and_model_are_immutable(self):
        url = self.detail_url(self.create())
        self.role.assign_perms("authentik_rbac.change_custompermission")
        self.assertEqual(self.client.patch(url, {"codename": "custom_other"}).status_code, 400)
        self.assertEqual(self.client.patch(url, {"model": "authentik_core.user"}).status_code, 400)
        self.assertEqual(self.client.patch(url, {"name": "Renamed"}).status_code, 200)

    def test_lists_only_custom_permissions(self):
        self.create()
        response = self.client.get(self.list_url)
        self.assertEqual([p["codename"] for p in response.json()["results"]], ["custom_rename"])

    def test_delete_removes_assignments(self):
        permission = self.create()
        self.role.assign_perms("authentik_core.custom_rename")
        self.role.assign_perms("authentik_rbac.delete_custompermission")
        self.assertEqual(self.client.delete(self.detail_url(permission)).status_code, 204)
        self.assertFalse(RoleModelPermission.objects.filter(permission_id=permission.pk).exists())

    def test_object_permissions(self):
        self.create()
        group = Group.objects.create(name=generate_id())
        other = Group.objects.create(name="x")
        self.role.assign_perms("authentik_core.custom_rename", group)
        self.assertTrue(self.user.has_perm("authentik_core.custom_rename", group))
        self.assertFalse(self.user.has_perm("authentik_core.custom_rename", other))
        self.assertFalse(self.user.has_perm("authentik_core.custom_rename"))

    def test_system_permission(self):
        self.create("custom_view_runtime", apps.get_model("authentik_rbac.systempermission"))
        self.role.assign_perms("authentik_rbac.custom_view_runtime")
        self.assertTrue(self.user.has_perm("authentik_rbac.custom_view_runtime"))

    def test_blueprint(self):
        role_name = generate_id()
        importer = Importer.from_string(f"""
version: 1
entries:
  - model: authentik_rbac.custompermission
    identifiers:
      codename: custom_add_service_account
    attrs:
      name: Can add service accounts
      model: authentik_core.user
  - model: authentik_rbac.role
    identifiers:
      name: {role_name}
    attrs:
      permissions:
        - authentik_core.custom_add_service_account
""")
        self.assertTrue(importer.validate()[0])
        self.assertTrue(importer.apply())
        user = create_test_user()
        user.roles.add(Role.objects.get(name=role_name))
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user.has_perm("authentik_core.custom_add_service_account"))
