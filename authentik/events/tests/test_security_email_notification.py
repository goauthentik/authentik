"""Tests for security email notification functionality"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import TestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction, NotificationRule
from authentik.events.tasks import notification_security_email
from authentik.tenants.models import Tenant


class TestSecurityEmailNotification(TestCase):
    """Test security email notification task"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.tenant = Tenant.objects.first()
        self.tenant.security_email = "security@test.com"
        self.tenant.save()

    def test_security_email_sent_when_configured(self):
        """Test that email is sent when security_email is configured"""
        event = Event.new(
            EventAction.PANIC_BUTTON_TRIGGERED,
            reason="Test reason",
            affected_user="testuser",
            triggered_by="admin",
        )
        event.set_user(self.user)
        event.save()

        rule = NotificationRule.objects.create(
            name="test_rule",
            destination_security_email=True,
        )

        with patch("authentik.stages.email.tasks.send_mail") as mock_send_mail:
            mock_send_mail.send_with_options = MagicMock()
            notification_security_email(str(event.pk), str(rule.pk))
            mock_send_mail.send_with_options.assert_called_once()

    def test_security_email_not_sent_when_not_configured(self):
        """Test that email is not sent when security_email is empty"""
        self.tenant.security_email = ""
        self.tenant.save()

        event = Event.new(
            EventAction.PANIC_BUTTON_TRIGGERED,
            reason="Test reason",
            affected_user="testuser",
            triggered_by="admin",
        )
        event.set_user(self.user)
        event.save()

        rule = NotificationRule.objects.create(
            name="test_rule",
            destination_security_email=True,
        )

        with patch("authentik.stages.email.tasks.send_mail") as mock_send_mail:
            mock_send_mail.send_with_options = MagicMock()
            notification_security_email(str(event.pk), str(rule.pk))
            mock_send_mail.send_with_options.assert_not_called()

    def test_security_email_not_sent_when_event_missing(self):
        """Test that task handles missing event gracefully"""
        rule = NotificationRule.objects.create(
            name="test_rule",
            destination_security_email=True,
        )

        with patch("authentik.stages.email.tasks.send_mail") as mock_send_mail:
            mock_send_mail.send_with_options = MagicMock()
            notification_security_email(str(uuid4()), str(rule.pk))
            mock_send_mail.send_with_options.assert_not_called()

    def test_security_email_not_sent_when_rule_missing(self):
        """Test that task handles missing rule gracefully"""
        event = Event.new(
            EventAction.PANIC_BUTTON_TRIGGERED,
            reason="Test reason",
            affected_user="testuser",
            triggered_by="admin",
        )
        event.set_user(self.user)
        event.save()

        with patch("authentik.stages.email.tasks.send_mail") as mock_send_mail:
            mock_send_mail.send_with_options = MagicMock()
            notification_security_email(str(event.pk), str(uuid4()))
            mock_send_mail.send_with_options.assert_not_called()

    def test_security_email_includes_event_context(self):
        """Test that email includes event context in the message"""
        event = Event.new(
            EventAction.PANIC_BUTTON_TRIGGERED,
            reason="Suspicious activity detected",
            affected_user="compromised_user",
            triggered_by="security_admin",
        )
        event.set_user(self.user)
        event.save()

        rule = NotificationRule.objects.create(
            name="test_rule",
            destination_security_email=True,
        )

        with patch("authentik.stages.email.tasks.send_mail") as mock_send_mail:
            mock_send_mail.send_with_options = MagicMock()

            notification_security_email(str(event.pk), str(rule.pk))

            # Verify send_mail was called
            mock_send_mail.send_with_options.assert_called_once()

            # Get the email dict that was passed to send_mail
            call_args = mock_send_mail.send_with_options.call_args
            email_dict = call_args[1]["args"][0]

            # Verify the email contains the correct recipient and subject
            self.assertIn("security@test.com", str(email_dict["to"]))
            self.assertIn(EventAction.PANIC_BUTTON_TRIGGERED, email_dict["subject"])
