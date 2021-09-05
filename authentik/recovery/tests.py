"""recovery tests"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from authentik.core.models import Token, TokenIntents, User


class TestRecovery(TestCase):
    """recovery tests"""

    def setUp(self):
        self.user = User.objects.create_user(username="recovery-test-user")

    def test_create_key(self):
        """Test creation of a new key"""
        out = StringIO()
        self.assertEqual(len(Token.objects.all()), 0)
        call_command("create_recovery_key", "1", self.user.username, stdout=out)
        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.assertIn(token.key, out.getvalue())
        self.assertEqual(len(Token.objects.all()), 1)

    def test_recovery_view(self):
        """Test recovery view"""
        out = StringIO()
        call_command("create_recovery_key", "1", self.user.username, stdout=out)
        token = Token.objects.get(intent=TokenIntents.INTENT_RECOVERY, user=self.user)
        self.client.get(reverse("authentik_recovery:use-token", kwargs={"key": token.key}))
        self.assertEqual(int(self.client.session["_auth_user_id"]), token.user.pk)

    def test_recovery_view_invalid(self):
        """Test recovery view with invalid token"""
        response = self.client.get(reverse("authentik_recovery:use-token", kwargs={"key": "abc"}))
        self.assertEqual(response.status_code, 404)
