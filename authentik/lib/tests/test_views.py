"""Test HTTP Helpers"""

from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.views import bad_request_message


class TestViews(TestCase):
    """Test Views Helpers"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.factory = RequestFactory()

    def test_bad_request_message(self):
        """test bad_request_message"""
        request = self.factory.get("/")
        self.assertEqual(bad_request_message(request, "foo").status_code, 400)
