"""Tests for hash_password management command"""

from io import StringIO

from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


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
