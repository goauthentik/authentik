"""Test field rules of permission checks"""

from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.api.search.ql import HiddenFieldsSearchFilter
from authentik.core.models import Group, ObjectAttribute, User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.apps import EnableCustomPermissions
from authentik.rbac.field_rules import FieldRules
from authentik.rbac.models import CustomPermission, PermissionCheck, Role

SALARIES = """
def hidden_fields(request, obj):
    if request.user.has_perm("authentik_core.custom_read_salary", obj):
        return set()
    return {"attributes.salary", "email"}

def readonly_fields(request, obj):
    if request.user.has_perm("authentik_core.custom_change_salary", obj):
        return set()
    return {"attributes.level"}
"""
USER_ENDPOINTS = [
    "core/users:list",
    "core/users:retrieve",
    "core/users:update",
    "core/users:partial_update",
]


class TestFieldRules(APITestCase):
    """Example 5: salaries are for holders of custom_read_salary"""

    def setUp(self):
        EnableCustomPermissions.set(True)
        for codename in ["custom_read_salary", "custom_change_salary"]:
            CustomPermission.objects.create(
                codename=codename,
                name=codename,
                content_type=ContentType.objects.get_for_model(User),
            )
        self.check = PermissionCheck.objects.create(
            name=generate_id(), expression=SALARIES, endpoints=USER_ENDPOINTS
        )
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.role.assign_perms(["authentik_core.view_user", "authentik_core.change_user"])
        self.employee = create_test_user(attributes={"salary": 100, "level": 3, "team": "a"})
        self.client.force_login(self.user)

    def url(self, user: User | None = None) -> str:
        if user is None:
            return reverse("authentik_api:user-list")
        return reverse("authentik_api:user-detail", kwargs={"pk": user.pk})

    def patch(self, data: dict):
        return self.client.patch(self.url(self.employee), data, format="json")

    def test_hidden_key_vanishes(self):
        body = self.client.get(self.url(self.employee)).json()
        self.assertEqual(body["attributes"], {"level": 3, "team": "a"})

    def test_hidden_field_is_empty(self):
        self.assertEqual(self.client.get(self.url(self.employee)).json()["email"], "")

    def test_object_grant_shows(self):
        self.role.assign_perms("authentik_core.custom_read_salary", self.employee)
        results = self.client.get(self.url(), {"search": self.employee.username}).json()
        self.assertEqual(results["results"][0]["attributes"]["salary"], 100)
        self.assertEqual(self.client.get(self.url(self.user)).json()["email"], "")

    def test_rules_apply_on_bound_endpoints_only(self):
        self.check.endpoints = ["core/users:list"]
        self.check.save()
        results = self.client.get(self.url(), {"search": self.employee.username}).json()
        self.assertNotIn("salary", results["results"][0]["attributes"])
        self.assertEqual(
            self.client.get(self.url(self.employee)).json()["attributes"]["salary"], 100
        )

    def test_hidden_input_dropped_and_stored_value_kept(self):
        response = self.patch({"attributes": {"salary": 1, "level": 3, "team": "b"}})
        self.assertEqual(response.status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.attributes, {"salary": 100, "level": 3, "team": "b"})

    def test_hidden_field_input_dropped(self):
        email = self.employee.email
        self.assertEqual(self.patch({"email": "new@goauthentik.io"}).status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.email, email)

    def test_readonly_change_refused(self):
        response = self.patch({"attributes": {"level": 4}})
        self.assertEqual(response.status_code, 400)
        self.assertIn("attributes.level", response.json())

    def test_readonly_current_value_passes(self):
        self.assertEqual(self.patch({"attributes": {"level": 3, "team": "c"}}).status_code, 200)

    def test_readonly_change_allowed_for_holders(self):
        self.role.assign_perms("authentik_core.custom_change_salary", self.employee)
        self.assertEqual(self.patch({"attributes": {"level": 4}}).status_code, 200)

    def test_search_by_hidden_key_finds_nothing(self):
        response = self.client.get(self.url(), {"search": "attributes.salary = 100"})
        self.assertEqual(response.json()["results"], [])
        response = self.client.get(self.url(), {"search": 'attributes.team = "a"'})
        self.assertEqual(len(response.json()["results"]), 1)

    def test_query_by_hidden_field_refused(self):
        email = self.employee.email
        self.assertEqual(self.client.get(self.url(), {"ordering": "-email"}).status_code, 400)
        response = self.client.get(self.url(), {"search": f'email = "{email}"'})
        self.assertEqual(response.status_code, 400)
        response = self.client.get(self.url(), {"search": email})
        self.assertEqual(response.json()["results"], [])

    def test_hidden_attribute_not_validated(self):
        ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            key="salary",
            label="salary",
            type=ObjectAttribute.AttributeType.TEXT,
            is_required=True,
        )
        self.assertEqual(self.patch({"attributes": {"level": 3, "team": "b"}}).status_code, 200)

    def test_failure_fails_closed(self):
        self.check.expression = "def hidden_fields(request, obj):\n    raise ValueError"
        self.check.save()
        self.assertEqual(self.client.get(self.url(self.employee)).status_code, 500)

    def test_object_may_not_hide_more_than_endpoint(self):
        self.check.expression = (
            "def hidden_fields(request, obj):\n    return {'name'} if obj else set()"
        )
        self.check.save()
        self.assertEqual(self.client.get(self.url(self.employee)).status_code, 500)

    def test_full_update_keeps_hidden_required_field(self):
        self.check.endpoints = ["core/groups:update"]
        self.check.expression = "def hidden_fields(request, obj):\n    return {'name'}"
        self.check.save()
        group = Group.objects.create(name=generate_id())
        self.role.assign_perms(["authentik_core.view_group", "authentik_core.change_group"])
        response = self.client.put(
            reverse("authentik_api:group-detail", kwargs={"pk": group.pk}),
            {"name": "renamed", "attributes": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        group.refresh_from_db()
        self.assertNotEqual(group.name, "renamed")


MEMBER_SALARIES = """
def hidden_fields(request, obj):
    if obj is None:
        return {"users_obj.attributes.salary"}
    return {
        f"users_obj[{member.pk}].attributes.salary"
        for member in obj.users.all()
        if not request.user.has_perm("authentik_core.custom_read_salary", member)
    }

def readonly_fields(request, obj):
    return {"users_obj.attributes.salary"}
"""


class TestNestedFieldRules(APITestCase):
    """Salaries of group members, decided member by member"""

    def setUp(self):
        EnableCustomPermissions.set(True)
        CustomPermission.objects.create(
            codename="custom_read_salary",
            name="custom_read_salary",
            content_type=ContentType.objects.get_for_model(User),
        )
        self.check = PermissionCheck.objects.create(
            name=generate_id(),
            expression=MEMBER_SALARIES,
            endpoints=["core/groups:retrieve", "core/groups:partial_update"],
        )
        self.user = create_test_user()
        role = Role.objects.create(name=generate_id())
        self.user.roles.add(role)
        role.assign_perms(["authentik_core.view_group", "authentik_core.change_group"])
        self.readable = create_test_user(attributes={"salary": 1, "team": "a"})
        self.hidden = create_test_user(attributes={"salary": 2, "team": "a"})
        role.assign_perms("authentik_core.custom_read_salary", self.readable)
        self.group = Group.objects.create(name=generate_id())
        self.group.users.add(self.readable, self.hidden)
        self.client.force_login(self.user)
        self.url = reverse("authentik_api:group-detail", kwargs={"pk": self.group.pk})

    def salaries(self, body: dict) -> dict:
        return {member["pk"]: member["attributes"].get("salary") for member in body["users_obj"]}

    def test_members_decided_one_by_one(self):
        body = self.client.get(self.url).json()
        self.assertEqual(self.salaries(body), {self.readable.pk: 1, self.hidden.pk: None})

    def test_path_through_list(self):
        self.check.expression = (
            "def hidden_fields(request, obj):\n    return {'users_obj.attributes.salary'}"
        )
        self.check.save()
        body = self.client.get(self.url).json()
        self.assertEqual(self.salaries(body), {self.readable.pk: None, self.hidden.pk: None})

    def test_writes_echoing_nested_objects(self):
        body = self.client.get(self.url).json()
        response = self.client.patch(
            self.url, {"name": "renamed", "users_obj": body["users_obj"]}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.salaries(response.json()), {self.readable.pk: 1, self.hidden.pk: None}
        )
        self.hidden.refresh_from_db()
        self.assertEqual(self.hidden.attributes["salary"], 2)

    def test_unknown_field_reported(self):
        self.check.expression = (
            "def hidden_fields(request, obj):\n    return {'user_obj.attributes'}"
        )
        self.check.save()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.force_login(create_test_admin_user())
        check = reverse("authentik_api:permissioncheck-detail", kwargs={"pk": self.check.pk})
        unknown = self.client.get(check).json()["unknown_fields"]
        self.assertEqual(unknown, {"core/groups:retrieve": ["user_obj"]})
        self.check.expression += "\n"
        self.check.save()
        self.assertEqual(self.client.get(check).json()["unknown_fields"], {})

    def test_remove_path(self):
        data = {
            "user_obj": {"pk": 1, "attributes": {"salary": 1}},
            "users_obj": [{"pk": 1, "a": 1}, {"pk": 2, "a": 2}],
        }
        self.assertEqual(
            FieldRules.remove_path(data, ["user_obj", "attributes", "salary"])["user_obj"],
            {"pk": 1, "attributes": {}},
        )
        self.assertEqual(FieldRules.remove_path(data, ["user_obj[2]"]), data)
        self.assertEqual(
            FieldRules.remove_path(data, ["users_obj[2]", "a"])["users_obj"],
            [{"pk": 1, "a": 1}, {"pk": 2}],
        )
        self.assertEqual(
            FieldRules.remove_path(data, ["users_obj[2]"])["users_obj"], [{"pk": 1, "a": 1}]
        )
        self.assertEqual(
            FieldRules.remove_path(data, ["users_obj", "a"])["users_obj"], [{"pk": 1}, {"pk": 2}]
        )


class TestQueriedFields(SimpleTestCase):
    """The model fields search and ordering parameters start from"""

    def test_search_fields(self):
        search = HiddenFieldsSearchFilter()
        self.assertEqual(search.searched_field("name"), "name")
        self.assertEqual(search.searched_field("=email"), "email")
        self.assertEqual(search.searched_field("^groups__name"), "groups")

    def test_ordering_terms(self):
        self.assertEqual(FieldRules.ordered_field("email"), "email")
        self.assertEqual(FieldRules.ordered_field(" -email"), "email")
        self.assertEqual(FieldRules.ordered_field("-groups__name"), "groups")
