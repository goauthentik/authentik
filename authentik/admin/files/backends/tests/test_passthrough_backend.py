"""Test passthrough backend"""

from django.test import TestCase

from authentik.admin.files.backends.passthrough import PassthroughBackend
from authentik.admin.files.usage import Usage


class TestPassthroughBackend(TestCase):
    """Test PassthroughBackend class"""

    def setUp(self):
        """Set up test fixtures"""
        self.backend = PassthroughBackend(Usage.MEDIA)

    def test_allowed_usages(self):
        """Test that PassthroughBackend only supports MEDIA usage"""
        self.assertEqual(PassthroughBackend.allowed_usages, [Usage.MEDIA])

    def test_manageable(self):
        """Test that PassthroughBackend is not manageable"""
        self.assertFalse(PassthroughBackend.manageable)

    def test_supports_file_path_font_awesome(self):
        """Test supports_file_path returns True for Font Awesome icons"""
        self.assertTrue(self.backend.supports_file_path("fa://user"))
        self.assertTrue(self.backend.supports_file_path("fa://home"))
        self.assertTrue(self.backend.supports_file_path("fa://shield"))

    def test_supports_file_path_http(self):
        """Test supports_file_path returns True for HTTP URLs"""
        self.assertTrue(self.backend.supports_file_path("http://example.com/icon.png"))
        self.assertTrue(self.backend.supports_file_path("http://cdn.example.com/logo.svg"))

    def test_supports_file_path_https(self):
        """Test supports_file_path returns True for HTTPS URLs"""
        self.assertTrue(self.backend.supports_file_path("https://example.com/icon.png"))
        self.assertTrue(self.backend.supports_file_path("https://cdn.example.com/logo.svg"))

    def test_supports_file_path_false(self):
        """Test supports_file_path returns False for regular paths"""
        self.assertFalse(self.backend.supports_file_path("icon.png"))
        self.assertFalse(self.backend.supports_file_path("/static/icon.png"))
        self.assertFalse(self.backend.supports_file_path("media/logo.svg"))
        self.assertFalse(self.backend.supports_file_path(""))

    def test_supports_file_path_invalid_scheme(self):
        """Test supports_file_path returns False for invalid schemes"""
        self.assertFalse(self.backend.supports_file_path("ftp://example.com/file.png"))
        self.assertFalse(self.backend.supports_file_path("file:///path/to/file.png"))
        self.assertFalse(self.backend.supports_file_path("data:image/png;base64,abc123"))

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

    def test_file_size(self):
        """Test file_size always returns 0"""
        self.assertEqual(self.backend.file_size("https://example.com/icon.png"), 0)
        self.assertEqual(self.backend.file_size("fa://user"), 0)
        self.assertEqual(self.backend.file_size("http://example.com/file.png"), 0)

    def test_file_exists_true(self):
        """Test file_exists returns True for supported URLs"""
        self.assertTrue(self.backend.file_exists("https://example.com/icon.png"))
        self.assertTrue(self.backend.file_exists("http://example.com/logo.svg"))
        self.assertTrue(self.backend.file_exists("fa://user"))

    def test_file_exists_false(self):
        """Test file_exists returns False for non-supported paths"""
        self.assertFalse(self.backend.file_exists("icon.png"))
        self.assertFalse(self.backend.file_exists("/static/icon.png"))
        self.assertFalse(self.backend.file_exists(""))

    def test_save_file_raises_not_implemented(self):
        """Test save_file raises NotImplementedError"""
        with self.assertRaises(NotImplementedError) as context:
            self.backend.save_file("test.png", b"content")
        self.assertIn("Cannot save files to passthrough backend", str(context.exception))

    def test_save_file_stream_raises_not_implemented(self):
        """Test save_file_stream raises NotImplementedError"""
        with self.assertRaises(NotImplementedError) as context:
            with self.backend.save_file_stream("test.png"):
                pass
        self.assertIn("Cannot save files to passthrough backend", str(context.exception))

    def test_delete_file_raises_not_implemented(self):
        """Test delete_file raises NotImplementedError"""
        with self.assertRaises(NotImplementedError) as context:
            self.backend.delete_file("test.png")
        self.assertIn("Cannot delete files from passthrough backend", str(context.exception))

    def test_backend_not_initialized_with_backend_type(self):
        """Test that PassthroughBackend doesn't set _backend_type since it's not manageable"""
        backend = PassthroughBackend(Usage.MEDIA)
        self.assertIsNone(backend._backend_type)
