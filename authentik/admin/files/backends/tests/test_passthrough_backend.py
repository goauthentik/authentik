"""Test passthrough backend"""

from django.test import TestCase

from authentik.admin.files.backends.passthrough import PassthroughBackend
from authentik.admin.files.usage import FileUsage


class TestPassthroughBackend(TestCase):
    """Test PassthroughBackend class"""

    def setUp(self):
        """Set up test fixtures"""
        self.backend = PassthroughBackend(FileUsage.MEDIA)

    def test_allowed_usages(self):
        """Test that PassthroughBackend only supports MEDIA usage"""
        self.assertEqual(self.backend.allowed_usages, [FileUsage.MEDIA])

    def test_supports_file_path_font_awesome(self):
        """Test supports_file_path returns True for Font Awesome icons"""
        self.assertTrue(self.backend.supports_file("fa://user"))
        self.assertTrue(self.backend.supports_file("fa://home"))
        self.assertTrue(self.backend.supports_file("fa://shield"))

    def test_supports_file_path_http(self):
        """Test supports_file_path returns True for HTTP URLs"""
        self.assertTrue(self.backend.supports_file("http://example.com/icon.png"))
        self.assertTrue(self.backend.supports_file("http://cdn.example.com/logo.svg"))

    def test_supports_file_path_https(self):
        """Test supports_file_path returns True for HTTPS URLs"""
        self.assertTrue(self.backend.supports_file("https://example.com/icon.png"))
        self.assertTrue(self.backend.supports_file("https://cdn.example.com/logo.svg"))

    def test_supports_file_path_false(self):
        """Test supports_file_path returns False for regular paths"""
        self.assertFalse(self.backend.supports_file("icon.png"))
        self.assertFalse(self.backend.supports_file("/static/icon.png"))
        self.assertFalse(self.backend.supports_file("media/logo.svg"))
        self.assertFalse(self.backend.supports_file(""))

    def test_supports_file_path_invalid_scheme(self):
        """Test supports_file_path returns False for invalid schemes"""
        self.assertFalse(self.backend.supports_file("ftp://example.com/file.png"))
        self.assertFalse(self.backend.supports_file("file:///path/to/file.png"))
        self.assertFalse(self.backend.supports_file("data:image/png;base64,abc123"))

    def test_list_files(self):
        """Test list_files returns empty generator"""
        files = list(self.backend.list_files())
        self.assertEqual(files, [])

    def test_file_url(self):
        """Test file_url returns the URL as-is"""
        url = "https://example.com/icon.png"
        self.assertEqual(self.backend.file_url(url), url)

    def test_file_url_font_awesome(self):
        """Test file_url returns Font Awesome URL as-is"""
        url = "fa://user"
        self.assertEqual(self.backend.file_url(url), url)

    def test_file_url_http(self):
        """Test file_url returns HTTP URL as-is"""
        url = "http://cdn.example.com/logo.svg"
        self.assertEqual(self.backend.file_url(url), url)
