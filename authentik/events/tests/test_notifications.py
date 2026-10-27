"""Notification tests"""

from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationRule,
    NotificationSeverity,
    NotificationTransport,
    NotificationWebhookMapping,
    TransportMode,
)
from authentik.lib.generators import generate_id
from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import PolicyBinding


class TestEventsNotifications(APITestCase):
    """Test Event Notifications"""

    def setUp(self) -> None:
        self.group = Group.objects.create(name="test-group")
        self.user = User.objects.create(name="test-user", username="test")
        self.group.users.add(self.user)
        self.group.save()

    def test_trigger_empty(self):
        """Test trigger without any policies attached"""
        transport = NotificationTransport.objects.create(name=generate_id())
        trigger = NotificationRule.objects.create(name=generate_id(), destination_group=self.group)
        trigger.transports.add(transport)
        trigger.save()

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 0)

    def test_trigger_single(self):
        """Test simple transport triggering"""
        transport = NotificationTransport.objects.create(name=generate_id())
        trigger = NotificationRule.objects.create(name=generate_id(), destination_group=self.group)
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

    def test_trigger_event_user(self):
        """Test trigger with event user"""
        user = create_test_user()
        transport = NotificationTransport.objects.create(name=generate_id())
        trigger = NotificationRule.objects.create(name=generate_id(), destination_event_user=True)
        trigger.transports.add(transport)
        trigger.save()
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).set_user(user).save()
        self.assertEqual(execute_mock.call_count, 1)
        notification: Notification = execute_mock.call_args[0][0]
        self.assertEqual(notification.user, user)

    def test_trigger_no_group(self):
        """Test trigger without group"""
        trigger = NotificationRule.objects.create(name=generate_id())
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
        transport = NotificationTransport.objects.create(name=generate_id())
        NotificationRule.objects.filter(name__startswith="default").delete()
        trigger = NotificationRule.objects.create(name=generate_id(), destination_group=self.group)
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

        transport = NotificationTransport.objects.create(name=generate_id(), send_once=True)
        NotificationRule.objects.filter(name__startswith="default").delete()
        trigger = NotificationRule.objects.create(name=generate_id(), destination_group=self.group)
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
            name=generate_id(), webhook_mapping_body=mapping, mode=TransportMode.LOCAL
        )
        NotificationRule.objects.filter(name__startswith="default").delete()
        trigger = NotificationRule.objects.create(name=generate_id(), destination_group=self.group)
        trigger.transports.add(transport)
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        Notification.objects.all().delete()
        Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(Notification.objects.first().body, "foo")

    def test_api_mark_all_seen(self):
        """Test mark_all_seen"""
        self.client.force_login(self.user)

        Notification.objects.create(
            severity=NotificationSeverity.NOTICE, body="foo", user=self.user, seen=False
        )

        response = self.client.post(reverse("authentik_api:notification-mark-all-seen"))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Notification.objects.filter(body="foo", seen=False).exists())

    def test_trigger_multiple_rules(self):
        """Test all rules are evaluated for one event, with policy, group, user and negated
        bindings"""
        NotificationRule.objects.all().delete()
        other_group = Group.objects.create(name=generate_id())
        transport = NotificationTransport.objects.create(name=generate_id())
        matcher = EventMatcherPolicy.objects.create(
            name=generate_id(), action=EventAction.CUSTOM_PREFIX
        )
        no_match = EventMatcherPolicy.objects.create(name=generate_id(), action=EventAction.LOGIN)

        def rule(severity: NotificationSeverity, **binding) -> NotificationRule:
            trigger = NotificationRule.objects.create(
                name=generate_id(), destination_event_user=True, severity=severity
            )
            trigger.transports.add(transport)
            if binding:
                PolicyBinding.objects.create(target=trigger, order=0, **binding)
            return trigger

        rule(NotificationSeverity.ALERT, policy=matcher)
        rule(NotificationSeverity.WARNING, group=self.group)
        rule(NotificationSeverity.NOTICE, group=other_group, negate=True)
        rule(NotificationSeverity.ALERT, user=self.user, negate=True)
        rule(NotificationSeverity.ALERT, policy=no_match)
        rule(NotificationSeverity.ALERT, group=other_group)
        rule(NotificationSeverity.ALERT, policy=matcher, enabled=False)
        rule(NotificationSeverity.ALERT)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).set_user(self.user).save()
        self.assertEqual(
            sorted(call[0][0].severity for call in execute_mock.call_args_list),
            sorted(
                [
                    NotificationSeverity.ALERT,
                    NotificationSeverity.WARNING,
                    NotificationSeverity.NOTICE,
                ]
            ),
        )
        for call in execute_mock.call_args_list:
            self.assertEqual(call[0][0].user, self.user)
