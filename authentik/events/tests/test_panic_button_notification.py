"""Test Panic Button Notification Task"""

from unittest.mock import patch

from django.test import TestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.events.tasks import panic_button_notification
from authentik.lib.generators import generate_id
from authentik.tenants.models import Tenant


class TestPanicButtonNotificationTask(TestCase):
    """Test Panic Button Notification Task"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.admin.email = f"{generate_id()}@admin.test"
        self.admin.save()
        self.user = create_test_user()
        self.user.email = f"{generate_id()}@user.test"
        self.user.save()
        self.tenant = Tenant.objects.first()
        self.tenant.panic_button_security_email = "security@test.com"
        self.tenant.save()

    def test_notify_user_only(self):
        """Test notification sent only to affected user"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=True,
                notify_admins=False,
                notify_security=False,
            )

        self.assertEqual(mock.call_count, 1)
        call_args = mock.call_args
        message_dict = call_args.kwargs["args"][0]
        # Check that user email is in recipients (sanitized format)
        self.assertEqual(len(message_dict["to"]), 1)
        self.assertIn(self.user.email, message_dict["to"][0])
        self.assertIn("Your Account Has Been Locked", message_dict["subject"])

    def test_notify_admins_only(self):
        """Test notification sent only to admins"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=True,
                notify_security=False,
            )

        self.assertEqual(mock.call_count, 1)
        call_args = mock.call_args
        message_dict = call_args.kwargs["args"][0]
        # Admin should be in the recipients (sanitized format "Name <email>")
        recipients_str = " ".join(message_dict["to"])
        self.assertIn(self.admin.email, recipients_str)
        self.assertIn("Panic Button Triggered", message_dict["subject"])

    def test_notify_security_only(self):
        """Test notification sent only to security email"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=False,
                notify_security=True,
            )

        self.assertEqual(mock.call_count, 1)
        call_args = mock.call_args
        message_dict = call_args.kwargs["args"][0]
        # Security email should be in recipients (sanitized format)
        self.assertEqual(len(message_dict["to"]), 1)
        self.assertIn("security@test.com", message_dict["to"][0])
        self.assertIn("SECURITY ALERT", message_dict["subject"])

    def test_notify_all(self):
        """Test notification sent to all recipients"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=True,
                notify_admins=True,
                notify_security=True,
            )

        # Should be 3 calls: user, admins, security
        self.assertEqual(mock.call_count, 3)

    def test_notify_none(self):
        """Test no notifications when all disabled"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=False,
                notify_security=False,
            )

        mock.assert_not_called()

    def test_user_without_email(self):
        """Test user notification skipped when user has no email"""
        self.user.email = ""
        self.user.save()

        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=True,
                notify_admins=False,
                notify_security=False,
            )

        mock.assert_not_called()

    def test_security_email_not_set(self):
        """Test security notification skipped when no security email configured"""
        self.tenant.panic_button_security_email = ""
        self.tenant.save()

        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=False,
                notify_security=True,
            )

        mock.assert_not_called()

    def test_admin_notification_excludes_affected_user(self):
        """Test admin notification excludes the affected user from recipients"""
        # Make the target user also an admin
        admin_group = Group.objects.create(name="admin-test", is_superuser=True)
        admin_group.users.add(self.user)

        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=True,
                notify_security=False,
            )

        self.assertEqual(mock.call_count, 1)
        call_args = mock.call_args
        message_dict = call_args.kwargs["args"][0]
        recipients_str = " ".join(message_dict["to"])
        # Affected user should not be in admin recipients
        self.assertNotIn(self.user.email, recipients_str)
        # Other admin should still be included
        self.assertIn(self.admin.email, recipients_str)

    def test_no_admins_with_email(self):
        """Test admin notification skipped when no admins have email"""
        self.admin.email = ""
        self.admin.save()

        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=True,
                notify_security=False,
            )

        mock.assert_not_called()

    def test_user_not_found(self):
        """Test task handles missing user gracefully"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=99999,  # Non-existent user
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=True,
                notify_admins=True,
                notify_security=True,
            )

        mock.assert_not_called()

    def test_triggered_by_not_found(self):
        """Test task handles missing triggered_by user gracefully"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=99999,  # Non-existent user
                reason="Test reason",
                notify_user=True,
                notify_admins=True,
                notify_security=True,
            )

        mock.assert_not_called()

    def test_email_delay_between_messages(self):
        """Test that emails are sent with delays to avoid rate limits"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=True,
                notify_admins=True,
                notify_security=True,
            )

        # Verify delays are applied (0, 1500, 3000 ms)
        self.assertEqual(mock.call_count, 3)
        delays = [call.kwargs.get("delay", 0) for call in mock.call_args_list]
        self.assertEqual(delays[0], 0)  # First email, no delay
        self.assertEqual(delays[1], 1500)  # Second email
        self.assertEqual(delays[2], 3000)  # Third email

    def test_correct_subjects_sent(self):
        """Test that correct subjects are used for each notification type"""
        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Suspicious activity detected",
                notify_user=True,
                notify_admins=True,
                notify_security=True,
            )

        self.assertEqual(mock.call_count, 3)
        subjects = [call.kwargs["args"][0]["subject"] for call in mock.call_args_list]
        # Check subjects contain expected text
        self.assertTrue(any("Your Account Has Been Locked" in s for s in subjects))
        self.assertTrue(any("Panic Button Triggered" in s for s in subjects))
        self.assertTrue(any("SECURITY ALERT" in s for s in subjects))

    def test_multiple_admins(self):
        """Test notification sent to multiple admins"""
        # Create another admin
        admin2 = create_test_admin_user()
        admin2.email = f"{generate_id()}@admin2.test"
        admin2.save()

        with patch("authentik.stages.email.tasks.send_mail.send_with_options") as mock:
            panic_button_notification(
                affected_user_pk=self.user.pk,
                triggered_by_pk=self.admin.pk,
                reason="Test reason",
                notify_user=False,
                notify_admins=True,
                notify_security=False,
            )

        self.assertEqual(mock.call_count, 1)
        call_args = mock.call_args
        message_dict = call_args.kwargs["args"][0]
        recipients_str = " ".join(message_dict["to"])
        self.assertIn(self.admin.email, recipients_str)
        self.assertIn(admin2.email, recipients_str)
