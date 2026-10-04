"""user tests"""

from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.contrib.auth.hashers import PBKDF2PasswordHasher, make_password
from django.db import IntegrityError, transaction
from django.http import HttpRequest
from django.test.testcases import TestCase
from django.utils.timezone import now

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

    def test_password_change_updates_device(self):
        """Test changing a password updates the user's single password device"""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        user.set_password("changed")
        user.save()
        self.assertEqual(PasswordDevice.objects.filter(user=user).count(), 1)
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user.check_password("changed"))
        self.assertFalse(user.check_password("initial"))

    def test_second_password_device_rejected(self):
        """Test the database only allows one password device per user"""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        with self.assertRaises(IntegrityError), transaction.atomic():
            PasswordDevice.objects.create(user=user, name="Password", password="second")

    def test_password_staged_until_save(self):
        """Test a password is only written to the device once the user is saved"""
        user = User.objects.create(username=generate_id())
        user.set_password("staged")
        self.assertFalse(PasswordDevice.objects.filter(user=user).exists())
        user.save()
        self.assertTrue(User.objects.get(pk=user.pk).check_password("staged"))

    def test_existing_password_staged_until_save(self):
        """Changing a loaded user leaves the stored password alone until save()."""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        user.set_password("changed")
        self.assertTrue(User.objects.get(pk=user.pk).check_password("initial"))
        user.save()
        self.assertTrue(User.objects.get(pk=user.pk).check_password("changed"))

    def test_password_save_failure_rolls_back_user(self):
        """User and password changes commit together."""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        user.name = "Changed name"
        user.set_password("changed")
        with (
            patch.object(PasswordDevice, "save", side_effect=IntegrityError),
            self.assertRaises(IntegrityError),
        ):
            user.save()
        stored = User.objects.get(pk=user.pk)
        self.assertNotEqual(stored.name, user.name)
        self.assertTrue(stored.check_password("initial"))

    def test_user_save_does_not_write_cached_password(self):
        """Saving a name must not overwrite a concurrent password change."""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        password = make_password(generate_id())
        PasswordDevice.objects.filter(user=user).update(password=password)
        user.name = "Changed name"
        user.save()
        self.assertEqual(PasswordDevice.objects.get(user=user).password, password)

    def test_password_unusable_without_device(self):
        """Test a user without a password device cannot authenticate with a password"""
        user = User.objects.create(username=generate_id())
        self.assertFalse(PasswordDevice.objects.filter(user=user).exists())
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.check_password("anything"))

    def test_password_partial_save(self):
        """Partial user updates leave a staged password pending until explicitly saved."""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        user.set_password("changed")
        user.name = "Changed name"
        user.save(update_fields=["name"])
        self.assertTrue(User.objects.get(pk=user.pk).check_password("initial"))
        user.save(update_fields=["password"])
        self.assertTrue(User.objects.get(pk=user.pk).check_password("changed"))

    def test_check_staged_password_does_not_save(self):
        """Checking an imported, outdated hash must not persist an unsaved password."""
        user = User.objects.create(username=generate_id())
        user.password = PBKDF2PasswordHasher().encode("staged", "salt", iterations=1)
        self.assertTrue(user.check_password("staged"))
        self.assertFalse(PasswordDevice.objects.filter(user=user).exists())

    def test_refresh_discards_staged_password(self):
        """Refreshing a user discards an unsaved password along with other changes."""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        user.set_password("changed")
        user.refresh_from_db()
        self.assertTrue(user.check_password("initial"))
        user.save()
        self.assertTrue(User.objects.get(pk=user.pk).check_password("initial"))

    def test_first_password_from_two_loaded_users(self):
        """A missing device cached by another writer must not cause a duplicate insert."""
        user = User.objects.create(username=generate_id())
        other = User.objects.get(pk=user.pk)
        self.assertFalse(other.has_usable_password())
        user.set_password("first")
        user.save()
        other.set_password("second")
        other.save()
        self.assertTrue(User.objects.get(pk=user.pk).check_password("second"))

    def test_session_auth_hash_follows_password(self):
        """Test changing a password invalidates existing sessions"""
        user = User.objects.create_user(username=generate_id(), password="initial")  # nosec
        previous_hash = user.get_session_auth_hash()
        user.set_password("changed")
        user.save()
        self.assertNotEqual(previous_hash, user.get_session_auth_hash())

    def test_hash_upgrade_preserves_password_metadata(self):
        """Rehashing a cached device must not overwrite newer password metadata."""
        password = generate_id()
        old_hash = PBKDF2PasswordHasher().encode(password, "salt", iterations=1)
        user = User.objects.create(username=generate_id(), password=old_hash)
        changed_at = now()
        PasswordDevice.objects.filter(user=user).update(password_change_date=changed_at)

        with patch.object(password_changed, "send") as signal:
            self.assertTrue(user.check_password(password))
        signal.assert_not_called()
        user.name = "Changed name"
        user.save()

        device = PasswordDevice.objects.get(user=user)
        self.assertNotEqual(device.password, old_hash)
        self.assertEqual(device.password_change_date, changed_at)

    def test_hash_upgrade_preserves_concurrent_password_change(self):
        """An outdated cached hash cannot overwrite a newly reset password."""
        old_hash = PBKDF2PasswordHasher().encode("initial", "salt", iterations=1)
        user = User.objects.create(username=generate_id(), password=old_hash)
        changed_hash = make_password("changed")
        PasswordDevice.objects.filter(user=user).update(password=changed_hash)

        self.assertTrue(user.check_password("initial"))

        self.assertEqual(PasswordDevice.objects.get(user=user).password, changed_hash)

    def test_async_password_check_upgrades_hash(self):
        """Django's async password API can load and rehash a password device."""
        old_hash = PBKDF2PasswordHasher().encode("initial", "salt", iterations=1)
        user = User.objects.create(username=generate_id(), password=old_hash)
        user = User.objects.get(pk=user.pk)
        changed_at = user.password_change_date
        user = User.objects.get(pk=user.pk)

        with patch.object(password_changed, "send") as signal:
            self.assertTrue(async_to_sync(user.acheck_password)("initial"))

        signal.assert_not_called()
        device = PasswordDevice.objects.get(user=user)
        self.assertNotEqual(device.password, old_hash)
        self.assertEqual(device.password_change_date, changed_at)

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
