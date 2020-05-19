"""admin tests"""
from typing import Callable

from django.shortcuts import reverse
from django.test import Client, TestCase
from django.urls.exceptions import NoReverseMatch

from passbook.admin.urls import urlpatterns
from passbook.core.models import User


class TestAdmin(TestCase):
    """Generic admin tests"""

    def setUp(self):
        self.user = User.objects.create_superuser(username="test")
        self.client = Client()
        self.client.force_login(self.user)


def generic_view_tester(view_name: str) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestAdmin):
        try:
            full_url = reverse(f"passbook_admin:{view_name}")
            response = self.client.get(full_url)
            self.assertTrue(response.status_code < 500)
        except NoReverseMatch:
            pass

    return tester


for url in urlpatterns:
    method_name = url.name.replace("-", "_")
    setattr(TestAdmin, f"test_{method_name}", generic_view_tester(url.name))
