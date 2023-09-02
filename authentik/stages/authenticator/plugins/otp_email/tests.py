from datetime import timedelta

from django.core import mail
from django.db import IntegrityError
from django.test.utils import override_settings
from freezegun import freeze_time

from authentik.stages.authenticator.forms import OTPAuthenticationForm
from authentik.stages.authenticator.tests import TestCase, ThrottlingTestMixin

from .models import EmailDevice


class EmailDeviceMixin:
    def setUp(self):
        try:
            alice = self.create_user("alice", "password")
        except IntegrityError:
            self.skipTest("Failed to create user.")
        else:
            self.device = alice.emaildevice_set.create()

        if hasattr(alice, "email"):
            alice.email = "alice@example.com"
            alice.save()
        else:
            self.skipTest("User model has no email.")


class AuthFormTest(EmailDeviceMixin, TestCase):
    @override_settings(OTP_EMAIL_SENDER="test@example.com")
    def test_email_interaction(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_device": "otp_email.emaildevice/1",
            "otp_token": "",
            "otp_challenge": "1",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        alice = form.get_user()
        self.assertEqual(alice.get_username(), "alice")
        self.assertIsNone(alice.otp_device)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])

        self.device.refresh_from_db()
        data["otp_token"] = self.device.token
        del data["otp_challenge"]
        form = OTPAuthenticationForm(None, data)

        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.get_user().otp_device, EmailDevice)


@override_settings(
    DEFAULT_FROM_EMAIL="root@localhost",
    OTP_EMAIL_THROTTLE_FACTOR=0,
)
class EmailTest(EmailDeviceMixin, TestCase):
    def test_token_generator(self):
        self.device.generate_token()
        self.device.token.isnumeric()

    def test_invalid_token(self):
        self.device.generate_token()
        self.assertFalse(self.device.verify_token(0))

    def test_no_reuse(self):
        self.device.generate_token()
        token = self.device.token
        self.assertTrue(self.device.verify_token(token))
        self.assertFalse(self.device.verify_token(token))

    def test_token_expiry(self):
        self.device.generate_token()
        token = self.device.token
        with freeze_time() as frozen_time:
            frozen_time.tick(delta=timedelta(seconds=301))
            self.assertFalse(self.device.verify_token(token))

    def test_defaults(self):
        self.device.generate_challenge()

        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]

        with self.subTest(field="from_email"):
            self.assertEqual(msg.from_email, "root@localhost")
        with self.subTest(field="body"):
            self.assertEqual(msg.body, "Test template 1: {}\n".format(self.device.token))

    @override_settings(
        OTP_EMAIL_SENDER="webmaster@example.com",
        OTP_EMAIL_SUBJECT="Test subject",
        OTP_EMAIL_BODY_TEMPLATE="Test template 2: {{token}}",
    )
    def test_settings(self):
        self.device.generate_challenge()

        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]

        with self.subTest(field="from_email"):
            self.assertEqual(msg.from_email, "webmaster@example.com")
        with self.subTest(field="subject"):
            self.assertEqual(msg.subject, "Test subject")
        with self.subTest(field="body"):
            self.assertEqual(msg.body, "Test template 2: {}".format(self.device.token))

    @override_settings(
        OTP_EMAIL_SENDER="webmaster@example.com",
        OTP_EMAIL_SUBJECT="Test subject",
        OTP_EMAIL_BODY_HTML_TEMPLATE="<div>{{token}}</div>",
    )
    def test_settings_html_template(self):
        self.device.generate_challenge()

        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]

        with self.subTest(field="from_email"):
            self.assertEqual(msg.from_email, "webmaster@example.com")
        with self.subTest(field="subject"):
            self.assertEqual(msg.subject, "Test subject")
        with self.subTest(field="body"):
            self.assertEqual(msg.body, "Test template 1: {}\n".format(self.device.token))
        with self.subTest(field="alternatives"):
            self.assertEqual(
                msg.alternatives[0],
                ("<div>{}</div>".format(self.device.token), "text/html"),
            )

    @override_settings(
        OTP_EMAIL_SENDER="webmaster@example.com",
        OTP_EMAIL_SUBJECT="Test subject",
        OTP_EMAIL_BODY_TEMPLATE_PATH="otp/email/custom.txt",
    )
    def test_settings_template_path(self):
        self.device.generate_challenge()

        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]

        with self.subTest(field="from_email"):
            self.assertEqual(msg.from_email, "webmaster@example.com")
        with self.subTest(field="subject"):
            self.assertEqual(msg.subject, "Test subject")
        with self.subTest(field="body"):
            self.assertEqual(msg.body, "Test template 3: {}\n".format(self.device.token))

    @override_settings(
        OTP_EMAIL_SENDER="webmaster@example.com",
        OTP_EMAIL_SUBJECT="Test subject",
        OTP_EMAIL_BODY_HTML_TEMPLATE_PATH="otp/email/custom_html.html",
    )
    def test_settings_html_template_path(self):
        self.device.generate_challenge()

        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]

        with self.subTest(field="from_email"):
            self.assertEqual(msg.from_email, "webmaster@example.com")
        with self.subTest(field="subject"):
            self.assertEqual(msg.subject, "Test subject")
        with self.subTest(field="body"):
            self.assertEqual(msg.body, "Test template 1: {}\n".format(self.device.token))
        with self.subTest(field="alternatives"):
            self.assertEqual(
                msg.alternatives[0],
                ("<p>{}</p>".format(self.device.token), "text/html"),
            )

    @override_settings(
        OTP_EMAIL_SENDER="webmaster@example.com",
        OTP_EMAIL_SUBJECT="Test subject",
        OTP_EMAIL_BODY_TEMPLATE="Test template 4: {{token}} {{foo}} {{bar}}",
    )
    def test_settings_extra_template_options(self):
        extra_context = {"foo": "extra 1", "bar": "extra 2"}
        self.device.generate_challenge(extra_context)

        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]

        with self.subTest(field="from_email"):
            self.assertEqual(msg.from_email, "webmaster@example.com")
        with self.subTest(field="subject"):
            self.assertEqual(msg.subject, "Test subject")
        with self.subTest(field="body"):
            self.assertEqual(
                msg.body,
                "Test template 4: {} {} {}".format(
                    self.device.token, extra_context["foo"], extra_context["bar"]
                ),
            )

    def test_alternative_email(self):
        self.device.email = "alice2@example.com"
        self.device.save()

        self.device.generate_challenge()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice2@example.com"])


@override_settings(
    OTP_EMAIL_THROTTLE_FACTOR=1,
)
class ThrottlingTestCase(EmailDeviceMixin, ThrottlingTestMixin, TestCase):
    def valid_token(self):
        if self.device.token is None:
            self.device.generate_token()

        return self.device.token

    def invalid_token(self):
        return -1
