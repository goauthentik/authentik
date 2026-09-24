"""Conditional policy evaluator tests"""

from datetime import timedelta
from unittest.mock import MagicMock, PropertyMock, patch
from uuid import uuid4

from django.test import RequestFactory, TestCase
from django.utils.timezone import now

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.endpoints.models import Device
from authentik.events.models import Event, EventAction
from authentik.flows.planner import FlowPlan
from authentik.lib.generators import generate_id
from authentik.policies.conditional.evaluator import ConditionValidationError, compile_actions
from authentik.policies.conditional.models import ConditionalPolicy, MissingBehavior
from authentik.policies.exceptions import PolicyException
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.types import PolicyRequest
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


def tree(root: dict, *actions: dict) -> dict:
    """Actions of a policy which checks the condition `root`, followed by `actions`"""
    return {"version": 2, "actions": [{"type": "condition", "condition": root}, *actions]}


def cond(key: str, operator: str, value=None, **extra) -> dict:
    node = {"type": "compare", "variable": {"key": key}, "operator": operator}
    if "param" in extra:
        node["variable"]["param"] = extra.pop("param")
    if "cast" in extra:
        node["variable"]["cast"] = extra.pop("cast")
    if value is not None:
        node["value"] = {"type": "literal", "value": value}
    node.update(extra)
    return node


def group(op: str, *children: dict) -> dict:
    return {"type": "group", "op": op, "children": list(children)}


class TestConditionalEvaluator(TestCase):
    """Conditional policy evaluator tests"""

    def setUp(self):
        self.user = create_test_user(
            email="Jane.Doe@Example.com",
            attributes={"department": "engineering", "level": 3, "nested": {"flag": "true"}},
        )
        self.request = PolicyRequest(self.user)
        self.request.http_request = RequestFactory().get("/", REMOTE_ADDR="10.1.2.3")

    def passes(self, root: dict, **kwargs) -> bool:
        policy = ConditionalPolicy(name=generate_id(), actions=tree(root), **kwargs)
        return policy.passes(self.request).passing

    def test_string_operators(self):
        """String operators, including case sensitivity"""
        self.assertTrue(self.passes(cond("user.email", "ends_with", "@Example.com")))
        self.assertFalse(self.passes(cond("user.email", "ends_with", "@example.com")))
        self.assertTrue(
            self.passes(
                cond("user.email", "ends_with", "@EXAMPLE.COM", options={"case_sensitive": False})
            )
        )
        self.assertTrue(self.passes(cond("user.email", "contains", "Doe")))
        self.assertTrue(self.passes(cond("user.email", "starts_with", "Jane")))
        self.assertTrue(self.passes(cond("user.email", "eq", self.user.email)))
        self.assertTrue(self.passes(cond("user.email", "in", ["a@b.c", self.user.email])))
        self.assertTrue(self.passes(cond("user.email", "not_in", ["a@b.c"])))
        self.assertTrue(self.passes(cond("user.email", "matches", r"^\w+\.\w+@")))
        self.assertTrue(
            self.passes(
                cond("user.email", "matches", r"^JANE\D", options={"case_sensitive": False})
            )
        )
        self.assertFalse(self.passes(cond("user.email", "matches", r"^JANE\D")))

    def test_attributes_cast(self):
        """Values of unknown type are cast"""
        self.assertTrue(
            self.passes(
                cond("user.attributes", "eq", "engineering", param="department", cast="string")
            )
        )
        self.assertTrue(
            self.passes(cond("user.attributes", "gte", 2, param="level", cast="number"))
        )
        self.assertTrue(
            self.passes(cond("user.attributes", "is_true", param="nested.flag", cast="boolean"))
        )
        # Value can't be cast to a number, so it's treated as missing
        self.assertFalse(
            self.passes(cond("user.attributes", "is_set", param="department", cast="number"))
        )

    def test_ip(self):
        """IP operators"""
        self.assertTrue(self.passes(cond("request.client_ip", "in_network", ["10.0.0.0/8"])))
        self.assertFalse(self.passes(cond("request.client_ip", "in_network", ["192.168.0.0/16"])))
        self.assertTrue(self.passes(cond("request.client_ip", "eq", "10.1.2.3")))

    def test_datetime(self):
        """Datetime operators"""
        self.user.last_login = now() - timedelta(hours=2)
        self.assertTrue(self.passes(cond("user.last_login", "within_last", "days=1")))
        self.assertFalse(self.passes(cond("user.last_login", "within_last", "hours=1")))
        self.assertTrue(self.passes(cond("user.last_login", "older_than", "hours=1")))
        self.assertTrue(
            self.passes(cond("user.last_login", "gt", (now() - timedelta(days=1)).isoformat()))
        )

    def test_lists(self):
        """List operators"""
        member = Group.objects.create(name=generate_id())
        other = Group.objects.create(name=generate_id())
        self.user.groups.add(member)
        self.assertTrue(self.passes(cond("user.groups", "has_item", str(member.pk))))
        self.assertFalse(self.passes(cond("user.groups", "has_item", str(other.pk))))
        self.assertTrue(
            self.passes(cond("user.groups", "has_any", [str(member.pk), str(other.pk)]))
        )
        self.assertFalse(
            self.passes(cond("user.groups", "has_all", [str(member.pk), str(other.pk)]))
        )
        self.assertTrue(self.passes(cond("user.groups", "length_eq", 1)))
        self.assertFalse(self.passes(cond("user.groups", "is_empty")))

    def test_logic(self):
        """Groups and negation"""
        true = cond("user.is_active", "is_true")
        false = cond("user.is_active", "is_false")
        self.assertTrue(self.passes(group("all", true, true)))
        self.assertFalse(self.passes(group("all", true, false)))
        self.assertTrue(self.passes(group("any", false, true)))
        self.assertFalse(self.passes(group("any", false, false)))
        self.assertTrue(self.passes({"type": "not", "child": false}))
        self.assertTrue(self.passes(group("all", true, group("any", false, true))))

    def test_variable_operand(self):
        """Compare two variables"""
        self.request.context[PLAN_CONTEXT_PROMPT] = {"email": self.user.email.upper()}
        node = cond("user.email", "eq", options={"case_sensitive": False})
        node["value"] = {
            "type": "variable",
            "variable": {"key": "prompt_data", "param": "email", "cast": "string"},
        }
        self.assertTrue(self.passes(node))
        node["options"]["case_sensitive"] = True
        self.assertFalse(self.passes(node))

    def test_missing(self):
        """Missing values"""
        node = cond("prompt_data", "eq", "foo", param="username", cast="string")
        # Fail policy
        self.assertFalse(self.passes({"type": "not", "child": node}))
        # Evaluate condition as false
        self.assertTrue(
            self.passes({"type": "not", "child": node}, missing_behavior=MissingBehavior.FALSE)
        )
        # Presence checks are always evaluated, and groups short-circuit so the
        # missing value is never compared
        guarded = group(
            "any", cond("prompt_data", "is_not_set", param="username", cast="string"), node
        )
        self.assertTrue(self.passes(guarded))
        self.request.context[PLAN_CONTEXT_PROMPT] = {"username": "foo"}
        self.assertTrue(self.passes(node))

    def test_failure_message(self):
        """Failure message is returned when the policy doesn't pass"""
        policy = ConditionalPolicy(
            name=generate_id(),
            actions=tree(cond("user.is_active", "is_false")),
            failure_message="nope",
        )
        result = policy.passes(self.request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("nope",))

    def test_event(self):
        """Event variables"""
        event = Event.new(EventAction.LOGIN_FAILED)
        event.client_ip = "1.2.3.4"
        event.save()
        request = PolicyRequest(self.user)
        request.obj = event
        request.context["event"] = event
        policy = ConditionalPolicy(
            name=generate_id(),
            actions=tree(
                group(
                    "all",
                    cond("event.action", "eq", EventAction.LOGIN_FAILED),
                    cond("event.client_ip", "in_network", ["1.2.3.0/24"]),
                )
            ),
        )
        self.assertTrue(policy.passes(request).passing)

    def test_policy_reference(self):
        """Evaluate referenced policies"""
        referenced = ExpressionPolicy.objects.create(
            name=generate_id(), expression="return request.user.is_active"
        )
        self.assertTrue(self.passes({"type": "policy", "policy": str(referenced.pk)}))
        with self.assertRaises(PolicyException):
            self.passes({"type": "policy", "policy": str(uuid4())})
        with self.assertRaises(PolicyException):
            self.passes({"type": "policy", "policy": generate_id()})

    def test_policy_reference_loop(self):
        """Reference loops are stopped"""
        policy = ConditionalPolicy.objects.create(name=generate_id())
        policy.actions = tree({"type": "policy", "policy": str(policy.pk)})
        policy.save()
        with self.assertRaises(PolicyException):
            policy.passes(self.request)

    def test_negate(self):
        """Operators can be negated with an option"""
        self.assertFalse(
            self.passes(cond("user.email", "contains", "Doe", options={"negate": True}))
        )
        self.assertTrue(
            self.passes(cond("user.email", "contains", "nope", options={"negate": True}))
        )
        # Negation doesn't turn missing values into a pass
        self.assertFalse(
            self.passes(
                cond(
                    "prompt_data",
                    "contains",
                    "foo",
                    param="username",
                    cast="string",
                    options={"negate": True},
                )
            )
        )

    def test_group_none(self):
        """None groups pass when no child passes"""
        true = cond("user.is_active", "is_true")
        false = cond("user.is_active", "is_false")
        self.assertTrue(self.passes(group("none", false, false)))
        self.assertFalse(self.passes(group("none", false, true)))

    def test_known_params(self):
        """Well-defined parameters are typed without a cast, and `*` collects from lists"""
        self.request.context["device"] = Device.objects.create(
            name=generate_id(), identifier=generate_id()
        )
        facts = {
            "hardware": {"manufacturer": "Apple", "cpu_count": 8},
            "software": [{"name": "Firefox"}, {"name": "Slack"}],
        }
        with patch(
            "authentik.endpoints.models.Device.cached_facts",
            PropertyMock(return_value=MagicMock(data=facts)),
        ):
            self.assertTrue(
                self.passes(cond("device.facts", "eq", "Apple", param="hardware.manufacturer"))
            )
            self.assertTrue(self.passes(cond("device.facts", "gte", 4, param="hardware.cpu_count")))
            self.assertTrue(
                self.passes(cond("device.facts", "has_item", "Slack", param="software.*.name"))
            )

    def run_actions(self, *actions: dict, request: PolicyRequest | None = None, **kwargs):
        policy = ConditionalPolicy(
            name=generate_id(), actions={"version": 2, "actions": list(actions)}, **kwargs
        )
        return policy.passes(request or self.request)

    def flow_request(self, **context) -> PolicyRequest:
        plan = FlowPlan(flow_pk=generate_id())
        plan.context = dict(context)
        request = PolicyRequest(self.user)
        request.context = {**context, "flow_plan": plan}
        return request

    def test_actions_sequence(self):
        """Actions run in order, a failing condition stops"""
        request = self.flow_request()
        set_first = {
            "type": "set",
            "target": {"key": "plan.context", "param": "first"},
            "value": {"type": "literal", "value": "a"},
        }
        set_second = {
            "type": "set",
            "target": {"key": "plan.context", "param": "second"},
            "value": {"type": "literal", "value": "b"},
        }
        result = self.run_actions(
            set_first,
            {"type": "condition", "condition": cond("user.is_active", "is_false")},
            set_second,
            request=request,
            failure_message="nope",
        )
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("nope",))
        plan = request.context["flow_plan"]
        self.assertEqual(plan.context["first"], "a")
        self.assertNotIn("second", plan.context)

    def test_actions_if(self):
        """If actions run the matching branch"""

        def branch(condition: dict):
            request = self.flow_request()
            result = self.run_actions(
                {
                    "type": "if",
                    "condition": condition,
                    "then_actions": [
                        {
                            "type": "set",
                            "target": {"key": "plan.email_override"},
                            "value": {
                                "type": "variable",
                                "variable": {"key": "user.email"},
                            },
                        }
                    ],
                    "else_actions": [{"type": "stop", "result": "fail", "message": "no"}],
                },
                request=request,
            )
            return result, request.context["flow_plan"].context

        result, context = branch(cond("user.is_active", "is_true"))
        self.assertTrue(result.passing)
        self.assertEqual(context["email"], self.user.email)
        result, context = branch(cond("user.is_active", "is_false"))
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("no",))
        self.assertNotIn("email", context)

    def test_actions_prompt_data(self):
        """Prompt fields can be set, and later actions see the new value"""
        prompt = {"email": "foo@goauthentik.io"}
        request = self.flow_request(prompt_data=prompt)
        result = self.run_actions(
            {
                "type": "set",
                "target": {"key": "prompt_data", "param": "username"},
                "value": {
                    "type": "variable",
                    "variable": {"key": "prompt_data", "param": "email", "cast": "string"},
                },
            },
            {
                "type": "condition",
                "condition": cond(
                    "prompt_data", "eq", "foo@goauthentik.io", param="username", cast="string"
                ),
            },
            request=request,
        )
        self.assertTrue(result.passing)
        self.assertEqual(prompt["username"], "foo@goauthentik.io")

    def test_actions_stop_and_disabled(self):
        """Stop ends with a result, disabled actions are skipped"""
        result = self.run_actions(
            {"type": "stop", "result": "fail", "enabled": False},
            {"type": "stop", "result": "pass", "message": "welcome"},
            {"type": "stop", "result": "fail"},
        )
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, ("welcome",))

    def test_actions_set_outside_flow(self):
        """Values of flows can only be set while a flow is executed"""
        with self.assertRaises(PolicyException):
            self.run_actions(
                {
                    "type": "set",
                    "target": {"key": "plan.context", "param": "foo"},
                    "value": {"type": "literal", "value": "bar"},
                }
            )

    def test_invalid_stored(self):
        """Invalid stored conditions raise a PolicyException"""
        with self.assertRaises(PolicyException):
            self.passes(cond("does.not.exist", "is_set"))


class TestConditionalCompiler(TestCase):
    """Validation of condition trees"""

    def assertInvalid(self, root: dict, message: str):
        with self.assertRaises(ConditionValidationError) as ctx:
            compile_actions(tree(root))
        self.assertIn(message, str(ctx.exception))

    def test_valid(self):
        compile_actions(tree(cond("user.email", "eq", "foo")))

    def test_invalid(self):
        self.assertInvalid(cond("foo", "eq", "bar"), "Unknown variable 'foo'")
        self.assertInvalid(cond("user.email", "gt", "bar"), "cannot be used with type string")
        self.assertInvalid(cond("user.email", "eq"), "requires a value")
        self.assertInvalid(cond("user.email", "is_set", "foo"), "does not take a value")
        self.assertInvalid(cond("user.last_login", "eq", "foo"), "not a valid datetime")
        self.assertInvalid(cond("user.last_login", "within_last", "foo"), "not a valid duration")
        self.assertInvalid(cond("request.client_ip", "in_network", ["foo"]), "does not appear")
        self.assertInvalid(cond("user.type", "eq", "foo"), "not a valid choice")
        self.assertInvalid(cond("user.email", "matches", "("), "Invalid regular expression")
        self.assertInvalid(cond("user.email", "matches", "a" * 300), "at most")
        self.assertInvalid(cond("user.attributes", "is_set"), "requires a parameter")
        self.assertInvalid(cond("user.attributes", "eq", "x", param="foo"), "must be cast")
        self.assertInvalid(cond("user.email", "is_set", param="foo"), "does not take a parameter")
        self.assertInvalid(cond("user.email", "is_set", cast="string"), "cannot be cast")
        self.assertInvalid(group("all"), "at least one item")
        self.assertInvalid(
            cond("user.email", "eq", "foo", options={"negate": True}), "cannot be negated"
        )
        self.assertInvalid(cond("user.last_login", "between", ["2020-01-01"]), "exactly two")

    def test_invalid_actions(self):
        def assert_invalid(actions: list[dict], message: str):
            with self.assertRaises(ConditionValidationError) as ctx:
                compile_actions({"version": 2, "actions": actions})
            self.assertIn(message, str(ctx.exception))

        literal = {"type": "literal", "value": "x"}
        assert_invalid([], "at least one action")
        assert_invalid(
            [{"type": "set", "target": {"key": "foo"}, "value": literal}], "Unknown target"
        )
        assert_invalid(
            [{"type": "set", "target": {"key": "plan.context"}, "value": literal}],
            "requires a key",
        )
        assert_invalid(
            [
                {
                    "type": "set",
                    "target": {"key": "plan.email_override"},
                    "value": {"type": "literal", "value": {"a": 1}},
                }
            ],
            "is not a string",
        )
        assert_invalid(
            [
                {
                    "type": "if",
                    "condition": cond("user.email", "gt", "x"),
                    "then_actions": [{"type": "stop", "result": "pass"}],
                }
            ],
            "actions.0.condition.operator",
        )

    def test_limits(self):
        node = cond("user.is_active", "is_true")
        for _ in range(12):
            node = {"type": "not", "child": node}
        self.assertInvalid(node, "levels deep")
        self.assertInvalid(
            group("all", *[cond("user.is_active", "is_true")] * 250), "at most 200 items"
        )
