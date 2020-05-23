"""passbook util view tests"""
import string
from random import SystemRandom

from django.test import RequestFactory, TestCase

from passbook.core.models import User
from passbook.core.views.utils import PermissionDeniedView


class TestUtilViews(TestCase):
    """Test Utility Views"""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="unittest user",
            email="unittest@example.com",
            password="".join(
                SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(8)
            ),
        )
        self.factory = RequestFactory()

    def test_permission_denied_view(self):
        """Test PermissionDeniedView"""
        request = self.factory.get("something")
        request.user = self.user
        response = PermissionDeniedView.as_view()(request)
        self.assertEqual(response.status_code, 200)
