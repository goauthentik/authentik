"""Conditional policy API tests"""

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group, ObjectAttribute, User
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.policies.conditional.models import ConditionalPolicy
from authentik.policies.conditional.tests.test_evaluator import cond, group, tree


class TestConditionalPolicyAPI(APITestCase):
    """Conditional policy API tests"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def create(self, conditions: dict):
        return self.client.post(
            reverse("authentik_api:conditionalpolicy-list"),
            data={"name": generate_id(), "actions": conditions},
            format="json",
        )

    def test_create(self):
        """Create a policy"""
        conditions = tree(
            group(
                "all",
                cond("user.email", "ends_with", "@goauthentik.io"),
                group("none", cond("request.client_ip", "in_network", ["192.0.2.0/24"])),
            )
        )
        response = self.create(conditions)
        self.assertEqual(response.status_code, 201, response.content)
        policy = ConditionalPolicy.objects.get(pk=response.json()["pk"])
        self.assertEqual(
            policy.actions["actions"][0]["condition"]["children"][0]["variable"]["key"],
            "user.email",
        )
        self.assertEqual(response.json()["component"], "ak-policy-conditional-form")

    def test_create_invalid_shape(self):
        """Invalid structure"""
        response = self.create({"version": 2, "actions": [{"type": "foo"}]})
        self.assertEqual(response.status_code, 400)
        response = self.create(
            tree(group("all", {"type": "compare", "operator": "eq", "variable": {}}))
        )
        self.assertEqual(response.status_code, 400)

    def test_error_paths(self):
        """Errors are reported for the node (and field) they belong to"""
        response = self.create(
            tree(
                group(
                    "all",
                    cond("user.email", "eq", "foo"),
                    group("none", cond("user.email", "gt", "foo")),
                    group("any", cond("user.last_login", "within_last", "foo")),
                )
            )
        )
        self.assertEqual(response.status_code, 400)
        errors = response.json()["actions"]
        self.assertEqual(errors["detail"], "The actions contain 2 errors.")
        self.assertEqual(
            set(errors["nodes"]),
            {
                "actions.0.condition.children.1.children.0.operator",
                "actions.0.condition.children.2.children.0.value",
            },
        )
        # Structural errors, reported by pydantic
        response = self.create(
            tree(
                group(
                    "all",
                    {**cond("user.email", "eq", "foo"), "operator": "nope"},
                    group(
                        "none",
                        {
                            **cond("user.email", "eq"),
                            "value": {"type": "variable", "variable": {}},
                        },
                    ),
                )
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.json()["actions"]["nodes"]),
            {
                "actions.0.condition.children.0.operator",
                "actions.0.condition.children.1.children.0.value.variable.key",
            },
        )

    def test_create_invalid_semantics(self):
        """Structure is valid, but doesn't match registry"""
        response = self.create(tree(cond("user.email", "gt", "foo")))
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot be used with type string", str(response.json()))

    def test_references(self):
        """Referenced policies must exist, and must not create loops"""
        response = self.create(tree({"type": "policy", "policy": generate_id()}))
        self.assertEqual(response.status_code, 400)

        first = ConditionalPolicy.objects.create(
            name=generate_id(), actions=tree(cond("user.is_active", "is_true"))
        )
        second = ConditionalPolicy.objects.create(
            name=generate_id(), actions=tree({"type": "policy", "policy": str(first.pk)})
        )
        response = self.client.patch(
            reverse("authentik_api:conditionalpolicy-detail", kwargs={"pk": first.pk}),
            data={"actions": tree({"type": "policy", "policy": str(second.pk)})},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "would create a loop", response.json()["actions"]["nodes"]["actions.0.condition"][0]
        )

    def test_labels(self):
        """Names of referenced objects are returned"""
        members = Group.objects.create(name=generate_id())
        other = ConditionalPolicy.objects.create(
            name=generate_id(), actions=tree(cond("user.is_active", "is_true"))
        )
        response = self.create(
            tree(
                group(
                    "all",
                    cond("user.groups", "has_item", str(members.pk)),
                    {"type": "policy", "policy": str(other.pk)},
                )
            )
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(
            response.json()["labels"],
            {
                f"authentik_core.group:{members.pk}": members.name,
                f"authentik_policies.policy:{other.pk}": other.name,
            },
        )

    def test_object_attributes(self):
        """Object attributes of users are offered as user attributes"""
        ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            key="org.department",
            label="Department",
            group="Organization",
            type=ObjectAttribute.AttributeType.TEXT,
        )
        response = self.client.get(reverse("authentik_api:conditionalpolicy-catalog"))
        variables = {variable["key"]: variable for variable in response.json()["variables"]}
        params = {param["key"]: param for param in variables["user.attributes"]["params"]}
        self.assertEqual(params["org.department"]["label"], "Attribute › Organization › Department")
        self.assertEqual(params["org.department"]["type"]["kind"], "string")
        # The attribute has a type, so it doesn't need to be cast
        response = self.create(
            tree(cond("user.attributes", "eq", "Engineering", param="org.department"))
        )
        self.assertEqual(response.status_code, 201, response.content)

    def test_catalog(self):
        """Catalog of variables"""
        response = self.client.get(reverse("authentik_api:conditionalpolicy-catalog"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        variables = {variable["key"]: variable for variable in body["variables"]}
        self.assertEqual(variables["user.email"]["type"]["kind"], "string")
        self.assertEqual(variables["user.email"]["app"], "authentik_core")
        self.assertEqual(variables["user.groups"]["type"]["item"]["model"], "authentik_core.group")
        self.assertEqual(variables["user.attributes"]["param"], "path")
        scenarios = {scenario["key"]: scenario for scenario in body["scenarios"]}
        self.assertEqual(
            scenarios["application_authorization"]["label"], "Application authorization"
        )
        self.assertIn("application", scenarios["application_authorization"]["facts"])
        self.assertIn("flow_plan", scenarios["flow_execution"]["facts"])
        self.assertNotIn("application", scenarios["flow_execution"]["facts"])
        self.assertIn("eq", {op["name"] for op in body["operators"]})


class TestConditionalPolicyTargets(APITestCase):
    """Check that policies are only bound where their variables are available"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.app_policy = ConditionalPolicy.objects.create(
            name=generate_id(), actions=tree(cond("application.slug", "eq", "foo"))
        )
        self.user_policy = ConditionalPolicy.objects.create(
            name=generate_id(), actions=tree(cond("user.is_active", "is_true"))
        )

    def bind(self, policy: ConditionalPolicy, target):
        return self.client.post(
            reverse("authentik_api:policybinding-list"),
            data={"policy": str(policy.pk), "target": str(target.pk), "order": 0},
            format="json",
        )

    def test_binding(self):
        flow = create_test_flow()
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        response = self.bind(self.app_policy, flow)
        self.assertEqual(response.status_code, 400)
        self.assertIn("application.slug", str(response.json()))
        self.assertEqual(self.bind(self.app_policy, app).status_code, 201)
        self.assertEqual(self.bind(self.user_policy, flow).status_code, 201)

    def test_binding_nested(self):
        """Variables of referenced policies are checked"""
        outer = ConditionalPolicy.objects.create(
            name=generate_id(),
            actions=tree({"type": "policy", "policy": str(self.app_policy.pk)}),
        )
        self.assertEqual(self.bind(outer, create_test_flow()).status_code, 400)


class TestConditionalPolicyTest(APITestCase):
    """Policy test endpoint returns a trace of the evaluation"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_trace(self):
        policy = ConditionalPolicy.objects.create(
            name=generate_id(),
            actions=tree(
                group(
                    "all",
                    cond("user.is_active", "is_true"),
                    cond("user.username", "eq", "not-the-username"),
                )
            ),
        )
        response = self.client.post(
            reverse("authentik_api:policy-test", kwargs={"pk": policy.pk}),
            data={"user": self.user.pk},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["passing"])
        nodes = [log["attributes"].get("node") for log in body["log_messages"]]
        self.assertIn("actions.0.condition.children.1", nodes)
