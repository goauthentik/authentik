"""Tests for hash_password management command."""

from io import StringIO
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class TestHashPasswordCommand(TestCase):
    """Test hash_password management command."""

    def call_prompt(self, side_effect, **options):
        """Call the command with an interactive password prompt."""
        with (
            patch(
                "authentik.core.management.commands.hash_password.getpass",
                side_effect=side_effect,
            ),
            patch(
                "authentik.core.management.commands.hash_password.sys.stdin.isatty",
                return_value=True,
            ),
        ):
            call_command("hash_password", **options)

    def test_hash_password(self):
        """Test hashing a password."""
        out = StringIO()
        call_command("hash_password", "test123", stdout=out, stderr=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_prompt(self):
        """Test hashing a password entered through the hidden prompt."""
        out = StringIO()
        self.call_prompt(["test123", "test123"], stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_empty_fails(self):
        """Test that empty password raises error."""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password", "")

        self.assertIn("Password cannot be empty", str(ctx.exception))

    @patch("authentik.core.management.commands.hash_password.sys.stdin.isatty", return_value=False)
    def test_hash_password_prompt_without_tty_fails(self, _isatty_mock):
        """Test that prompting requires an interactive terminal."""
        with self.assertRaises(CommandError) as ctx:
            call_command("hash_password")

        self.assertIn("requires an interactive terminal", str(ctx.exception))

    def test_hash_password_prompt_errors(self):
        """Test errors raised while prompting for a password."""
        for side_effect, message in (
            (["", ""], "Password cannot be empty"),
            (["test123", "different"], "Passwords do not match"),
            (KeyboardInterrupt, "Aborted"),
        ):
            with self.subTest(message=message), self.assertRaises(CommandError) as ctx:
                self.call_prompt(side_effect)
            self.assertIn(message, str(ctx.exception))
