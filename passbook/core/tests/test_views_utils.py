"""passbook util view tests"""

from django.test import RequestFactory, TestCase

from passbook.core.views.utils import LoadingView, PermissionDeniedView


class TestUtilViews(TestCase):
    """Test Utility Views"""

    def setUp(self):
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
        response = PermissionDeniedView.as_view()(request)
        self.assertEqual(response.status_code, 200)
