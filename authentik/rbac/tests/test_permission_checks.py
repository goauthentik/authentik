from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.models import CustomPermission, PermissionCheck, Role, SystemPermission

DENY = """
def has_permission(request):
    return False
"""


class PermissionCheckTestCase(APITestCase):
    """A logged-in user with a role, and custom permissions enabled"""

    def setUp(self):
        EnableCustomPermissions.set(True)
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.client.force_login(self.user)


class TestDecisions(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.role.assign_perms("authentik_core.view_group")
        self.url = reverse("authentik_api:group-list")
        self.system = reverse("authentik_api:admin_system")

    def test_false_forbids(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        PermissionCheck.objects.create(
            name=generate_id(), expression=DENY, endpoints=["core/groups:list"]
        )
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_true_keeps_decision(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def has_permission(request):\n    return True",
            endpoints=["admin/system:get"],
        )
        self.assertEqual(self.client.get(self.system).status_code, 403)

    def test_skip_exception_grants(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def has_permission(request):\n    raise PermissionCheckSkipException",
            endpoints=["admin/system:get"],
        )
        self.assertEqual(self.client.get(self.system).status_code, 200)

    def test_superuser_skips_checks(self):
        PermissionCheck.objects.create(
            name=generate_id(), expression=DENY, endpoints=["core/groups:list"]
        )
        self.client.force_login(create_test_admin_user())
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_outposts_run_checks(self):
        PermissionCheck.objects.create(
            name=generate_id(), expression=DENY, endpoints=["core/groups:list"]
        )
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_exception_forbids(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def has_permission(request):\n    raise ValueError",
            endpoints=["core/groups:list"],
        )
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_non_bool_forbids(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def has_permission(request):\n    return 1",
            endpoints=["core/groups:list"],
        )
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_narrow_list(self):
        kept = Group.objects.create(name=generate_id())
        Group.objects.create(name=generate_id())
        PermissionCheck.objects.create(
            name=generate_id(),
            expression=(
                "def narrow_list(request, queryset):\n"
                f"    return queryset.filter(name='{kept.name}')"
            ),
            endpoints=["core/groups:list"],
        )
        groups = self.client.get(self.url).json()["results"]
        self.assertEqual(sorted(group["name"] for group in groups), [kept.name])

    def test_narrow_list_wrong_type_forbids(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def narrow_list(request, queryset):\n    return ak_user_by()",
            endpoints=["core/groups:list"],
        )
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_retrieve_agrees_with_list(self):
        kept = Group.objects.create(name=generate_id())
        hidden = Group.objects.create(name="x")
        PermissionCheck.objects.create(
            name=generate_id(),
            expression=(
                f"def narrow_list(request, queryset):\n    return queryset.filter(pk='{kept.pk}')"
            ),
            endpoints=["core/groups:list"],
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
        self.url = reverse("authentik_api:group-list")

    def test_narrow_list_cannot_widen(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression=(
                "def narrow_list(request, queryset):\n    return queryset.model.objects.all()"
            ),
            endpoints=["core/groups:list"],
        )
        groups = self.client.get(self.url).json()["results"]
        self.assertEqual(sorted(group["name"] for group in groups), [self.visible.name])

    def test_widen_list(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression=f"def widen_list(request, queryset):\n"
            f"    return queryset.filter(pk='{self.hidden.pk}')",
            endpoints=["core/groups:list"],
        )
        groups = self.client.get(self.url).json()["results"]
        self.assertEqual(
            sorted(group["name"] for group in groups), sorted([self.visible.name, self.hidden.name])
        )


class TestMembershipDecisions(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.group = Group.objects.create(name=generate_id())
        self.member = create_test_user()
        self.role.assign_perms("authentik_core.add_user_to_group", self.group)
        self.role.assign_perms("authentik_core.view_user", self.member)
        self.url = reverse("authentik_api:group-add-user", kwargs={"pk": self.group.pk})

    def test_denied_visible_user_is_403(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def has_object_permission(request, obj):\n    return False",
            endpoints=["core/groups:add_user"],
        )
        self.assertEqual(self.client.post(self.url, {"pk": self.member.pk}).status_code, 403)

    def test_named_user_follows_users_list(self):
        hidden = create_test_user()
        self.assertEqual(self.client.post(self.url, {"pk": hidden.pk}).status_code, 404)
        PermissionCheck.objects.create(
            name=generate_id(),
            expression=(
                f"def widen_list(request, queryset):\n    return queryset.filter(pk={hidden.pk})"
            ),
            endpoints=["core/users:list"],
        )
        self.assertEqual(self.client.post(self.url, {"pk": hidden.pk}).status_code, 204)


class TestValidation(PermissionCheckTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(create_test_admin_user())
        self.url = reverse("authentik_api:permissioncheck-list")

    def test_valid(self):
        data = {"name": generate_id(), "expression": DENY, "endpoints": ["core/groups:list"]}
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 201)

    def test_syntax_error(self):
        data = {
            "name": generate_id(),
            "expression": "def has_permission(",
            "endpoints": ["core/groups:list"],
        }
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)

    def test_no_function(self):
        data = {"name": generate_id(), "expression": "x = 1", "endpoints": ["core/groups:list"]}
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)

    def test_unknown_endpoint(self):
        data = {"name": generate_id(), "expression": DENY, "endpoints": ["core/nothing:list"]}
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)

    def test_rbac_endpoints_take_checks(self):
        data = {"name": generate_id(), "expression": DENY, "endpoints": ["rbac/roles:add_user"]}
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 201)

    def test_endpoint_runs_no_defined_function(self):
        data = {
            "name": generate_id(),
            "expression": "def has_object_permission(request, obj):\n    return True",
            "endpoints": ["core/groups:list"],
        }
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)

    def test_endpoint_bound_once(self):
        data = {"name": generate_id(), "expression": DENY, "endpoints": ["core/groups:list"]}
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 201)
        data["name"] = generate_id()
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)

    def test_endpoints_required(self):
        data = {"name": generate_id(), "expression": DENY}
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)
        data["endpoints"] = []
        self.assertEqual(self.client.post(self.url, data, format="json").status_code, 400)

    def test_endpoints(self):
        response = self.client.get(reverse("authentik_api:endpoints-list"))
        endpoints = {endpoint["id"]: endpoint["functions"] for endpoint in response.json()}
        self.assertEqual(
            endpoints["core/groups:list"],
            ["has_permission", "narrow_list", "widen_list", "hidden_fields", "alter_response"],
        )
        self.assertEqual(
            endpoints["core/groups:add_user"],
            ["has_permission", "has_object_permission", "alter_response"],
        )
        self.assertEqual(endpoints["admin/system:get"], ["has_permission", "alter_response"])
        self.assertEqual(
            endpoints["sources/plex:redeem_token"], ["has_permission", "alter_response"]
        )
        self.assertIn("rbac/roles:add_user", endpoints)


class TestRealWorldExamples(PermissionCheckTestCase):
    def test_delegated_service_accounts(self):
        CustomPermission.objects.create(
            codename="custom_add_service_account",
            name="custom_add_service_account",
            content_type=ContentType.objects.get_for_model(User),
        )
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="""
def has_permission(request):
    if request.user.has_perm("authentik_core.custom_add_service_account"):
        raise PermissionCheckSkipException
    return True
""",
            endpoints=["core/users:service_account"],
        )
        url = reverse("authentik_api:user-service-account")
        data = {"name": generate_id(), "create_group": False}
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.role.assign_perms("authentik_core.custom_add_service_account")
        self.assertEqual(self.client.post(url, data).status_code, 200)
        self.assertTrue(User.objects.filter(username=data["name"]).exists())

    def test_users_leave_groups(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="""
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
            endpoints=["core/users:list", "core/groups:remove_user"],
        )
        other = create_test_user()
        group = Group.objects.create(name=generate_id(), attributes={"self_service_leave": True})
        group.users.add(self.user, other)
        url = reverse("authentik_api:group-remove-user", kwargs={"pk": group.pk})
        self.assertEqual(self.client.post(url, {"pk": other.pk}).status_code, 403)
        self.assertEqual(self.client.post(url, {"pk": self.user.pk}).status_code, 204)
        self.assertFalse(group.users.filter(pk=self.user.pk).exists())

    def test_managers_place_reports_in_groups(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="""
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
            endpoints=["core/users:list", "core/groups:add_user"],
        )
        report = create_test_user(attributes={"manager": str(self.user.uuid)})
        stranger = create_test_user()
        opted_in = Group.objects.create(
            name=generate_id(), attributes={"managers_may_assign": True}
        )
        other = Group.objects.create(name=generate_id())

        users = self.client.get(reverse("authentik_api:user-list")).json()["results"]
        self.assertEqual([user["pk"] for user in users], [report.pk])

        opted_in_url = reverse("authentik_api:group-add-user", kwargs={"pk": opted_in.pk})
        other_url = reverse("authentik_api:group-add-user", kwargs={"pk": other.pk})
        self.assertEqual(self.client.post(opted_in_url, {"pk": report.pk}).status_code, 204)
        self.assertEqual(self.client.post(other_url, {"pk": report.pk}).status_code, 403)
        self.assertEqual(self.client.post(opted_in_url, {"pk": stranger.pk}).status_code, 403)


class TestAlterResponse(PermissionCheckTestCase):
    """alter_response changes what an endpoint responds with"""

    def setUp(self):
        super().setUp()
        self.role.assign_perms("authentik_rbac.view_system_info")
        self.url = reverse("authentik_api:admin_system")

    def test_trimming_system_information(self):
        CustomPermission.objects.create(
            codename="custom_view_runtime_details",
            name="custom_view_runtime_details",
            content_type=ContentType.objects.get_for_model(SystemPermission),
        )
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="""
def alter_response(request, data):
    if request.user.has_perm("authentik_rbac.custom_view_runtime_details"):
        return data
    return {key: value for key, value in data.items() if key not in {"http_headers", "runtime"}}
""",
            endpoints=["admin/system:get"],
        )
        body = self.client.get(self.url).json()
        self.assertNotIn("runtime", body)
        self.assertIn("server_time", body)
        self.role.assign_perms("authentik_rbac.custom_view_runtime_details")
        self.assertIn("runtime", self.client.get(self.url).json())

    def test_exception_fails_closed(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def alter_response(request, data):\n    raise ValueError",
            endpoints=["admin/system:get"],
        )
        self.assertEqual(self.client.get(self.url).status_code, 500)

    def test_unserializable_fails_closed(self):
        PermissionCheck.objects.create(
            name=generate_id(),
            expression="def alter_response(request, data):\n    return object()",
            endpoints=["admin/system:get"],
        )
        self.assertEqual(self.client.get(self.url).status_code, 500)
