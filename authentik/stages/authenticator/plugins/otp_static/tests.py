from django.contrib.admin import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import RequestFactory
from django.test.utils import override_settings

from authentik.stages.authenticator.forms import OTPAuthenticationForm
from authentik.stages.authenticator.tests import TestCase, ThrottlingTestMixin

from .admin import StaticDeviceAdmin, StaticTokenInline
from .lib import add_static_token
from .models import StaticDevice, StaticToken


class DeviceTest(TestCase):
    """A few generic tests to get us started."""

    def setUp(self):
        try:
            self.user = self.create_user("alice", "password")
        except Exception:
            self.skipTest("Unable to create the test user.")

    def test_str(self):
        device = StaticDevice.objects.create(user=self.user, name="Device")

        str(device)

    def test_str_unpopulated(self):
        device = StaticDevice()

        str(device)


class LibTest(TestCase):
    """
    Test miscellaneous library functions.
    """

    def setUp(self):
        try:
            self.user = self.create_user("alice", "password")
        except Exception:
            self.skipTest("Unable to create the test user.")

    def test_add_static_token(self):
        statictoken = add_static_token("alice")

        self.assertEqual(statictoken.device.user, self.user)
        self.assertEqual(self.user.staticdevice_set.count(), 1)

    def test_add_static_token_existing_device(self):
        self.user.staticdevice_set.create(name="Test")
        statictoken = add_static_token("alice")

        self.assertEqual(statictoken.device.user, self.user)
        self.assertEqual(self.user.staticdevice_set.count(), 1)
        self.assertEqual(statictoken.device.name, "Test")

    def test_add_static_token_no_user(self):
        with self.assertRaises(self.User.DoesNotExist):
            add_static_token("bogus")

    def test_add_static_token_specific(self):
        statictoken = add_static_token("alice", "token")

        self.assertEqual(statictoken.token, "token")


class AuthFormTest(TestCase):
    """
    Test the auth form with static tokens.

    We try to honor custom user models, but if we can't create users, we'll
    skip the tests.
    """

    def setUp(self):
        for device_id, username in enumerate(["alice", "bob"]):
            try:
                user = self.create_user(username, "password")
            except IntegrityError:
                self.skipTest("Unable to create a test user.")
            else:
                device = user.staticdevice_set.create(id=device_id + 1)
                device.token_set.create(token=username + "1")
                device.token_set.create(token=username + "1")
                device.token_set.create(token=username + "2")

    def test_empty(self):
        data = {}
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.get_user(), None)

    def test_bad_password(self):
        data = {
            "username": "alice",
            "password": "bogus",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        self.assertEqual(list(form.errors.keys()), ["__all__"])

    def test_no_token(self):
        data = {
            "username": "alice",
            "password": "password",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.get_user().get_username(), "alice")

    def test_passive_token(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_token": "alice1",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertTrue(form.is_valid())
        alice = form.get_user()
        self.assertEqual(alice.get_username(), "alice")
        self.assertIsInstance(alice.otp_device, StaticDevice)
        self.assertEqual(alice.otp_device.token_set.count(), 2)

    def test_spoofed_device(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_device": "otp_static.staticdevice/2",
            "otp_token": "bob1",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        alice = form.get_user()
        self.assertEqual(alice.get_username(), "alice")
        self.assertIsNone(alice.otp_device)

    def test_specific_device_fail(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_device": "otp_email.staticdevice/1",
            "otp_token": "bogus",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertFalse(form.is_valid())
        alice = form.get_user()
        self.assertEqual(alice.get_username(), "alice")
        self.assertIsNone(alice.otp_device)

    def test_specific_device(self):
        data = {
            "username": "alice",
            "password": "password",
            "otp_device": "otp_static.staticdevice/1",
            "otp_token": "alice1",
        }
        form = OTPAuthenticationForm(None, data)

        self.assertTrue(form.is_valid())
        alice = form.get_user()
        self.assertEqual(alice.get_username(), "alice")
        self.assertIsNotNone(alice.otp_device)


@override_settings(
    OTP_STATIC_THROTTLE_FACTOR=1,
)
class ThrottlingTestCase(ThrottlingTestMixin, TestCase):
    def setUp(self):
        try:
            user = self.create_user("alice", "password")
        except IntegrityError:
            self.skipTest("Unable to create a test user.")
        else:
            self.device = user.staticdevice_set.create()
            self.device.token_set.create(token="valid1")
            self.device.token_set.create(token="valid2")
            self.device.token_set.create(token="valid3")

    def valid_token(self):
        return self.device.token_set.first().token

    def invalid_token(self):
        return "bogus"


class StaticDeviceAdminTest(TestCase):
    def setUp(self):
        try:
            self.admin = self.create_user(
                "admin",
                "password",
                email="admin@example.com",
                is_staff=True,
            )
        except IntegrityError:
            self.skipTest("Unable to create test user.")
        else:
            self.device = self.admin.staticdevice_set.create()
        self.device_admin = StaticDeviceAdmin(StaticDevice, AdminSite())
        self.get_request = RequestFactory().get("/")
        self.get_request.user = self.admin

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=True)
    def test_inline_instances_when_sensitive_information_hidden(self):
        self._add_device_perms("change_statictoken")
        instances = self.device_admin.get_inline_instances(self.get_request, obj=None)
        self.assertIsInstance(instances, list)
        self.assertEqual(len(instances), 1)
        self.assertIsInstance(instances[0], StaticTokenInline)
        instances = self.device_admin.get_inline_instances(self.get_request, obj=self.device)
        self.assertEqual(instances, [])

    @override_settings(OTP_ADMIN_HIDE_SENSITIVE_DATA=False)
    def test_inline_instances_when_sensitive_information_shown(self):
        self._add_device_perms("change_statictoken")
        for obj in (None, self.device):
            instances = self.device_admin.get_inline_instances(self.get_request, obj=obj)
            self.assertIsInstance(instances, list)
            self.assertEqual(len(instances), 1)

    #
    # Helpers
    #

    def _add_device_perms(self, *codenames):
        ct = ContentType.objects.get_for_models(StaticDevice, StaticToken)

        perms = [
            Permission.objects.get(content_type__in=ct.values(), codename=codename)
            for codename in codenames
        ]

        self.admin.user_permissions.add(*perms)
