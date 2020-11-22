"""passbook user view tests"""
import string
from random import SystemRandom

from django.shortcuts import reverse
from django.test import TestCase

from passbook.core.models import User


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
            self.client.get(reverse("passbook_core:shell")).status_code, 200
        )

    def test_overview(self):
        """Test overview"""
        self.assertEqual(
            self.client.get(reverse("passbook_core:overview")).status_code, 200
        )

    def test_user_settings(self):
        """Test user settings"""
        self.assertEqual(
            self.client.get(reverse("passbook_core:user-settings")).status_code, 200
        )
