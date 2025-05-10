"""Test email stage tasks"""

from unittest.mock import patch

from django.core.mail import EmailMultiAlternatives
from django.test import TestCase

from authentik.common.utils.reflection import class_to_path
from authentik.core.tests.utils import create_test_admin_user
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import get_email_body, send_mails


class TestEmailTasks(TestCase):
    """Test email stage tasks"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.stage = EmailStage.objects.create(
            name="test-email",
            use_global_settings=True,
        )
        self.auth_stage = AuthenticatorEmailStage.objects.create(
            name="test-auth-email",
            use_global_settings=True,
        )

    def test_get_email_body_html(self):
        """Test get_email_body with HTML alternative"""
        message = EmailMultiAlternatives()
        message.body = "plain text"
        message.attach_alternative("<p>html content</p>", "text/html")
        self.assertEqual(get_email_body(message), "<p>html content</p>")

    def test_get_email_body_plain(self):
        """Test get_email_body with plain text only"""
        message = EmailMultiAlternatives()
        message.body = "plain text"
        self.assertEqual(get_email_body(message), "plain text")

    def test_send_mails_email_stage(self):
        """Test send_mails with EmailStage"""
        message = EmailMultiAlternatives()
        with patch("authentik.stages.email.tasks.send_mail") as mock_send:
            send_mails(self.stage, message)
            mock_send.s.assert_called_once_with(
                message.__dict__, class_to_path(EmailStage), str(self.stage.pk)
            )

    def test_send_mails_authenticator_stage(self):
        """Test send_mails with AuthenticatorEmailStage"""
        message = EmailMultiAlternatives()
        with patch("authentik.stages.email.tasks.send_mail") as mock_send:
            send_mails(self.auth_stage, message)
            mock_send.s.assert_called_once_with(
                message.__dict__, class_to_path(AuthenticatorEmailStage), str(self.auth_stage.pk)
            )
