"""Tests for hash_password management command and password_hash serializer functionality"""

from io import StringIO

from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.users import UserSerializer
from authentik.core.models import User
from authentik.lib.generators import generate_id


class TestHashPasswordCommand(TestCase):
    """Test hash_password management command"""

    def test_hash_password_basic(self):
        """Test basic password hashing"""
        out = StringIO()
        call_command("hash_password", "test123", stdout=out)
        hashed = out.getvalue().strip()

        # Verify it's a valid hash
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        # Verify the hash can be validated
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_special_chars(self):
        """Test hashing password with special characters"""
        out = StringIO()
        password = "P@ssw0rd!#$%^&*(){}[]"  # nosec
        call_command("hash_password", password, stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password(password, hashed))

    def test_hash_password_unicode(self):
        """Test hashing password with unicode characters"""
        out = StringIO()
        password = "пароль123"  # nosec
        call_command("hash_password", password, stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password(password, hashed))

    def test_hash_password_long(self):
        """Test hashing a very long password"""
        out = StringIO()
        password = "a" * 1000
        call_command("hash_password", password, stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password(password, hashed))

    def test_hash_password_spaces(self):
        """Test hashing password with spaces"""
        out = StringIO()
        password = "my super secret password"  # nosec
        call_command("hash_password", password, stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password(password, hashed))

    def test_hash_password_empty_fails(self):
        """Test that empty password raises error"""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password", "")
        self.assertIn("Password cannot be empty", str(ctx.exception))

    def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        out1 = StringIO()
        out2 = StringIO()

        call_command("hash_password", "password1", stdout=out1)
        call_command("hash_password", "password2", stdout=out2)

        hash1 = out1.getvalue().strip()
        hash2 = out2.getvalue().strip()

        self.assertNotEqual(hash1, hash2)
        self.assertTrue(check_password("password1", hash1))
        self.assertTrue(check_password("password2", hash2))
        self.assertFalse(check_password("password1", hash2))
        self.assertFalse(check_password("password2", hash1))

    def test_hash_same_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)"""
        out1 = StringIO()
        out2 = StringIO()

        call_command("hash_password", "samepassword", stdout=out1)
        call_command("hash_password", "samepassword", stdout=out2)

        hash1 = out1.getvalue().strip()
        hash2 = out2.getvalue().strip()

        # Hashes should be different due to random salt
        self.assertNotEqual(hash1, hash2)
        # But both should validate the same password
        self.assertTrue(check_password("samepassword", hash1))
        self.assertTrue(check_password("samepassword", hash2))


class TestUserSerializerPasswordHash(TestCase):
    """Test UserSerializer password_hash functionality in blueprint context"""

    def test_password_hash_sets_password_correctly(self):
        """Test that a valid password_hash sets the password directly without re-hashing"""
        password = "test-password-123"  # nosec
        password_hash = make_password(password)

        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": password_hash,
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # Verify password was set correctly
        self.assertTrue(user.check_password(password))
        # Verify the hash was set directly (not re-hashed)
        self.assertEqual(user.password, password_hash)

    def test_password_hash_invalid_format_raises_error(self):
        """Test that an invalid password_hash raises ValidationError"""
        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": "not-a-valid-hash",
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(ValidationError) as ctx:
            serializer.save()

        self.assertIn("Invalid password hash format", str(ctx.exception))

    def test_password_hash_takes_precedence_over_password(self):
        """Test that password_hash takes precedence over password when both are provided"""
        plaintext_password = "plaintext-password"  # nosec
        hash_password = "hash-password"  # nosec
        password_hash = make_password(hash_password)

        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password": plaintext_password,
            "password_hash": password_hash,
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # Verify the hash password is used, not the plaintext
        self.assertTrue(user.check_password(hash_password))
        self.assertFalse(user.check_password(plaintext_password))

    def test_password_change_date_updated_with_password_hash(self):
        """Test that password_change_date is updated when using password_hash"""
        password_hash = make_password("test-password")  # nosec

        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": password_hash,
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # Verify password_change_date is set
        self.assertIsNotNone(user.password_change_date)

    def test_password_hash_update_existing_user(self):
        """Test that password_hash works when updating an existing user"""
        # Create user first
        user = User.objects.create(username=generate_id(), name="Test User")
        user.set_password("old-password")  # nosec
        user.save()

        new_password = "new-password-123"  # nosec
        password_hash = make_password(new_password)

        data = {
            "password_hash": password_hash,
        }

        serializer = UserSerializer(
            instance=user,
            data=data,
            context={SERIALIZER_CONTEXT_BLUEPRINT: True},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()

        # Verify password was updated
        self.assertTrue(updated_user.check_password(new_password))
        self.assertFalse(updated_user.check_password("old-password"))

    def test_password_hash_whitespace_only_rejected(self):
        """Test that whitespace-only password_hash is rejected by serializer validation"""
        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": "   ",  # whitespace only
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        # Serializer should reject blank values
        self.assertFalse(serializer.is_valid())
        self.assertIn("password_hash", serializer.errors)

    def test_password_hash_empty_string_rejected(self):
        """Test that empty string password_hash is rejected by serializer validation"""
        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": "",
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        # Serializer should reject blank values
        self.assertFalse(serializer.is_valid())
        self.assertIn("password_hash", serializer.errors)

    def test_password_hash_null_creates_unusable_password(self):
        """Test that null password_hash results in unusable password"""
        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": None,
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # User should have an unusable password since no valid password was provided
        self.assertFalse(user.has_usable_password())

    def test_password_hash_not_available_outside_blueprint_context(self):
        """Test that password_hash field is not available outside blueprint context"""
        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": make_password("test"),  # nosec
        }

        # Without blueprint context
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # password_hash should not be in validated_data
        self.assertNotIn("password_hash", serializer.validated_data)

    def test_password_hash_identifies_various_hashers(self):
        """Test that valid Django password hashes are accepted"""
        password = "test-password"  # nosec
        password_hash = make_password(password)

        # Verify the hash is a valid Django hash format
        hasher = identify_hasher(password_hash)
        self.assertIsNotNone(hasher)

        username = generate_id()
        data = {
            "username": username,
            "name": "Test User",
            "password_hash": password_hash,
        }

        serializer = UserSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(user.check_password(password))
