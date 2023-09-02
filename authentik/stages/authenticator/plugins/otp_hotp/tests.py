from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from freezegun import freeze_time

from authentik.stages.authenticator.forms import OTPAuthenticationForm
from authentik.stages.authenticator.tests import TestCase, ThrottlingTestMixin

from .admin import HOTPDeviceAdmin
from .models import HOTPDevice


class HOTPDeviceMixin:
    """
    A TestCase helper that gives us a HOTPDevice to work with.
    """

    # The next three tokens
    tokens = [782373, 313268, 307722]
    key = "d2e8a68036f68960b1c30532bb6c56da5934d879"

    def setUp(self):
        try:
            alice = self.create_user("alice", "password", email="alice@example.com")
        except IntegrityError:
            self.skipTest("Unable to create test user.")
        else:
            self.device = alice.hotpdevice_set.create(
                key=self.key, digits=6, tolerance=1, counter=0
            )


@override_settings(
    OTP_HOTP_THROTTLE_FACTOR=0,
)
class HOTPTest(HOTPDeviceMixin, TestCase):
    def test_normal(self):
        ok = self.device.verify_token(self.tokens[0])

        self.assertTrue(ok)
        self.assertEqual(self.device.counter, 1)

    def test_normal_drift(self):
        ok = self.device.verify_token(self.tokens[1])

        self.assertTrue(ok)
        self.assertEqual(self.device.counter, 2)

    def test_excessive_drift(self):
        ok = self.device.verify_token(self.tokens[2])

        self.assertFalse(ok)
        self.assertEqual(self.device.counter, 0)

    def test_bad_value(self):
        ok = self.device.verify_token(123456)

        self.assertFalse(ok)
        self.assertEqual(self.device.counter, 0)

    def test_config_url_no_issuer(self):
        with override_settings(OTP_HOTP_ISSUER=None):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "hotp")
        self.assertEqual(parsed.path, "/alice")
        self.assertIn("secret", params)
        self.assertNotIn("issuer", params)

    def test_config_url_issuer(self):
        with override_settings(OTP_HOTP_ISSUER="example.com"):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "hotp")
        self.assertEqual(parsed.path, "/example.com%3Aalice")
        self.assertIn("secret", params)
        self.assertIn("issuer", params)
        self.assertEqual(params["issuer"][0], "example.com")

    def test_config_url_issuer_spaces(self):
        with override_settings(OTP_HOTP_ISSUER="Very Trustworthy Source"):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "hotp")
        self.assertEqual(parsed.path, "/Very%20Trustworthy%20Source%3Aalice")
        self.assertIn("secret", params)
        self.assertIn("issuer", params)
        self.assertEqual(params["issuer"][0], "Very Trustworthy Source")

    def test_config_url_issuer_method(self):
        with override_settings(OTP_HOTP_ISSUER=lambda d: d.user.email):
            url = self.device.config_url

        parsed = urlsplit(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "otpauth")
        self.assertEqual(parsed.netloc, "hotp")
        self.assertEqual(parsed.path, "/alice%40example.com%3Aalice")
        self.assertIn("secret", params)
        self.assertIn("issuer", params)
        self.assertEqual(params["issuer"][0], "alice@example.com")


class AuthFormTest(TestCase):
    """
    Test auth form with HOTP tokens
    """

    tokens = HOTPTest.tokens
    key = HOTPTest.key

    def setUp(self):
        try:
            alice = self.create_user("alice", "password")
        except IntegrityError:
            self.skipTest("Unable to create test user.")
        else:
            self.device = alice.hotpdevice_set.create(
                key=self.key, digits=6, tolerance=1, counter=0
            )

    def test_no_token(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_device": self.device.persistent_id,
        }
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.get_user().get_username(), "alice")

    def test_bad_token(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_token": "123456",
            "otp_device": self.device.persistent_id,
        }
        form = OTPAuthenticationForm(None, data)
        self.assertFalse(form.is_valid())

    def test_good_token(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_token": self.tokens[0],
            "otp_device": self.device.persistent_id,
        }
        form = OTPAuthenticationForm(None, data)
        self.assertTrue(form.is_valid())

    def test_attempt_after_fail(self):
        good_data = {
            "username": "alice",
            "password": "password",
            "otp_token": self.tokens[0],
            "otp_device": self.device.persistent_id,
        }
        bad_data = {
            "username": "alice",
            "password": "password",
            "otp_token": "123456",
            "otp_device": self.device.persistent_id,
        }

        with freeze_time() as frozen_time:
            form1 = OTPAuthenticationForm(None, bad_data)
            self.assertFalse(form1.is_valid())

            # Should fail even with good data:
            form2 = OTPAuthenticationForm(None, good_data)
            self.assertFalse(form2.is_valid())
            self.assertIn(
                "Verification temporarily disabled because of 1 failed attempt",
                form2.errors["__all__"][0],
            )

            # Fail again after throttling expired:
            frozen_time.tick(timedelta(seconds=1.1))
            form3 = OTPAuthenticationForm(None, bad_data)
            self.assertFalse(form3.is_valid())
            self.assertIn("Invalid token", form3.errors["__all__"][0])

            # Test n=2 error message:
            form4 = OTPAuthenticationForm(None, bad_data)
            self.assertFalse(form4.is_valid())
            self.assertIn(
                "Verification temporarily disabled because of 2 failed attempts",
                form4.errors["__all__"][0],
            )

            # Pass this time:
            frozen_time.tick(timedelta(seconds=2.1))
            form5 = OTPAuthenticationForm(None, good_data)
            self.assertTrue(form5.is_valid())


class HOTPAdminTest(TestCase):
    def setUp(self):
        """
        Create a device at the fourth time step. The current token is 154567.
        """
        try:
            self.admin = self.create_user(
                "admin", "password", email="admin@example.com", is_staff=True
            )
        except IntegrityError:
            self.skipTest("Unable to create test user.")
        else:
            self.device = self.admin.hotpdevice_set.create(
                key="d2e8a68036f68960b1c30532bb6c56da5934d879",
                digits=6,
                tolerance=1,
                counter=0,
            )
        self.device_admin = HOTPDeviceAdmin(HOTPDevice, AdminSite())
        self.get_request = RequestFactory().get("/")
        self.get_request.user = self.admin

    def test_anonymous(self):
        for suffix in ["config", "qrcode"]:
            with self.subTest(view=suffix):
                url = reverse("admin:otp_hotp_hotpdevice_" + suffix, kwargs={"pk": self.device.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_unauthorized(self):
        self.client.login(username="admin", password="password")

        for suffix in ["config", "qrcode"]:
            with self.subTest(view=suffix):
                url = reverse("admin:otp_hotp_hotpdevice_" + suffix, kwargs={"pk": self.device.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_view_perm(self):
        self._add_device_perms("view_hotpdevice")
        self.client.login(username="admin", password="password")

        for suffix in ["config", "qrcode"]:
            with self.subTest(view=suffix):
                url = reverse("admin:otp_hotp_hotpdevice_" + suffix, kwargs={"pk": self.device.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_change_perm(self):
        self._add_device_perms("change_hotpdevice")
        self.client.login(username="admin", password="password")

        for suffix in ["config", "qrcode"]:
            with self.subTest(view=suffix):
                url = reverse("admin:otp_hotp_hotpdevice_" + suffix, kwargs={"pk": self.device.pk})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True)
    def test_sensitive_information_hidden_while_adding_device(self):
        fields = self._get_fields(device=None)
        self.assertIn("key", fields)
        self.assertNotIn("qrcode_link", fields)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True)
    def test_sensitive_information_hidden_while_changing_device(self):
        fields = self._get_fields(device=self.device)
        self.assertNotIn("key", fields)
        self.assertNotIn("qrcode_link", fields)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=False)
    def test_sensitive_information_shown_while_adding_device(self):
        fields = self._get_fields(device=None)
        self.assertIn("key", fields)
        self.assertNotIn("qrcode_link", fields)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=False)
    def test_sensitive_information_shown_while_changing_device(self):
        fields = self._get_fields(device=self.device)
        self.assertIn("key", fields)
        self.assertIn("qrcode_link", fields)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True)
    def test_list_display_when_sensitive_information_hidden(self):
        self.assertEqual(
            self.device_admin.get_list_display(self.get_request),
            ["user", "name", "confirmed"],
        )

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=False)
    def test_list_display_when_sensitive_information_shown(self):
        self.assertEqual(
            self.device_admin.get_list_display(self.get_request),
            ["user", "name", "confirmed", "qrcode_link"],
        )

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True)
    def test_config_view_when_sensitive_information_hidden(self):
        self._add_device_perms("change_hotpdevice")
        with self.assertRaises(PermissionDenied):
            self.device_admin.config_view(self.get_request, self.device.id)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=False)
    def test_config_view_when_sensitive_information_shown(self):
        self._add_device_perms("change_hotpdevice")
        response = self.device_admin.config_view(self.get_request, self.device.id)
        self.assertEqual(response.status_code, 200)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True)
    def test_qrcode_view_when_sensitive_information_hidden(self):
        self._add_device_perms("change_hotpdevice")
        with self.assertRaises(PermissionDenied):
            self.device_admin.qrcode_view(self.get_request, self.device.id)

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=False)
    def test_qrcode_view_when_sensitive_information_shown(self):
        self._add_device_perms("change_hotpdevice")
        response = self.device_admin.qrcode_view(self.get_request, self.device.id)
        self.assertEqual(response.status_code, 200)

    #
    # Helpers
    #

    def _add_device_perms(self, *codenames):
        ct = ContentType.objects.get_for_model(HOTPDevice)

        perms = [
            Permission.objects.get(content_type=ct, codename=codename) for codename in codenames
        ]

        self.admin.user_permissions.add(*perms)

    def _get_fields(self, device):
        return {
            field
            for fieldset in self.device_admin.get_fieldsets(self.get_request, obj=device)
            for field in fieldset[1]["fields"]
        }


@override_settings(
    OTP_HOTP_THROTTLE_FACTOR=1,
)
class ThrottlingTestCase(HOTPDeviceMixin, ThrottlingTestMixin, TestCase):
    def valid_token(self):
        return self.tokens[0]

    def invalid_token(self):
        return -1
