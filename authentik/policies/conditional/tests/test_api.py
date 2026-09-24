"""Conditional policy API tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import NotificationRule
from authentik.lib.generators import generate_id
from authentik.policies.conditional.models import ConditionalPolicy
from authentik.policies.conditional.tests.test_evaluator import cond, group, tree
from authentik.policies.models import PolicyBinding
from authentik.stages.prompt.models import PromptStage


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
                {"type": "not", "child": cond("request.geoip.country", "in", ["KP"])},
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
                    {"type": "not", "child": cond("user.email", "gt", "foo")},
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
                "actions.0.condition.children.1.child.operator",
                "actions.0.condition.children.2.children.0.value",
            },
        )
        # Structural errors, reported by pydantic
        response = self.create(
            tree(
                group(
                    "all",
                    {**cond("user.email", "eq", "foo"), "operator": "nope"},
                    {
                        "type": "not",
                        "child": {
                            **cond("user.email", "eq"),
                            "value": {"type": "variable", "variable": {}},
                        },
                    },
                )
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.json()["actions"]["nodes"]),
            {
                "actions.0.condition.children.0.operator",
                "actions.0.condition.children.1.child.value.variable.key",
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
        targets = {target["model"]: target for target in body["targets"]}
        self.assertIn("event", targets["authentik_events.notificationrule"]["facts"])
        self.assertNotIn("http_request", targets["authentik_events.notificationrule"]["facts"])
        self.assertIn("flow_plan", targets["authentik_flows.flow"]["facts"])
        self.assertIn("authentik_stages_prompt.promptstage", targets)
        self.assertIn("eq", {op["name"] for op in body["operators"]})


class TestConditionalPolicyTargets(APITestCase):
    """Check that policies are only bound where their variables are available"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.event_policy = ConditionalPolicy.objects.create(
            name=generate_id(), actions=tree(cond("event.action", "eq", "login"))
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
        rule = NotificationRule.objects.create(name=generate_id())
        response = self.bind(self.event_policy, flow)
        self.assertEqual(response.status_code, 400)
        self.assertIn("event.action", str(response.json()))
        self.assertEqual(self.bind(self.event_policy, rule).status_code, 201)
        self.assertEqual(self.bind(self.user_policy, flow).status_code, 201)

    def test_binding_nested(self):
        """Variables of referenced policies are checked"""
        outer = ConditionalPolicy.objects.create(
            name=generate_id(),
            actions=tree({"type": "policy", "policy": str(self.event_policy.pk)}),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.assertEqual(self.bind(outer, app).status_code, 400)

    def test_prompt_stage(self):
        """Validation policies of a prompt stage"""
        prompt_policy = ConditionalPolicy.objects.create(
            name=generate_id(),
            actions=tree(cond("prompt_data", "eq", "foo", param="username", cast="string")),
        )
        stage = PromptStage.objects.create(name=generate_id())
        url = reverse("authentik_api:promptstage-detail", kwargs={"pk": stage.pk})
        response = self.client.patch(
            url, data={"validation_policies": [str(self.event_policy.pk)]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(
            url, data={"validation_policies": [str(prompt_policy.pk)]}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PolicyBinding.objects.filter(policy=prompt_policy).count(), 0)


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
