"""authentik user view tests"""
import string
from random import SystemRandom

from django.shortcuts import reverse
from django.test import TestCase

from authentik.core.models import User


class TestUserViews(TestCase):
    """Test User Views"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="unittest user",
            email="unittest@example.com",
            password="".join(
                SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(8)
            ),
        )
        self.client.force_login(self.user)

    def test_user_settings(self):
        """Test UserSettingsView"""
        self.assertEqual(
            self.client.get(reverse("authentik_core:user-settings")).status_code, 200
        )

    def test_user_details(self):
        """Test UserDetailsView"""
        self.assertEqual(
            self.client.get(reverse("authentik_core:user-details")).status_code, 200
        )
