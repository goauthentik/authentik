"""Tests for hash_password management command."""

from io import StringIO
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class TestHashPasswordCommand(TestCase):
    """Test hash_password management command."""

    def test_hash_password_stdin(self):
        """Test hashing a password read from standard input."""
        out = StringIO()
        with patch(
            "authentik.core.management.commands.hash_password.sys.stdin",
            StringIO("test123\n"),
        ):
            call_command("hash_password", stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_prompt(self):
        """Test hashing a password entered through the hidden prompt."""
        out = StringIO()
        with (
            patch(
                "authentik.core.management.commands.hash_password.getpass",
                side_effect=["test123", "test123"],
            ),
            patch(
                "authentik.core.management.commands.hash_password.sys.stdin.isatty",
                return_value=True,
            ),
        ):
            call_command("hash_password", stdout=out)
        hashed = out.getvalue().strip()

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(check_password("test123", hashed))

    def test_hash_password_empty_stdin_fails(self):
        """Test that an empty password read from standard input raises an error."""
        with (
            patch(
                "authentik.core.management.commands.hash_password.sys.stdin",
                StringIO("\n"),
            ),
            self.assertRaises(CommandError) as ctx,
        ):
            call_command("hash_password")

        self.assertIn("Password cannot be empty", str(ctx.exception))

    def test_hash_password_empty_prompt_fails(self):
        """Test that an empty prompted password raises an error."""
        with (
            patch(
                "authentik.core.management.commands.hash_password.getpass",
                side_effect=["", ""],
            ),
            patch(
                "authentik.core.management.commands.hash_password.sys.stdin.isatty",
                return_value=True,
            ),
            self.assertRaises(CommandError) as ctx,
        ):
            call_command("hash_password")

        self.assertIn("Password cannot be empty", str(ctx.exception))

    def test_hash_password_mismatched_prompt_fails(self):
        """Test that mismatched prompted passwords raise an error."""
        with (
            patch(
                "authentik.core.management.commands.hash_password.getpass",
                side_effect=["test123", "different"],
            ),
            patch(
                "authentik.core.management.commands.hash_password.sys.stdin.isatty",
                return_value=True,
            ),
            self.assertRaises(CommandError) as ctx,
        ):
            call_command("hash_password")

        self.assertIn("Passwords do not match", str(ctx.exception))
