"""Alert tests"""

from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase

from authentik.events.models import (
    Event,
    EventAction,
    EventAlertAction,
    EventAlertTrigger,
)
from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import PolicyBinding


class TestEventsAlets(APITestCase):
    """Test Event Alerts"""

    def test_trigger_single(self):
        """Test simple action triggering"""
        action = EventAlertAction.objects.create(name="action")
        trigger = EventAlertTrigger.objects.create(name="trigger", action=action)
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.EventAlertAction.execute", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 1)

    def test_trigger_no_action(self):
        """Test trigger without action"""
        trigger = EventAlertTrigger.objects.create(name="trigger")
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.EventAlertAction.execute", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 0)

    def test_policy_error_recursive(self):
        """Test Policy error which would cause recursion"""
        action = EventAlertAction.objects.create(name="action")
        trigger = EventAlertTrigger.objects.create(name="trigger", action=action)
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        passes = MagicMock(side_effect=PolicyException)
        with patch(
            "authentik.policies.event_matcher.models.EventMatcherPolicy.passes", passes
        ):
            with patch(
                "authentik.events.models.EventAlertAction.execute", execute_mock
            ):
                Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(passes.call_count, 0)
