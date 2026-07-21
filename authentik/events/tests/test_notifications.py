"""Notification tests"""

from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
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

    def test_trigger_disabled(self):
        """Test that a disabled rule does not trigger even when its policies match"""
        transport = NotificationTransport.objects.create(name=generate_id())
        trigger = NotificationRule.objects.create(
            name=generate_id(), destination_group=self.group, enabled=False
        )
        trigger.transports.add(transport)
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX).save()
        self.assertEqual(execute_mock.call_count, 0)

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

    def test_trigger_event_subject(self):
        """Test trigger routing to the event's subject, not its actor"""
        actor = create_test_user()
        subject = create_test_user()
        transport = NotificationTransport.objects.create(name=generate_id())
        trigger = NotificationRule.objects.create(
            name=generate_id(), destination_event_subject=True
        )
        trigger.transports.add(transport)
        trigger.save()
        matcher = EventMatcherPolicy.objects.create(
            name="matcher", action=EventAction.CUSTOM_PREFIX
        )
        PolicyBinding.objects.create(target=trigger, policy=matcher, order=0)

        execute_mock = MagicMock()
        with patch("authentik.events.models.NotificationTransport.send", execute_mock):
            Event.new(EventAction.CUSTOM_PREFIX, subject_uuid=subject.uuid).set_user(actor).save()
        self.assertEqual(execute_mock.call_count, 1)
        notification: Notification = execute_mock.call_args[0][0]
        self.assertEqual(notification.user, subject)

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


class TestUserSecurityNotificationRules(APITestCase):
    """Test the default user security notification rules blueprint"""

    BLUEPRINT = "default/events-user-security-notifications.yaml"
    RULE_NAMES = [
        "default-notify-user-password-change",
        "default-notify-user-mfa-device-change",
        "default-notify-user-impossible-travel",
        "default-notify-user-account-lockdown",
        "default-notify-user-welcome",
    ]

    def apply(self):
        content = BlueprintInstance(path=self.BLUEPRINT).retrieve()
        self.assertTrue(Importer.from_string(content).apply())

    def test_rules_disabled_by_default(self):
        """All user notification rules ship disabled"""
        NotificationRule.objects.filter(name__in=self.RULE_NAMES).delete()
        self.apply()
        for name in self.RULE_NAMES:
            with self.subTest(rule=name):
                self.assertFalse(NotificationRule.objects.get(name=name).enabled)

    def test_reapply_keeps_admin_changes(self):
        """Re-applying the blueprint must not revert a rule the admin enabled"""
        NotificationRule.objects.filter(name__in=self.RULE_NAMES).delete()
        self.apply()
        rule = NotificationRule.objects.get(name=self.RULE_NAMES[0])
        rule.enabled = True
        rule.save()
        self.apply()
        rule.refresh_from_db()
        self.assertTrue(rule.enabled)
