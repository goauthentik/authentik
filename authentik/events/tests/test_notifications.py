"""Notification tests"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.core.models import Group, User
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationRule,
    NotificationTransport,
    NotificationWebhookMapping,
    TransportMode,
)
from authentik.lib.generators import generate_id
from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import PolicyBinding


class TestEventsNotifications(TestCase):
    """Test Event Notifications"""

    def setUp(self) -> None:
        self.group = Group.objects.create(name="test-group")
        self.user = User.objects.create(name="test-user", username="test")
        self.group.users.add(self.user)
        self.group.save()

    def test_trigger_empty(self):
        """Test trigger without any policies attached"""
        transport = NotificationTransport.objects.create(name="transport")
        trigger = NotificationRule.objects.create(name="trigger", group=self.group)
        trigger.transports.add(transport)
        trigger.save()

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 0)

    def test_trigger_single(self):
        """Test simple transport triggering"""
        transport = NotificationTransport.objects.create(name="transport")
        trigger = NotificationRule.objects.create(name="trigger", group=self.group)
        trigger.transports.add(transport)
        trigger.save()
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 1)

    def test_trigger_no_group(self):
        """Test trigger without group"""
        trigger = NotificationRule.objects.create(name="trigger")
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 0)

    def test_policy_error_recursive(self):
        """Test Policy error which would cause recursion"""
        transport = NotificationTransport.objects.create(name="transport")
        NotificationRule.objects.filter(name__startswith="default").delete()
        trigger = NotificationRule.objects.create(name="trigger", group=self.group)
        trigger.transports.add(transport)
        trigger.save()
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        passes = MagicMock(side_effect=PolicyException)
        with patch("authentik.policies.event_matcher.models.EventMatcherPolicy.passes", passes):
            with patch("authentik.events.models.NotificationTransport.send", execute_mock):
                Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(passes.call_count, 1)

    def test_transport_once(self):
        """Test transport's send_once"""
        user2 = User.objects.create(name="test2-user", username="test2")
        self.group.users.add(user2)
        self.group.save()

        transport = NotificationTransport.objects.create(name="transport", send_once=True)
        NotificationRule.objects.filter(name__startswith="default").delete()
        trigger = NotificationRule.objects.create(name="trigger", group=self.group)
        trigger.transports.add(transport)
        trigger.save()
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 1)

    def test_transport_mapping(self):
        """Test transport mapping"""
        mapping = NotificationWebhookMapping.objects.create(
            name=generate_id(),
            expression="""notification.body = 'foo'""",
        )

        transport = NotificationTransport.objects.create(
            name="transport", webhook_mapping=mapping, mode=TransportMode.LOCAL
        )
        NotificationRule.objects.filter(name__startswith="default").delete()
        trigger = NotificationRule.objects.create(name="trigger", group=self.group)
        trigger.transports.add(transport)
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        Notification.objects.all().delete()
        Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(Notification.objects.first().body, "foo")
