"""authentik user view tests"""
import string
from random import SystemRandom

from django.test import TestCase
from django.urls import reverse

from authentik.core.models import User


class TestOverviewViews(TestCase):
    """Test Overview Views"""

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

    def test_shell(self):
        """Test shell"""
        self.assertEqual(
            self.client.get(reverse("authentik_core:if-admin")).status_code, 200
        )
