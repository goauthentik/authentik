"""recovery tests"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
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
            "1",
            self.user.username,
            schema=get_public_schema_name(),
            stdout=out,
        )
        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, out.getvalue())
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 1)

    def test_create_key_invalid(self):
        """Test creation of a new key (invalid)"""
        out = StringIO()
        self.assertEqual(len(Token.objects.filter(intent=TokenIntents.INTENT_RECOVERY)), 0)
        call_command("create_recovery_key", "1", "foo", schema=get_public_schema_name(), stderr=out)
        self.assertIn("not found", out.getvalue())

    def test_recovery_view(self):
        """Test recovery view"""
        out = StringIO()
        call_command(
            "create_recovery_key",
            "1",
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
