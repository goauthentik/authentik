"""Test email management commands"""

from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.core.management import call_command
from django.test import TestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.stages.email.models import EmailStage


class TestEmailManagementCommands(TestCase):
    """Test email management commands"""

    def setUp(self):
        self.user = create_test_admin_user()

    def test_test_email_command_with_stage(self):
        """Test test_email command with specified stage"""
        EmailStage.objects.create(
            name="test-stage",
            from_address="test@authentik.local",
            host="localhost",
            port=25,
        )

        with patch("authentik.stages.email.models.EmailStage.backend_class", EmailBackend):
            out = StringIO()
            call_command("test_email", "test@example.com", stage="test-stage", stdout=out)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "authentik Test-Email")
            self.assertEqual(mail.outbox[0].to, ["test@example.com"])
            self.assertIn("Test email sent", out.getvalue())

    def test_test_email_command_with_global_settings(self):
        """Test test_email command with global settings"""
        # Mock the backend to use Django's locmem backend
        with patch("authentik.stages.email.models.EmailStage.backend_class", EmailBackend):
            out = StringIO()
            call_command("test_email", "test@example.com", stdout=out)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "authentik Test-Email")
            self.assertEqual(mail.outbox[0].to, ["test@example.com"])
            self.assertIn("Test email sent", out.getvalue())

    def test_test_email_command_invalid_stage(self):
        """Test test_email command with invalid stage"""
        out = StringIO()
        err = StringIO()
        call_command("test_email", "test@example.com", stage="nonexistent", stdout=out, stderr=err)

        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("does not exist", err.getvalue())

    def test_test_email_command_with_custom_from(self):
        """Test test_email command respects custom from address"""
        EmailStage.objects.create(
            name="test-stage",
            from_address="custom@authentik.local",
            host="localhost",
            port=25,
        )

        with patch("authentik.stages.email.models.EmailStage.backend_class", EmailBackend):
            out = StringIO()
            call_command("test_email", "test@example.com", stage="test-stage", stdout=out)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].from_email, "custom@authentik.local")
            self.assertEqual(mail.outbox[0].to, ["test@example.com"])
            self.assertIn("Test email sent", out.getvalue())
