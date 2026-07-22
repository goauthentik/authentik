"""Notification tests"""

from unittest.mock import MagicMock, PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
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
            Event.new(EventAction.CUSTOM_PREFIX, subject=subject).set_user(actor).save()
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


class TestUserSecurityNotificationsDelivery(APITestCase):
    """End-to-end tests for the default user security notification rules: from the
    client request (or, for login blocks, the event the flow executor emits) all the
    way to the email in the affected user's inbox"""

    BLUEPRINT = "default/events-user-security-notifications.yaml"

    def setUp(self):
        content = BlueprintInstance(path=self.BLUEPRINT).retrieve()
        self.assertTrue(Importer.from_string(content).apply())

    def enable_rule(self, name: str):
        NotificationRule.objects.filter(name=name).update(enabled=True)

    def email_backend(self):
        return patch(
            "authentik.stages.email.models.EmailStage.backend_class",
            PropertyMock(return_value=EmailBackend),
        )

    def test_password_change_email(self):
        """Changing a user's password through the API must email that user"""
        admin = create_test_admin_user()
        user = create_test_user()
        self.client.force_login(admin)
        self.enable_rule("default-notify-user-password-change")

        with self.email_backend():
            response = self.client.post(
                reverse("authentik_api:user-set-password", kwargs={"pk": user.pk}),
                data={"password": generate_id()},
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(user.email, message.to[0])
        self.assertEqual(message.subject, "authentik Notification: your password was changed")
        self.assertIn("The password for your account was just changed", message.body)

    def test_password_change_email_non_http_not_sent(self):
        """A password change outside a request (shell, bootstrap) must not email"""
        user = create_test_user()
        self.enable_rule("default-notify-user-password-change")

        with self.email_backend():
            user.set_password(generate_id())
            user.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_mfa_device_change_emails(self):
        """Adding an MFA device and removing it through the API must email its owner"""
        user = create_test_user()
        self.client.force_login(user)
        self.enable_rule("default-notify-user-mfa-device-change")

        with self.email_backend():
            device = user.staticdevice_set.create()
            response = self.client.delete(
                reverse("authentik_api:staticdevice-detail", kwargs={"pk": device.pk})
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 2)
        added, removed = mail.outbox
        self.assertEqual(added.subject, "authentik Notification: a new MFA device was added")
        self.assertIn("was just added to your account", added.body)
        self.assertEqual(removed.subject, "authentik Notification: an MFA device was removed")
        self.assertIn("was just removed from your account", removed.body)
        for message in mail.outbox:
            self.assertIn(user.email, message.to[0])

    def test_impossible_travel_email(self):
        """A login blocked for impossible travel must email the affected user.

        The flow executor emitting this event is covered by
        authentik/flows/tests/test_markers.py; this test starts from the event."""
        user = create_test_user()
        self.enable_rule("default-notify-user-impossible-travel")

        with self.email_backend():
            Event.new(
                EventAction.LOGIN_BLOCKED,
                message="Distance is further than possible.",
                reasons=["impossible_travel"],
                subject=user,
            ).set_user(user).save()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(user.email, message.to[0])
        self.assertEqual(
            message.subject,
            "authentik Notification: a sign-in from an unusual location was blocked",
        )
        self.assertIn("too far from your previous sign-in", message.body)

    def test_impossible_travel_email_other_reasons_not_sent(self):
        """A login blocked for other reasons must not trigger the impossible travel rule"""
        user = create_test_user()
        self.enable_rule("default-notify-user-impossible-travel")

        with self.email_backend():
            Event.new(
                EventAction.LOGIN_BLOCKED,
                message="Client IP is not in an allowed country.",
                reasons=["forbidden_country"],
                subject=user,
            ).set_user(user).save()

        self.assertEqual(len(mail.outbox), 0)

    def test_welcome_email(self):
        """Creating a user through the API must send them the welcome email"""
        admin = create_test_admin_user()
        self.client.force_login(admin)
        self.enable_rule("default-notify-user-welcome")
        username = generate_id()

        with self.email_backend():
            response = self.client.post(
                reverse("authentik_api:user-list"),
                data={
                    "username": username,
                    "name": username,
                    "email": f"{username}@goauthentik.io",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(f"{username}@goauthentik.io", message.to[0])
        self.assertEqual(message.subject, "Welcome to authentik")
        self.assertIn(username, message.alternatives[0][0])
