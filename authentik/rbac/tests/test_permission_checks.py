from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.models import CustomPermission, PermissionCheck, Role

DENY = """
def has_permission(request):
    return False
"""


def create_custom_permission(codename: str, model: type[Model]) -> CustomPermission:
    return CustomPermission.objects.create(
        codename=codename, name=codename, content_type=ContentType.objects.get_for_model(model)
    )


class PermissionCheckTestCase(APITestCase):
    """A user with a role, and helpers to bind checks"""

    def setUp(self):
        EnableCustomPermissions.set(True)
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.client.force_login(self.user)

    def bind(self, expression: str, *endpoints: str) -> PermissionCheck:
        return PermissionCheck.objects.create(
            name=generate_id(), expression=expression, endpoints=list(endpoints)
        )

    def group_names(self) -> list[str]:
        response = self.client.get(reverse("authentik_api:group-list"))
        return sorted(group["name"] for group in response.json()["results"])


class TestDecisions(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.role.assign_perms("authentik_core.view_group")
        self.url = reverse("authentik_api:group-list")
        self.system = reverse("authentik_api:admin_system")

    def test_false_forbids(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.bind(DENY, "core/groups:list")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_true_keeps_decision(self):
        self.bind("def has_permission(request):\n    return True", "admin/system:get")
        self.assertEqual(self.client.get(self.system).status_code, 403)

    def test_skip_exception_grants(self):
        self.bind(
            "def has_permission(request):\n    raise PermissionCheckSkipException",
            "admin/system:get",
        )
        self.assertEqual(self.client.get(self.system).status_code, 200)

    def test_superuser_skips_checks(self):
        self.bind(DENY, "core/groups:list")
        self.client.force_login(create_test_admin_user())
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_outposts_run_checks(self):
        self.bind(DENY, "core/groups:list")
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_exception_forbids(self):
        self.bind("def has_permission(request):\n    raise ValueError", "core/groups:list")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_non_bool_forbids(self):
        self.bind("def has_permission(request):\n    return 1", "core/groups:list")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_narrow_list(self):
        kept = Group.objects.create(name=generate_id())
        Group.objects.create(name=generate_id())
        self.bind(
            f"def narrow_list(request, queryset):\n    return queryset.filter(name='{kept.name}')",
            "core/groups:list",
        )
        self.assertEqual(self.group_names(), [kept.name])

    def test_narrow_list_wrong_type_forbids(self):
        self.bind(
            "def narrow_list(request, queryset):\n    return ak_user_by()", "core/groups:list"
        )
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_retrieve_agrees_with_list(self):
        kept = Group.objects.create(name=generate_id())
        hidden = Group.objects.create(name="x")
        self.bind(
            f"def narrow_list(request, queryset):\n    return queryset.filter(pk='{kept.pk}')",
            "core/groups:list",
        )
        detail = "authentik_api:group-detail"
        response = self.client.get(reverse(detail, kwargs={"pk": kept.pk}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse(detail, kwargs={"pk": hidden.pk}))
        self.assertEqual(response.status_code, 404)


class TestLists(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.visible = Group.objects.create(name=generate_id())
        self.hidden = Group.objects.create(name=generate_id())
        self.role.assign_perms("authentik_core.view_group", self.visible)

    def test_narrow_list_cannot_widen(self):
        self.bind(
            "def narrow_list(request, queryset):\n    return queryset.model.objects.all()",
            "core/groups:list",
        )
        self.assertEqual(self.group_names(), [self.visible.name])

    def test_widen_list(self):
        self.bind(
            f"def widen_list(request, queryset):\n"
            f"    return queryset.filter(pk='{self.hidden.pk}')",
            "core/groups:list",
        )
        self.assertEqual(self.group_names(), sorted([self.visible.name, self.hidden.name]))


class TestMembershipDecisions(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.group = Group.objects.create(name=generate_id())
        self.member = create_test_user()
        self.role.assign_perms("authentik_core.add_user_to_group", self.group)
        self.role.assign_perms("authentik_core.view_user", self.member)
        self.url = reverse("authentik_api:group-add-user", kwargs={"pk": self.group.pk})

    def test_denied_visible_user_is_403(self):
        self.bind(
            "def has_object_permission(request, obj):\n    return False",
            "core/groups:add_user",
        )
        self.assertEqual(self.client.post(self.url, {"pk": self.member.pk}).status_code, 403)

    def test_named_user_follows_users_list(self):
        hidden = create_test_user()
        self.assertEqual(self.client.post(self.url, {"pk": hidden.pk}).status_code, 404)
        self.bind(
            f"def widen_list(request, queryset):\n    return queryset.filter(pk={hidden.pk})",
            "core/users:list",
        )
        self.assertEqual(self.client.post(self.url, {"pk": hidden.pk}).status_code, 204)


class TestValidation(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(create_test_admin_user())
        self.url = reverse("authentik_api:permissioncheck-list")

    def create(self, expression: str, *endpoints: str):
        return self.client.post(
            self.url,
            {"name": generate_id(), "expression": expression, "endpoints": list(endpoints)},
            format="json",
        )

    def test_valid(self):
        self.assertEqual(self.create(DENY, "core/groups:list").status_code, 201)

    def test_syntax_error(self):
        self.assertEqual(self.create("def has_permission(", "core/groups:list").status_code, 400)

    def test_no_function(self):
        self.assertEqual(self.create("x = 1", "core/groups:list").status_code, 400)

    def test_unknown_endpoint(self):
        self.assertEqual(self.create(DENY, "core/nothing:list").status_code, 400)

    def test_rbac_endpoints_take_checks(self):
        self.assertEqual(self.create(DENY, "rbac/roles:add_user").status_code, 201)

    def test_endpoint_runs_no_defined_function(self):
        expression = "def has_object_permission(request, obj):\n    return True"
        self.assertEqual(self.create(expression, "core/groups:list").status_code, 400)

    def test_endpoint_bound_once(self):
        self.create(DENY, "core/groups:list")
        self.assertEqual(self.create(DENY, "core/groups:list").status_code, 400)

    def test_endpoints_required(self):
        url = reverse("authentik_api:permissioncheck-list")
        data = {"name": generate_id(), "expression": DENY}
        self.assertEqual(self.client.post(url, data, format="json").status_code, 400)
        self.assertEqual(self.create(DENY).status_code, 400)

    def test_endpoints(self):
        response = self.client.get(reverse("authentik_api:endpoints-list"))
        endpoints = {endpoint["id"]: endpoint["functions"] for endpoint in response.json()}
        self.assertEqual(
            endpoints["core/groups:list"],
            ["has_permission", "narrow_list", "widen_list", "hidden_fields"],
        )
        self.assertEqual(
            endpoints["core/groups:add_user"], ["has_permission", "has_object_permission"]
        )
        self.assertEqual(endpoints["admin/system:get"], ["has_permission"])
        self.assertIn("rbac/roles:add_user", endpoints)


class TestRealWorldExamples(PermissionCheckTestCase):
    def test_delegated_service_accounts(self):
        create_custom_permission("custom_add_service_account", User)
        self.bind(
            """
def has_permission(request):
    if request.user.has_perm("authentik_core.custom_add_service_account"):
        raise PermissionCheckSkipException
    return True
""",
            "core/users:service_account",
        )
        url = reverse("authentik_api:user-service-account")
        data = {"name": generate_id(), "create_group": False}
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.role.assign_perms("authentik_core.custom_add_service_account")
        self.assertEqual(self.client.post(url, data).status_code, 200)
        self.assertTrue(User.objects.filter(username=data["name"]).exists())

    def test_users_leave_groups(self):
        self.bind(
            """
def widen_list(request, queryset):
    return queryset.filter(pk=request.user.pk)

def has_object_permission(request, obj):
    if (
        ak_user_by(pk=request.data.get("pk")) == request.user
        and obj.attributes.get("self_service_leave", False)
    ):
        raise PermissionCheckSkipException
    return True
""",
            "core/users:list",
            "core/groups:remove_user",
        )
        other = create_test_user()
        group = Group.objects.create(name=generate_id(), attributes={"self_service_leave": True})
        group.users.add(self.user, other)
        url = reverse("authentik_api:group-remove-user", kwargs={"pk": group.pk})
        self.assertEqual(self.client.post(url, {"pk": other.pk}).status_code, 403)
        self.assertEqual(self.client.post(url, {"pk": self.user.pk}).status_code, 204)
        self.assertFalse(group.users.filter(pk=self.user.pk).exists())

    def test_managers_place_reports_in_groups(self):
        self.bind(
            """
def widen_list(request, queryset):
    return queryset.filter(attributes__manager=str(request.user.uuid))

def has_object_permission(request, obj):
    target = ak_user_by(pk=request.data.get("pk"))
    if (
        target is not None
        and target.attributes.get("manager") == str(request.user.uuid)
        and obj.attributes.get("managers_may_assign", False)
    ):
        raise PermissionCheckSkipException
    return True
""",
            "core/users:list",
            "core/groups:add_user",
        )
        report = create_test_user(attributes={"manager": str(self.user.uuid)})
        stranger = create_test_user()
        opted_in = Group.objects.create(
            name=generate_id(), attributes={"managers_may_assign": True}
        )
        other = Group.objects.create(name=generate_id())

        users = self.client.get(reverse("authentik_api:user-list")).json()["results"]
        self.assertEqual([user["pk"] for user in users], [report.pk])

        def add(group: Group, user: User) -> int:
            url = reverse("authentik_api:group-add-user", kwargs={"pk": group.pk})
            return self.client.post(url, {"pk": user.pk}).status_code

        self.assertEqual(add(opted_in, report), 204)
        self.assertEqual(add(other, report), 403)
        self.assertEqual(add(opted_in, stranger), 403)
