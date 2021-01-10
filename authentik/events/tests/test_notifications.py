"""Notification tests"""

from unittest.mock import MagicMock, patch

from rest_framework.test import APITestCase

from authentik.events.models import (
    Event,
    EventAction,
    NotificationTransport,
    NotificationTrigger,
)
from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import PolicyBinding


class TestEventsNotifications(APITestCase):
    """Test Event Notifications"""

    def test_trigger_single(self):
        """Test simple transport triggering"""
        transport = NotificationTransport.objects.create(name="transport")
        trigger = NotificationTrigger.objects.create(
            name="trigger", transport=transport
        )
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch(
            "authentik.events.models.NotificationTransport.execute", execute_mock
        ):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 1)

    def test_trigger_no_action(self):
        """Test trigger without transport"""
        trigger = NotificationTrigger.objects.create(name="trigger")
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch(
            "authentik.events.models.NotificationTransport.execute", execute_mock
        ):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 0)

    def test_policy_error_recursive(self):
        """Test Policy error which would cause recursion"""
        transport = NotificationTransport.objects.create(name="transport")
        trigger = NotificationTrigger.objects.create(
            name="trigger", transport=transport
        )
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
                "authentik.events.models.NotificationTransport.execute", execute_mock
            ):
                Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(passes.call_count, 0)
