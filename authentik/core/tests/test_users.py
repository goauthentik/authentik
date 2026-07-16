"""user tests"""

from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.test.testcases import TestCase
from rest_framework.exceptions import ValidationError

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.core.signals import password_changed, password_hash_changed
from authentik.events.models import Event
from authentik.lib.generators import generate_id

# Recognized algorithm prefix, but the $-separated fields were eaten by an env var
# interpolating the hash. Only decoding the body catches this.
CORRUPT_PASSWORD_HASH = "pbkdf2_sha256$1000000/K4wGpWYKfJPSCcNM="


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

    def test_set_password_from_hash_rejects_corrupt_hash(self):
        """Test a hash with a recognized prefix but a corrupt body is rejected."""
        user = User.objects.create(username=generate_id())
        original = make_password("original-password")  # nosec
        user.set_password_from_hash(original)
        user.save()

        with self.assertRaises(ValueError):
            user.set_password_from_hash(CORRUPT_PASSWORD_HASH)

        user.refresh_from_db()
        self.assertEqual(user.password, original)
        self.assertTrue(user.check_password("original-password"))

    def test_validate_password_hash_rejects_malformed_bodies(self):
        """Test hashes are validated past their algorithm prefix."""
        for password_hash in (
            CORRUPT_PASSWORD_HASH,
            "pbkdf2_sha256$whatever",
            "pbkdf2_sha256$not-a-number$salt$hash",
            "argon2$garbage",
            "scrypt$1$2",
        ):
            with self.subTest(password_hash=password_hash), self.assertRaises(ValueError):
                User.validate_password_hash(password_hash)

    def test_validate_password_hash_accepts_valid_hash(self):
        """Test a well-formed hash still validates."""
        User.validate_password_hash(make_password(generate_id()))


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

    def test_password_hash_rejects_invalid_format(self):
        """Test invalid password hash values are rejected."""
        serializer = UserSerializer(
            data={
                "username": generate_id(),
                "name": "Test User",
                "password_hash": "not-a-valid-hash",
            },
            context={SERIALIZER_CONTEXT_BLUEPRINT: True},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(ValidationError) as ctx:
            serializer.save()

        self.assertIn("Invalid password hash format", str(ctx.exception))

    def test_password_hash_rejects_corrupt_body(self):
        """Test a hash with a recognized prefix but a corrupt body is rejected."""
        serializer = UserSerializer(
            data={
                "username": generate_id(),
                "name": "Test User",
                "password_hash": CORRUPT_PASSWORD_HASH,
            },
            context={SERIALIZER_CONTEXT_BLUEPRINT: True},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(ValidationError) as ctx:
            serializer.save()

        self.assertIn("Invalid password hash format", str(ctx.exception))

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
