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
        """Test list_files lists built-in source icons with a variant per theme"""
        files = list(self.backend.list_files())

        self.assertIn("/static/authentik/sources/github/%(theme)s.svg", files)
        self.assertIn("/static/authentik/sources/kerberos/%(theme)s.png", files)
        self.assertNotIn("/static/authentik/sources/github/light.svg", files)
        self.assertNotIn("/static/authentik/sources/github/dark.svg", files)

    def test_themed_urls_source_icon(self):
        """Test themed_urls of a built-in source icon picked in the file picker"""
        self.assertEqual(
            self.backend.themed_urls("/static/authentik/sources/github/%(theme)s.svg"),
            {
                "light": "/static/authentik/sources/github/light.svg",
                "dark": "/static/authentik/sources/github/dark.svg",
            },
        )

    def test_themed_urls_source_icon_variant(self):
        """Test themed_urls of one variant of a built-in source icon, as used by defaults"""
        github = {
            "light": "/static/authentik/sources/github/light.svg",
            "dark": "/static/authentik/sources/github/dark.svg",
        }
        self.assertEqual(
            self.backend.themed_urls("/static/authentik/sources/github/light.svg"), github
        )
        self.assertEqual(
            self.backend.themed_urls("/static/authentik/sources/github/dark.svg"), github
        )

    def test_themed_urls_other_static_files(self):
        """Test themed_urls returns None for other static files"""
        self.assertIsNone(self.backend.themed_urls("/static/dist/assets/icons/icon.svg"))
        self.assertIsNone(self.backend.themed_urls("/static/dist/assets/icons/light.svg"))
        self.assertIsNone(self.backend.themed_urls("/static/authentik/sources/github/logo.svg"))
        self.assertIsNone(
            self.backend.themed_urls("/static/authentik/sources/github/../github/light.svg")
        )
