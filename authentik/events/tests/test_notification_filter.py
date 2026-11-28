"""Notification dispatch filter tests"""

from time import monotonic
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Event, EventAction, NotificationRule
from authentik.events.notification_filter import CACHE_TIMEOUT, clear_cache
from authentik.lib.generators import generate_id
from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding, PolicyBindingModel

# The receiver imports the task lazily, so patch it on the task module
DISPATCH = "authentik.events.tasks.event_trigger_dispatch.send"
BINDING_TABLE = "authentik_policies_policybinding"


class TestNotificationDispatchFilter(TestCase):
    """Test that notification dispatch is skipped for events no rule can match"""

    def setUp(self) -> None:
        NotificationRule.objects.all().delete()

    def rule(self, **binding) -> NotificationRule:
        """Create a notification rule, with a binding if any binding arguments are given"""
        rule = NotificationRule.objects.create(name=generate_id())
        if binding:
            PolicyBinding.objects.create(target=rule, order=0, **binding)
        return rule

    def matcher(self, action: str | None = None, **kwargs) -> EventMatcherPolicy:
        return EventMatcherPolicy.objects.create(name=generate_id(), action=action, **kwargs)

    def dispatched(self, action: str) -> bool:
        """Save an event with `action` and return whether the dispatch task was sent"""
        with patch(DISPATCH) as send:
            event = Event.new(action)
            event.save()
        if not send.called:
            return False
        send.assert_called_once_with(event.event_uuid)
        return True

    def binding_queries(self, action: str) -> int:
        """Save an event with `action` and return how many queries looked at bindings"""
        with patch(DISPATCH), CaptureQueriesContext(connection) as ctx:
            Event.new(action).save()
        return len([query for query in ctx.captured_queries if BINDING_TABLE in query["sql"]])

    def test_no_rules(self):
        """Without any rules, nothing is dispatched"""
        self.assertFalse(self.dispatched(EventAction.LOGIN))

    def test_rule_without_enabled_bindings(self):
        """Rules without (enabled) bindings never match"""
        self.rule()
        self.rule(policy=self.matcher(EventAction.LOGIN), enabled=False)
        self.rule(policy=self.matcher(), enabled=False)
        self.rule(group=Group.objects.create(name=generate_id()), enabled=False)
        self.assertFalse(self.dispatched(EventAction.LOGIN))

    def test_matcher_action(self):
        """Only the actions of matchers are dispatched"""
        self.rule(policy=self.matcher(EventAction.CONFIGURATION_ERROR))
        self.rule(policy=self.matcher(EventAction.UPDATE_AVAILABLE))
        self.assertTrue(self.dispatched(EventAction.CONFIGURATION_ERROR))
        self.assertTrue(self.dispatched(EventAction.UPDATE_AVAILABLE))
        self.assertFalse(self.dispatched(EventAction.LOGIN))

    def test_custom_action(self):
        """Custom actions are matched by their prefixed name"""
        self.rule(policy=self.matcher(EventAction.CUSTOM_PREFIX + "foo"))
        self.assertTrue(self.dispatched("foo"))
        self.assertFalse(self.dispatched("bar"))

    def test_matcher_other_filters(self):
        """Matchers with an action and other filters are treated by their action"""
        self.rule(policy=self.matcher(EventAction.MODEL_CREATED, app="authentik.core"))
        self.rule(policy=self.matcher(EventAction.MODEL_UPDATED, model="authentik_core.user"))
        self.rule(policy=self.matcher(EventAction.MODEL_DELETED, client_ip="127.0.0.1"))
        self.assertTrue(self.dispatched(EventAction.MODEL_CREATED))
        self.assertFalse(self.dispatched(EventAction.LOGIN))

    def test_any_action(self):
        """Bindings whose result doesn't only depend on the event action dispatch everything"""
        cases = {
            "expression policy": lambda: {
                "policy": ExpressionPolicy.objects.create(
                    name=generate_id(), expression="return True"
                )
            },
            "user": lambda: {"user": create_test_user()},
            "group": lambda: {"group": Group.objects.create(name=generate_id())},
            "matcher without action": lambda: {"policy": self.matcher()},
            "matcher with empty action": lambda: {"policy": self.matcher("")},
            "matcher with execution logging": lambda: {
                "policy": self.matcher(EventAction.CONFIGURATION_ERROR, execution_logging=True)
            },
            "negated": lambda: {
                "policy": self.matcher(EventAction.CONFIGURATION_ERROR),
                "negate": True,
            },
            "dry run": lambda: {
                "policy": self.matcher(EventAction.CONFIGURATION_ERROR),
                "dry_run": True,
            },
            "failure result": lambda: {
                "policy": self.matcher(EventAction.CONFIGURATION_ERROR),
                "failure_result": True,
            },
        }
        for name, binding in cases.items():
            with self.subTest(name):
                clear_cache()
                NotificationRule.objects.all().delete()
                self.rule(policy=self.matcher(EventAction.UPDATE_AVAILABLE))
                self.assertFalse(self.dispatched(EventAction.LOGIN))
                self.rule(**binding())
                self.assertTrue(self.dispatched(EventAction.LOGIN))

    def test_any_action_other_target(self):
        """Bindings on objects other than notification rules are ignored"""
        self.rule(policy=self.matcher(EventAction.CONFIGURATION_ERROR))
        target = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=target, order=0, policy=self.matcher())
        PolicyBinding.objects.create(target=target, order=1, policy=self.matcher(EventAction.LOGIN))
        self.assertFalse(self.dispatched(EventAction.LOGIN))

    def test_skip_not_remembered(self):
        """A skipped action is checked again for every event"""
        self.assertFalse(self.dispatched(EventAction.LOGIN))

        matcher = self.matcher(EventAction.CONFIGURATION_ERROR)
        rule = self.rule()
        binding = PolicyBinding.objects.create(target=rule, order=0, policy=matcher, enabled=False)
        self.assertFalse(self.dispatched(EventAction.CONFIGURATION_ERROR))

        # enable the binding
        binding.enabled = True
        binding.save()
        self.assertTrue(self.dispatched(EventAction.CONFIGURATION_ERROR))

        # change the matcher's action, without a signal
        self.assertFalse(self.dispatched(EventAction.LOGIN))
        EventMatcherPolicy.objects.filter(pk=matcher.pk).update(action=EventAction.LOGIN)
        self.assertTrue(self.dispatched(EventAction.LOGIN))

        # add a binding that matches any action
        self.assertFalse(self.dispatched(EventAction.LOGOUT))
        PolicyBinding.objects.create(target=rule, order=1, policy=self.matcher())
        self.assertTrue(self.dispatched(EventAction.LOGOUT))

    def test_match_remembered(self):
        """A matching action is dispatched without a query until the timeout passes"""
        rule = self.rule(policy=self.matcher(EventAction.CONFIGURATION_ERROR))
        self.assertEqual(self.binding_queries(EventAction.CONFIGURATION_ERROR), 1)
        self.assertEqual(self.binding_queries(EventAction.CONFIGURATION_ERROR), 0)
        # Other actions are still checked
        self.assertEqual(self.binding_queries(EventAction.LOGIN), 1)
        self.assertEqual(self.binding_queries(EventAction.LOGIN), 1)

        # Still dispatched after the rule is gone, which only costs a task
        rule.delete()
        self.assertTrue(self.dispatched(EventAction.CONFIGURATION_ERROR))
        with patch(
            "authentik.events.notification_filter.monotonic",
            return_value=monotonic() + CACHE_TIMEOUT + 1,
        ):
            self.assertFalse(self.dispatched(EventAction.CONFIGURATION_ERROR))

    def test_any_action_remembered(self):
        """While a binding matches any action, no event is checked until the timeout passes"""
        rule = self.rule(policy=self.matcher())
        self.assertEqual(self.binding_queries(EventAction.LOGIN), 1)
        self.assertEqual(self.binding_queries(EventAction.LOGOUT), 0)

        rule.delete()
        self.assertTrue(self.dispatched(EventAction.LOGOUT))
        with patch(
            "authentik.events.notification_filter.monotonic",
            return_value=monotonic() + CACHE_TIMEOUT + 1,
        ):
            self.assertFalse(self.dispatched(EventAction.LOGOUT))
