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

    def test_hash_password_stdin(self):
        """Test hashing a password read from stdin."""
        out = StringIO()
        call_command("hash_password", "--stdin", stdin_stream=StringIO("test123\n"), stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_stdin_without_trailing_newline(self):
        """Test that a password piped without a trailing newline is read intact."""
        out = StringIO()
        call_command("hash_password", "--stdin", stdin_stream=StringIO("test123"), stdout=out)

        self.assertTrue(check_password("test123", out.getvalue().strip()))

    def test_hash_password_stdin_preserves_inner_whitespace(self):
        """Test that only the trailing newline is stripped from stdin."""
        out = StringIO()
        call_command("hash_password", "--stdin", stdin_stream=StringIO(" pass word \n"), stdout=out)

        self.assertTrue(check_password(" pass word ", out.getvalue().strip()))

    def test_hash_password_stdin_empty_fails(self):
        """Test that an empty stdin raises error."""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password", "--stdin", stdin_stream=StringIO("\n"))

        self.assertIn("Password cannot be empty", str(ctx.exception))

    def test_hash_password_stdin_with_argument_fails(self):
        """Test that --stdin and a password argument are mutually exclusive."""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password", "test123", "--stdin", stdin_stream=StringIO("test123\n"))

        self.assertIn("Cannot use both --stdin and a password argument", str(ctx.exception))

    def test_hash_password_no_password_without_tty_fails(self):
        """Test that omitting the password without a TTY raises an actionable error."""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password", stdin_stream=StringIO(""))

        self.assertIn("No password given", str(ctx.exception))
