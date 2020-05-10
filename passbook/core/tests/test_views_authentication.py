"""passbook Core Account Test"""
import string
from random import SystemRandom

from django.test import TestCase
from django.urls import reverse

from passbook.core.models import User


class TestAuthenticationViews(TestCase):
    """passbook Core Account Test"""

    def setUp(self):
        super().setUp()
        self.sign_up_data = {
            "name": "Test",
            "username": "beryjuorg",
            "email": "unittest@passbook.beryju.org",
            "password": "B3ryju0rg!",
            "password_repeat": "B3ryju0rg!",
        }
        self.login_data = {
            "uid_field": "unittest@example.com",
        }
        self.user = User.objects.create_superuser(
            username="unittest user",
            email="unittest@example.com",
            password="".join(
                SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(8)
            ),
        )

    def test_logout_view(self):
        """Test account.logout view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("passbook_core:auth-logout"))
        self.assertEqual(response.status_code, 302)

    def test_sign_up_view_auth(self):
        """Test account.sign_up view (Authenticated)"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("passbook_core:auth-logout"))
        self.assertEqual(response.status_code, 302)
