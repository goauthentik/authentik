"""Conditional policy evaluator tests"""

from datetime import timedelta
from pickle import dumps, loads  # nosec
from uuid import uuid4

from django.test import RequestFactory, TestCase
from django.utils.timezone import now

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.flows.planner import FlowPlan
from authentik.lib.generators import generate_id
from authentik.policies.conditional.evaluator import ConditionCompiler
from authentik.policies.conditional.models import ConditionalPolicy
from authentik.policies.conditional.schema import ConditionValidationError, MissingBehavior
from authentik.policies.exceptions import PolicyException
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.types import PolicyRequest


def tree(root: dict, *actions: dict) -> dict:
    """Actions of a policy which checks the condition `root`, followed by `actions`"""
    return {"version": 2, "actions": [{"type": "condition", "condition": root}, *actions]}


def cond(key: str, operator: str, value=None, **extra) -> dict:
    node = {"type": "compare", "variable": {"key": key}, "operator": operator}
    for field in ("param", "cast"):
        if field in extra:
            node["variable"][field] = extra.pop(field)
    if value is not None:
        node["value"] = {"type": "literal", "value": value}
    return node | extra


def group(op: str, *children: dict) -> dict:
    return {"type": "group", "op": op, "children": list(children)}


def set_context(key: str, value) -> dict:
    return {
        "type": "set",
        "target": {"key": "plan.context", "param": key},
        "value": {"type": "literal", "value": value},
    }


class TestConditionalEvaluator(TestCase):
    """Conditional policy evaluator tests"""

    def setUp(self):
        self.user = create_test_user(
            email="Jane.Doe@Example.com",
            attributes={"department": "engineering", "level": 3, "nested": {"flag": "true"}},
        )
        self.request = PolicyRequest(self.user)
        self.request.http_request = RequestFactory().get("/", REMOTE_ADDR="10.1.2.3")

    def run_actions(self, *actions: dict, request: PolicyRequest | None = None, **kwargs):
        policy = ConditionalPolicy(
            name=generate_id(), actions={"version": 2, "actions": list(actions)}, **kwargs
        )
        return policy.passes(request or self.request)

    def passes(self, root: dict, **kwargs) -> bool:
        return self.run_actions(*tree(root)["actions"], **kwargs).passing

    def flow_request(self) -> PolicyRequest:
        request = PolicyRequest(self.user)
        request.context = {"flow_plan": FlowPlan(flow_pk=generate_id())}
        return request

    def test_operators(self):
        """Operators, casts, groups and options"""
        member = Group.objects.create(name=generate_id())
        other = str(Group.objects.create(name=generate_id()).pk)
        self.user.groups.add(member)
        self.user.last_login = now() - timedelta(hours=2)
        true = cond("user.is_active", "is_true")
        false = cond("user.is_active", "is_false")
        insensitive = {"options": {"case_sensitive": False}}
        negate = {"options": {"negate": True}}
        cases = [
            (cond("user.email", "ends_with", "@Example.com"), True),
            (cond("user.email", "ends_with", "@example.com"), False),
            (cond("user.email", "ends_with", "@EXAMPLE.COM", **insensitive), True),
            (cond("user.email", "contains", "Doe"), True),
            (cond("user.email", "contains", "Doe", **negate), False),
            (cond("user.email", "contains", "nope", **negate), True),
            (cond("user.email", "starts_with", "Jane"), True),
            (cond("user.email", "eq", self.user.email), True),
            (cond("user.email", "in", ["a@b.c", self.user.email]), True),
            (cond("user.email", "not_in", ["a@b.c"]), True),
            (cond("user.email", "matches", r"^\w+\.\w+@"), True),
            (cond("user.email", "matches", r"^JANE\D"), False),
            (cond("user.email", "matches", r"^JANE\D", **insensitive), True),
            (cond("user.attributes", "eq", "engineering", param="department", cast="string"), True),
            (cond("user.attributes", "gte", 2, param="level", cast="number"), True),
            (cond("user.attributes", "is_true", param="nested.flag", cast="boolean"), True),
            # Value can't be cast to a number, so it's treated as missing
            (cond("user.attributes", "is_set", param="department", cast="number"), False),
            (cond("request.client_ip", "in_network", ["10.0.0.0/8"]), True),
            (cond("request.client_ip", "in_network", ["192.168.0.0/16"]), False),
            (cond("request.client_ip", "eq", "10.1.2.3"), True),
            (cond("user.last_login", "within_last", "days=1"), True),
            (cond("user.last_login", "within_last", "hours=1"), False),
            (cond("user.last_login", "older_than", "hours=1"), True),
            (cond("user.last_login", "gt", (now() - timedelta(days=1)).isoformat()), True),
            (cond("user.groups", "has_item", str(member.pk)), True),
            (cond("user.groups", "has_item", other), False),
            (cond("user.groups", "has_any", [str(member.pk), other]), True),
            (cond("user.groups", "has_all", [str(member.pk), other]), False),
            (cond("user.groups", "length_eq", 1), True),
            (cond("user.groups", "is_empty"), False),
            (group("all", true, true), True),
            (group("all", true, false), False),
            (group("any", false, true), True),
            (group("any", false, false), False),
            (group("none", false, false), True),
            (group("none", false, true), False),
            (group("all", true, group("any", false, true)), True),
        ]
        for node, expected in cases:
            with self.subTest(node=node):
                self.assertEqual(self.passes(node), expected)

    def test_variable_operand(self):
        """Compare two variables"""
        self.request.context["email"] = self.user.email.upper()
        node = cond("user.email", "eq", options={"case_sensitive": False})
        node["value"] = {
            "type": "variable",
            "variable": {"key": "plan.context", "param": "email", "cast": "string"},
        }
        self.assertTrue(self.passes(node))
        node["options"]["case_sensitive"] = True
        self.assertFalse(self.passes(node))

    def test_missing(self):
        """Missing values"""
        node = cond("plan.context", "eq", "foo", param="username", cast="string")
        # Fail policy
        self.assertFalse(self.passes(group("none", node)))
        # Evaluate condition as false
        self.assertTrue(self.passes(group("none", node), missing_behavior=MissingBehavior.FALSE))
        # Negation doesn't turn missing values into a pass
        self.assertFalse(self.passes(node | {"operator": "contains", "options": {"negate": True}}))
        # Presence checks are always evaluated, and groups short-circuit so the
        # missing value is never compared
        guarded = group("any", cond("plan.context", "is_not_set", param="username"), node)
        self.assertTrue(self.passes(guarded))
        self.request.context["username"] = "foo"
        self.assertTrue(self.passes(node))

    def test_policy_reference(self):
        """Evaluate referenced policies, and stop reference loops"""
        referenced = ExpressionPolicy.objects.create(
            name=generate_id(), expression="return request.user.is_active"
        )
        self.assertTrue(self.passes({"type": "policy", "policy": str(referenced.pk)}))
        with self.assertRaises(PolicyException):
            self.passes({"type": "policy", "policy": str(uuid4())})
        policy = ConditionalPolicy.objects.create(name=generate_id())
        policy.actions = tree({"type": "policy", "policy": str(policy.pk)})
        policy.save()
        with self.assertRaises(PolicyException):
            policy.passes(self.request)

    def test_actions(self):
        """Actions run in order, a failing condition stops with the failure message"""
        request = self.flow_request()
        result = self.run_actions(
            set_context("first", "a"),
            {"type": "condition", "condition": cond("user.is_active", "is_false")},
            set_context("second", "b"),
            request=request,
            failure_message="nope",
        )
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("nope",))
        self.assertEqual(request.context["flow_plan"].context, {"first": "a"})
        # Values of flows can only be set while a flow is executed
        with self.assertRaises(PolicyException):
            self.run_actions(set_context("foo", "bar"))

    def test_actions_if(self):
        """If actions run the matching branch"""
        for is_active in (True, False):
            request = self.flow_request()
            action = {
                "type": "if",
                "condition": cond("user.is_active", "is_true" if is_active else "is_false"),
                "then_actions": [
                    {
                        "type": "set",
                        "target": {"key": "plan.context", "param": "email"},
                        "value": {"type": "variable", "variable": {"key": "user.email"}},
                    }
                ],
                "else_actions": [{"type": "stop", "result": "fail", "message": "no"}],
            }
            result = self.run_actions(action, request=request)
            self.assertEqual(result.passing, is_active)
            self.assertEqual(result.messages, () if is_active else ("no",))
            self.assertEqual(
                request.context["flow_plan"].context,
                {"email": self.user.email} if is_active else {},
            )

    def test_actions_stop_and_disabled(self):
        """Stop ends with a result, disabled actions are skipped"""
        result = self.run_actions(
            {"type": "stop", "result": "fail", "enabled": False},
            {"type": "stop", "result": "pass", "message": "welcome"},
            {"type": "stop", "result": "fail"},
        )
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, ("welcome",))

    def test_invalid_stored(self):
        """Invalid stored actions raise a PolicyException"""
        with self.assertRaises(PolicyException):
            self.passes(cond("does.not.exist", "is_set"))

    def test_pickle(self):
        """Policies are pickled with policy results, for example to cache them, and are
        compiled again after being unpickled"""
        policy = ConditionalPolicy(name=generate_id(), actions=tree(cond("user.email", "is_set")))
        self.assertTrue(policy.passes(self.request).passing)
        self.assertTrue(loads(dumps(policy)).passes(self.request).passing)  # nosec


class TestConditionalCompiler(TestCase):
    """Validation of actions"""

    def assertInvalid(self, actions: list[dict], message: str):  # noqa: N802
        with self.assertRaises(ConditionValidationError) as ctx:
            ConditionCompiler.compile({"version": 2, "actions": actions})
        self.assertIn(message, str(ctx.exception))

    def test_invalid(self):
        literal = {"type": "literal", "value": "x"}
        deep = cond("user.is_active", "is_true")
        for _ in range(12):
            deep = group("none", deep)
        cases = [
            (cond("foo", "eq", "bar"), "Unknown variable 'foo'"),
            (cond("user.email", "gt", "bar"), "cannot be used with type string"),
            (cond("user.email", "eq"), "requires a value"),
            (cond("user.email", "is_set", "foo"), "does not take a value"),
            (cond("user.last_login", "eq", "foo"), "not a valid datetime"),
            (cond("user.last_login", "within_last", "foo"), "not a valid duration"),
            (cond("request.client_ip", "in_network", ["foo"]), "does not appear"),
            (cond("user.type", "eq", "foo"), "not a valid choice"),
            (cond("user.email", "matches", "("), "Invalid regular expression"),
            (cond("user.email", "matches", "a" * 300), "at most"),
            (cond("user.attributes", "is_set"), "requires a parameter"),
            (cond("user.attributes", "eq", "x", param="foo"), "must be cast"),
            (cond("user.email", "is_set", param="foo"), "does not take a parameter"),
            (cond("user.email", "is_set", cast="string"), "cannot be cast"),
            (group("all"), "at least one item"),
            (cond("user.email", "eq", "foo", options={"negate": True}), "cannot be negated"),
            (cond("user.last_login", "between", ["2020-01-01"]), "exactly two"),
            (deep, "levels deep"),
            (group("all", *[cond("user.is_active", "is_true")] * 250), "at most 200 items"),
        ]
        for node, message in cases:
            with self.subTest(message):
                self.assertInvalid(tree(node)["actions"], message)
        self.assertInvalid([], "at least one action")
        self.assertInvalid(
            [{"type": "set", "target": {"key": "foo"}, "value": literal}], "Unknown target"
        )
        self.assertInvalid(
            [{"type": "set", "target": {"key": "plan.context"}, "value": literal}],
            "requires a key",
        )
