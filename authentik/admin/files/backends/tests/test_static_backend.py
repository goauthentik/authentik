from django.test import TestCase

from authentik.admin.files.backends.static import StaticBackend
from authentik.admin.files.usage import FileUsage


class TestStaticBackend(TestCase):
    """Test Static backend functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.usage = FileUsage.MEDIA
        self.backend = StaticBackend(self.usage)

    def test_init(self):
        """Test StaticBackend initialization"""
        self.assertEqual(self.backend.usage, self.usage)

    def test_allowed_usages(self):
        """Test that StaticBackend only supports MEDIA usage"""
        self.assertEqual(self.backend.allowed_usages, [FileUsage.MEDIA])

    def test_supports_file_path_static_prefix(self):
        """Test supports_file_path returns True for /static prefix"""
        self.assertTrue(self.backend.supports_file("/static/assets/icons/test.svg"))
        self.assertTrue(self.backend.supports_file("/static/authentik/sources/icon.png"))

    def test_supports_file_path_not_static(self):
        """Test supports_file_path returns False for non-static paths"""
        self.assertFalse(self.backend.supports_file("web/dist/assets/icons/test.svg"))
        self.assertFalse(self.backend.supports_file("web/dist/assets/images/logo.png"))
        self.assertFalse(self.backend.supports_file("media/public/test.png"))
        self.assertFalse(self.backend.supports_file("/media/test.svg"))
        self.assertFalse(self.backend.supports_file("test.jpg"))

    def test_list_files(self):
        """Test list_files includes expected files"""
        files = list(self.backend.list_files())

        self.assertIn("/static/dist/assets/icons/icon.svg", files)
        self.assertIn("/static/dist/assets/icons/icon_left_brand.svg", files)
        self.assertIn("/static/dist/assets/images/flow_background.jpg", files)
        self.assertIn("/static/authentik/sources/ldap.png", files)
        self.assertIn("/static/authentik/sources/openidconnect.svg", files)
        self.assertIn("/static/authentik/sources/saml.png", files)
