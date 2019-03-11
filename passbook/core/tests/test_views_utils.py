"""passbook util view tests"""
import string
from random import SystemRandom

from django.test import RequestFactory, TestCase

from passbook.core.models import User
from passbook.core.views.utils import LoadingView, PermissionDeniedView


class TestUtilViews(TestCase):
    """Test Utility Views"""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='unittest user',
            email='unittest@example.com',
            password=''.join(SystemRandom().choice(
                string.ascii_uppercase + string.digits) for _ in range(8)))
        self.factory = RequestFactory()

    def test_loading_view(self):
        """Test loading view"""
        request = self.factory.get('something')
        response = LoadingView.as_view(target_url='somestring')(request)
        response.render()
        self.assertIn('somestring', response.content.decode('utf-8'))

    def test_permission_denied_view(self):
        """Test PermissionDeniedView"""
        request = self.factory.get('something')
        request.user = self.user
        response = PermissionDeniedView.as_view()(request)
        self.assertEqual(response.status_code, 200)
