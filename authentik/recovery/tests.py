"""recovery tests"""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from django_tenants.utils import get_public_schema_name

from authentik.core.models import Token, TokenIntents, User


class TestRecovery(TestCase):
    """recovery tests"""

    def setUp(self):
        self.user: User = User.objects.create_user(username="recovery-test-user")

    def test_create_key(self):
        """Test creation of a new key"""
        out = StringIO()
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 0)
        call_command(
            "create_recovery_key",
            "5",
            self.user.username,
            schema=get_public_schema_name(),
            stdout=out,
        )
        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, out.getvalue())
        self.assertIn("valid for 5 minutes", out.getvalue())
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 1)

    def test_create_key_invalid(self):
        """Test creation of a new key (invalid)"""
        out = StringIO()
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 0)
        call_command("create_recovery_key", "5", "foo", schema=get_public_schema_name(), stderr=out)
        self.assertIn("not found", out.getvalue())

    def test_recovery_view(self):
        """Test recovery view"""
        out = StringIO()
        call_command(
            "create_recovery_key",
            "10",
            self.user.username,
            schema=get_public_schema_name(),
            stdout=out,
        )
        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.client.get(reverse("authentik_recovery:use-token", kwargs={"key": token.key}))
        self.assertEqual(self.client.session["authenticatedsession"].user.pk, token.user.pk)

    def test_recovery_view_invalid(self):
        """Test recovery view with invalid token"""
        response = self.client.get(reverse("authentik_recovery:use-token", kwargs={"key": "abc"}))
        self.assertEqual(response.status_code, 404)

    def test_recovery_admin_group_invalid(self):
        """Test creation of admin group"""
        out = StringIO()
        call_command("create_admin_group", "1", schema=get_public_schema_name(), stderr=out)
        self.assertIn("not found", out.getvalue())

    def test_recovery_admin_group(self):
        """Test creation of admin group"""
        out = StringIO()
        call_command(
            "create_admin_group", self.user.username, schema=get_public_schema_name(), stdout=out
        )
        self.assertIn("successfully added to", out.getvalue())
        self.assertTrue(self.user.is_superuser)

    def test_create_key_default_duration(self):
        """Test creation of a new key with default duration (60 minutes)"""
        out = StringIO()
        before_creation = now()
        call_command(
            "create_recovery_key",
            self.user.username,  # Just the user, duration will use default
            schema=get_public_schema_name(),
            stdout=out,
        )
        after_creation = now()

        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, out.getvalue())
        self.assertIn("valid for 1 hour", out.getvalue())

        # Verify the token expires in approximately 60 minutes (default)
        expected_expiry_min = before_creation + timedelta(minutes=60)
        expected_expiry_max = after_creation + timedelta(minutes=60)
        self.assertGreaterEqual(token.expires, expected_expiry_min)
        self.assertLessEqual(token.expires, expected_expiry_max)

    def test_create_key_custom_duration(self):
        """Test creation of a new key with custom duration"""
        out = StringIO()
        custom_duration = 120  # 2 hours
        before_creation = now()

        call_command(
            "create_recovery_key",
            str(custom_duration),
            self.user.username,
            schema=get_public_schema_name(),
            stdout=out,
        )
        after_creation = now()

        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, out.getvalue())
        self.assertIn("valid for 2 hours", out.getvalue())

        # Verify the token expires in approximately the custom duration
        expected_expiry_min = before_creation + timedelta(minutes=custom_duration)
        expected_expiry_max = after_creation + timedelta(minutes=custom_duration)
        self.assertGreaterEqual(token.expires, expected_expiry_min)
        self.assertLessEqual(token.expires, expected_expiry_max)

    def test_create_key_short_duration(self):
        """Test creation of a new key with very short duration (1 minute)"""
        out = StringIO()
        short_duration = 1
        before_creation = now()

        call_command(
            "create_recovery_key",
            str(short_duration),
            self.user.username,
            schema=get_public_schema_name(),
            stdout=out,
        )
        after_creation = now()

        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, out.getvalue())
        self.assertIn("valid for 1 minute", out.getvalue())

        # Verify the token expires in approximately 1 minute
        expected_expiry_min = before_creation + timedelta(minutes=short_duration)
        expected_expiry_max = after_creation + timedelta(minutes=short_duration)
        self.assertGreaterEqual(token.expires, expected_expiry_min)
        self.assertLessEqual(token.expires, expected_expiry_max)

    def test_create_key_duration_validation(self):
        """Test that the duration is correctly converted to minutes"""
        # Test various durations to ensure they're calculated correctly
        test_cases = [1, 5, 30, 60, 120, 1440]  # 1min, 5min, 30min, 1hr, 2hr, 24hr

        for duration in test_cases:
            with self.subTest(duration=duration):
                out = StringIO()
                before_creation = now()

                call_command(
                    "create_recovery_key",
                    str(duration),
                    self.user.username,
                    schema=get_public_schema_name(),
                    stdout=out,
                )
                after_creation = now()

                token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)

                # Verify the token expires in approximately the specified duration
                expected_expiry_min = before_creation + timedelta(minutes=duration)
                expected_expiry_max = after_creation + timedelta(minutes=duration)
                self.assertGreaterEqual(token.expires, expected_expiry_min)
                self.assertLessEqual(token.expires, expected_expiry_max)

                # Clean up for next iteration
                token.delete()

    def test_create_key_help_text(self):
        """Test that the help text correctly indicates minutes"""
        from authentik.recovery.management.commands.create_recovery_key import Command

        command = Command()
        # Check that the help text mentions minutes
        parser = command.create_parser("test", "create_recovery_key")
        help_text = parser.format_help()
        self.assertIn("minutes", help_text.lower())
        self.assertNotIn("years", help_text.lower())

    def test_format_duration_message(self):
        """Test the format_duration_message method directly"""
        from authentik.recovery.management.commands.create_recovery_key import Command

        command = Command()

        # Test cases for various durations
        test_cases = [
            # Minutes
            (1, "1 minute"),
            (2, "2 minutes"),
            (5, "5 minutes"),
            (30, "30 minutes"),
            (59, "59 minutes"),
            # Hours
            (60, "1 hour"),
            (90, "1 hour and 30 minutes"),
            (120, "2 hours"),
            (150, "2 hours and 30 minutes"),
            (180, "3 hours"),
            (721, "12 hours and 1 minute"),
            (1439, "23 hours and 59 minutes"),
            # Days
            (1440, "1 day"),
            (1500, "1 day and 1 hour"),
            (1501, "1 day, 1 hour and 1 minute"),
            (2880, "2 days"),
            (2940, "2 days and 1 hour"),
            (2941, "2 days, 1 hour and 1 minute"),
            (4320, "3 days"),
            (4380, "3 days and 1 hour"),
            (4441, "3 days, 2 hours and 1 minute"),
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = command.format_duration_message(duration)
                self.assertEqual(
                    result,
                    expected,
                    f"For duration {duration}, expected '{expected}' but got '{result}'",
                )

    def test_create_key_duration_message_formatting(self):
        """Test that various duration formats are displayed correctly in command output"""
        test_cases = [
            (1, "valid for 1 minute"),
            (5, "valid for 5 minutes"),
            (60, "valid for 1 hour"),
            (90, "valid for 1 hour and 30 minutes"),
            (120, "valid for 2 hours"),
            (1440, "valid for 1 day"),
            (1500, "valid for 1 day and 1 hour"),
            (1501, "valid for 1 day, 1 hour and 1 minute"),
        ]

        for duration, expected_message in test_cases:
            with self.subTest(duration=duration):
                out = StringIO()
                call_command(
                    "create_recovery_key",
                    str(duration),
                    self.user.username,
                    schema=get_public_schema_name(),
                    stdout=out,
                )

                output = out.getvalue()
                self.assertIn(expected_message, output)

                # Clean up
                Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY, user=self.user).delete()
