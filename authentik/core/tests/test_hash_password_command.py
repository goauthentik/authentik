"""Tests for hash_password management command."""

from io import StringIO

from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class TestHashPasswordCommand(TestCase):
    """Test hash_password management command."""

    def test_hash_password(self):
        """Test hashing a password."""
        out = StringIO()
        call_command("hash_password", "test123", stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_empty_fails(self):
        """Test that empty password raises error."""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password", "")

        self.assertIn("Password cannot be empty", str(ctx.exception))
