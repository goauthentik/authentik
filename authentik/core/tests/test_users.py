"""user tests"""

from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.http import HttpRequest
from django.test.testcases import TestCase

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.core.signals import password_changed, password_hash_changed
from authentik.events.models import Event
from authentik.lib.generators import generate_id
from authentik.stages.password.models import PasswordDevice


class TestUsers(TestCase):
    """Test user"""

    def test_user_managed_role(self):
        """Test user managed role"""
        perm = "authentik_core.view_user"
        user = User.objects.create(username=generate_id())
        user.assign_perms_to_managed_role(perm)
        self.assertEqual(user.roles.count(), 1)
        self.assertTrue(user.has_perm(perm))
        user.remove_perms_from_managed_role(perm)
        self.assertFalse(user.has_perm(perm))

    def test_user_ak_groups(self):
        """Test user.ak_groups is a proxy for user.groups"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(user.ak_groups, user.groups)

    def test_user_ak_groups_event(self):
        """Test user.ak_groups creates exactly one event"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(Event.objects.count(), 0)
        user.ak_groups.all()
        self.assertEqual(Event.objects.count(), 1)
        user.ak_groups.all()
        self.assertEqual(Event.objects.count(), 1)

    def test_locale_user_setting_wins_over_language_code(self):
        """Test the user's saved locale takes precedence over request.LANGUAGE_CODE"""
        user = User.objects.create(
            username=generate_id(),
            attributes={"settings": {"locale": "de"}},
        )
        request = HttpRequest()
        request.LANGUAGE_CODE = "fr"
        self.assertEqual(user.locale(request), "de")

    def test_locale_falls_back_to_language_code(self):
        """Test request.LANGUAGE_CODE is used when the user has no saved locale"""
        user = User.objects.create(username=generate_id())
        request = HttpRequest()
        request.LANGUAGE_CODE = "fr"
        self.assertEqual(user.locale(request), "fr")

    def test_locale_empty_user_setting_falls_back_to_language_code(self):
        """Test an empty saved locale does not shadow request.LANGUAGE_CODE"""
        user = User.objects.create(
            username=generate_id(),
            attributes={"settings": {"locale": ""}},
        )
        request = HttpRequest()
        request.LANGUAGE_CODE = "fr"
        self.assertEqual(user.locale(request), "fr")

    def test_locale_no_request_returns_user_setting(self):
        """Test the user's saved locale is returned when there is no request"""
        user = User.objects.create(
            username=generate_id(),
            attributes={"settings": {"locale": "de"}},
        )
        self.assertEqual(user.locale(), "de")

    def test_locale_no_request_no_setting_returns_empty(self):
        """Test an empty string is returned when there is no request and no saved locale"""
        user = User.objects.create(username=generate_id())
        self.assertEqual(user.locale(), "")

    def test_password_stored_on_device(self):
        """Test a new user's password is written to their password device"""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        self.assertEqual(user.password, PasswordDevice.objects.get(user=user).password)
        self.assertTrue(User.objects.get(pk=user.pk).check_password("initial"))

    def test_password_change_updates_device(self):
        """Test changing a password updates the device instead of adding another one"""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        user.set_password("changed")
        user.save()
        self.assertEqual(PasswordDevice.objects.filter(user=user).count(), 1)
        self.assertTrue(User.objects.get(pk=user.pk).check_password("changed"))

    def test_password_staged_until_save(self):
        """Test a password is only written to the device once the user is saved"""
        user = User.objects.create(username=generate_id())
        user.set_password("staged")
        self.assertFalse(PasswordDevice.objects.filter(user=user).exists())
        user.save()
        self.assertTrue(User.objects.get(pk=user.pk).check_password("staged"))

    def test_password_unusable_without_device(self):
        """Test a user without a password device cannot authenticate with a password"""
        user = User.objects.create(username=generate_id())
        self.assertFalse(PasswordDevice.objects.filter(user=user).exists())
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.check_password("anything"))

    def test_session_auth_hash_follows_password(self):
        """Test changing a password invalidates existing sessions"""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        previous_hash = user.get_session_auth_hash()
        user.set_password("changed")
        user.save()
        self.assertNotEqual(previous_hash, user.get_session_auth_hash())

    def test_set_password_from_hash_signal_skips_source_sync_receivers(self):
        """Test hash password updates do not expose a raw password to sync receivers."""
        user = User.objects.create(
            username=generate_id(),
            attributes={"distinguishedName": "cn=test,ou=users,dc=example,dc=com"},
        )
        password_changed_captured = []
        password_hash_changed_captured = []
        dispatch_uid = generate_id()
        hash_dispatch_uid = generate_id()

        def password_changed_receiver(sender, **kwargs):
            password_changed_captured.append(kwargs)

        def password_hash_changed_receiver(sender, **kwargs):
            password_hash_changed_captured.append(kwargs)

        password_changed.connect(password_changed_receiver, dispatch_uid=dispatch_uid)
        password_hash_changed.connect(
            password_hash_changed_receiver, dispatch_uid=hash_dispatch_uid
        )
        try:
            with (
                patch(
                    "authentik.sources.ldap.signals.LDAPSource.objects.filter"
                ) as ldap_sources_filter,
                patch(
                    "authentik.sources.kerberos.signals."
                    "UserKerberosSourceConnection.objects.select_related"
                ) as kerberos_connections_select,
            ):
                user.set_password_from_hash(make_password("new-password"))  # nosec
                user.save()
        finally:
            password_changed.disconnect(dispatch_uid=dispatch_uid)
            password_hash_changed.disconnect(dispatch_uid=hash_dispatch_uid)

        self.assertEqual(password_changed_captured, [])
        self.assertEqual(len(password_hash_changed_captured), 1)
        ldap_sources_filter.assert_not_called()
        kerberos_connections_select.assert_not_called()


class TestUserSerializerPasswordHash(TestCase):
    """Test UserSerializer password_hash support in blueprint context."""

    def test_password_hash_sets_password_directly(self):
        """Test a valid password hash is stored without re-hashing."""
        password = "test-password-123"  # nosec
        password_hash = make_password(password)
        serializer = UserSerializer(
            data={
                "username": generate_id(),
                "name": "Test User",
                "password_hash": password_hash,
            },
            context={SERIALIZER_CONTEXT_BLUEPRINT: True},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.password, password_hash)
        self.assertTrue(user.check_password(password))
        self.assertIsNotNone(user.password_change_date)

    def test_unrecognized_password_hash_is_stored_unchanged(self):
        """Test blueprint password hashes are stored without validation."""
        password_hash = "custom$password$hash"
        serializer = UserSerializer(
            data={
                "username": generate_id(),
                "name": "Test User",
                "password_hash": password_hash,
            },
            context={SERIALIZER_CONTEXT_BLUEPRINT: True},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.password, password_hash)

    def test_password_hash_ignored_outside_blueprint_context(self):
        """Test password_hash is not accepted by the regular serializer."""
        serializer = UserSerializer(
            data={
                "username": generate_id(),
                "name": "Test User",
                "password_hash": make_password("test"),  # nosec
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("password_hash", serializer.validated_data)
