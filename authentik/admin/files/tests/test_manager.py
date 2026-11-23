"""Test file service layer"""

from unittest import skipUnless
from unittest.mock import Mock, patch
from urllib.parse import urlparse

from django.db import DatabaseError
from django.http import HttpRequest
from django.test import TestCase

from authentik.admin.files.manager import FileManager
from authentik.admin.files.tests.utils import (
    FileTestFileBackendMixin,
    FileTestS3BackendMixin,
    s3_test_server_available,
)
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


class TestResolveFileUrlBasic(TestCase):
    def test_resolve_empty_path(self):
        """Test resolving empty file path"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("")
        self.assertEqual(result, "")

    def test_resolve_none_path(self):
        """Test resolving None file path"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url(None)
        self.assertEqual(result, "")

    def test_resolve_font_awesome(self):
        """Test resolving Font Awesome icon"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("fa://fa-check")
        self.assertEqual(result, "fa://fa-check")

    def test_resolve_http_url(self):
        """Test resolving HTTP URL"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("http://example.com/icon.png")
        self.assertEqual(result, "http://example.com/icon.png")

    def test_resolve_https_url(self):
        """Test resolving HTTPS URL"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("https://example.com/icon.png")
        self.assertEqual(result, "https://example.com/icon.png")

    def test_resolve_static_path(self):
        """Test resolving static file path"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("/static/authentik/sources/icon.svg")
        self.assertEqual(result, "/static/authentik/sources/icon.svg")

    def test_file_url_theme_variable_uses_light(self):
        """Test file_url resolves %(theme)s to the light variant, never the placeholder"""
        manager = FileManager(FileUsage.MEDIA)
        self.assertEqual(
            manager.file_url("/static/authentik/sources/kerberos/%(theme)s.png"),
            "/static/authentik/sources/kerberos/light.png",
        )
        self.assertEqual(
            manager.file_url("https://example.com/logo-%(theme)s.png"),
            "https://example.com/logo-light.png",
        )

    def test_file_url_forwards_use_cache(self):
        """Test file_url forwards use_cache to backend."""
        manager = FileManager(FileUsage.MEDIA)
        backend = Mock()
        backend.supports_file.return_value = True
        backend.file_url.return_value = "/files/media/public/test.png?token=fresh"
        manager.backends = [backend]

        result = manager.file_url("test.png", use_cache=False)

        self.assertEqual(result, "/files/media/public/test.png?token=fresh")
        backend.file_url.assert_called_once_with("test.png", None, use_cache=False)


class TestResolveFileUrlFileBackend(FileTestFileBackendMixin, TestCase):
    def test_resolve_storage_file(self):
        """Test resolving uploaded storage file"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("test.png").split("?")[0]
        self.assertEqual(result, "/files/media/public/test.png")

    def test_resolve_full_static_with_request(self):
        """Test resolving static file with request builds absolute URI"""
        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
        }

        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("/static/icon.svg", mock_request)

        self.assertEqual(result, "http://example.com/static/icon.svg")

    def test_resolve_full_file_backend_with_request(self):
        """Test resolving FileBackend file with request"""
        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
        }

        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("test.png", mock_request).split("?")[0]

        self.assertEqual(result, "http://example.com/files/media/public/test.png")


@skipUnless(s3_test_server_available(), "S3 test server not available")
class TestResolveFileUrlS3Backend(FileTestS3BackendMixin, TestCase):
    @CONFIG.patch("storage.media.s3.custom_domain", "s3.test:8080/test")
    @CONFIG.patch("storage.media.s3.secure_urls", False)
    def test_resolve_full_s3_backend(self):
        """Test resolving S3Backend returns presigned URL as-is"""
        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
        }

        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("test.png", mock_request)

        # S3 URLs should be returned as-is (already absolute)
        self.assertTrue(result.startswith("http://s3.test:8080/test"))


class TestThemedUrls(FileTestFileBackendMixin, TestCase):
    """Test FileManager.themed_urls method"""

    def test_themed_urls_none_path(self):
        """Test themed_urls returns None for None path"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.themed_urls(None)
        self.assertIsNone(result)

    def test_themed_urls_empty_path(self):
        """Test themed_urls returns None for empty path"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.themed_urls("")
        self.assertIsNone(result)

    def test_themed_urls_no_theme_variable(self):
        """Test themed_urls returns None when no %(theme)s in path"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.themed_urls("logo.png")
        self.assertIsNone(result)

    def test_themed_urls_with_theme_variable(self):
        """Test themed_urls returns dict of URLs for each theme"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.themed_urls("logo-%(theme)s.png")

        self.assertIsInstance(result, dict)
        self.assertIn("light", result)
        self.assertIn("dark", result)
        self.assertIn("logo-light.png", result["light"])
        self.assertIn("logo-dark.png", result["dark"])

    def test_themed_urls_with_request(self):
        """Test themed_urls builds absolute URLs with request"""
        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
        }

        manager = FileManager(FileUsage.MEDIA)
        result = manager.themed_urls("logo-%(theme)s.svg", mock_request)

        self.assertIsInstance(result, dict)
        light_url = urlparse(result["light"])
        dark_url = urlparse(result["dark"])
        self.assertEqual(light_url.scheme, "http")
        self.assertEqual(light_url.netloc, "example.com")
        self.assertEqual(dark_url.scheme, "http")
        self.assertEqual(dark_url.netloc, "example.com")

    def test_themed_urls_passthrough_with_theme_variable(self):
        """Test themed_urls returns dict for passthrough URLs with %(theme)s"""
        manager = FileManager(FileUsage.MEDIA)
        # External URLs with %(theme)s should return themed URLs
        result = manager.themed_urls("https://example.com/logo-%(theme)s.png")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["light"], "https://example.com/logo-light.png")
        self.assertEqual(result["dark"], "https://example.com/logo-dark.png")

    def test_themed_urls_passthrough_without_theme_variable(self):
        """Test themed_urls returns None for passthrough URLs without %(theme)s"""
        manager = FileManager(FileUsage.MEDIA)
        # External URLs without %(theme)s should return None
        result = manager.themed_urls("https://example.com/logo.png")
        self.assertIsNone(result)


class TestPrefetchUrls(FileTestFileBackendMixin, TestCase):
    """Test FileManager.prefetch_urls"""

    names = [
        "logo.png",
        "logo-%(theme)s.svg",
        "https://goauthentik.io/logo.png",
        "/static/dist/assets/icons/icon.svg",
    ]

    def _urls(self, manager: FileManager) -> list:
        return [(manager.file_url(name), manager.themed_urls(name)) for name in self.names]

    def test_prefetch_urls(self):
        """Inside the block, file_url() and themed_urls() return the URLs they return outside
        it, and reading the cached ones takes one query"""
        manager = FileManager(FileUsage.MEDIA)
        expected = self._urls(manager)
        with self.assertNumQueries(1), manager.prefetch_urls(self.names):
            self.assertEqual(self._urls(manager), expected)

    def test_prefetch_urls_uncached(self):
        """A URL that is not cached yet is generated and cached inside the block"""
        manager = FileManager(FileUsage.MEDIA)
        with manager.prefetch_urls(["logo.png"]):
            url = manager.file_url("logo.png")
        with self.assertNumQueries(1):
            self.assertEqual(manager.file_url("logo.png"), url)

    def test_prefetch_urls_cache_error(self):
        """When the bulk read fails, each call reads its own URL, as without the block"""
        manager = FileManager(FileUsage.MEDIA)
        expected = self._urls(manager)
        with (
            patch("authentik.admin.files.manager.cache.get_many", side_effect=DatabaseError),
            manager.prefetch_urls(self.names),
        ):
            self.assertEqual(self._urls(manager), expected)
