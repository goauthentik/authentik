"""recovery tests"""
from io import StringIO

from django.core.management import call_command
from django.shortcuts import reverse
from django.test import TestCase

from passbook.core.models import Token, User
from passbook.lib.config import CONFIG


class TestRecovery(TestCase):
    """recovery tests"""

    def setUp(self):
        self.user = User.objects.create_user(username="recovery-test-user")

    def test_create_key(self):
        """Test creation of a new key"""
        CONFIG.update_from_dict({"domain": "testserver"})
        out = StringIO()
        self.assertEqual(len(Token.objects.all()), 0)
        call_command("create_recovery_key", "1", self.user.username, stdout=out)
        self.assertIn("https://testserver/recovery/use-token/", out.getvalue())
        self.assertEqual(len(Token.objects.all()), 1)

    def test_recovery_view(self):
        """Test recovery view"""
        out = StringIO()
        call_command("create_recovery_key", "1", self.user.username, stdout=out)
        token = Token.objects.first()
        self.client.get(
            reverse("passbook_recovery:use-token", kwargs={"uuid": str(token.uuid)})
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), token.user.pk)
