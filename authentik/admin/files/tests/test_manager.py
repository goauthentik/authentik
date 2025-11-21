"""Test file service layer"""

from django.http import HttpRequest
from django.test import TestCase

from authentik.admin.files.manager import FileManager
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


class TestResolveFileUrl(TestCase):
    """Test resolve_file_url function"""

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

    @CONFIG.patch("storage.media.backend", "file")
    def test_resolve_storage_file(self):
        """Test resolving uploaded storage file"""
        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("test.png")
        self.assertEqual(result, "/media/public/test.png")

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

    @CONFIG.patch("storage.media.backend", "file")
    def test_resolve_full_file_backend_with_request(self):
        """Test resolving FileBackend file with request"""
        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
        }

        manager = FileManager(FileUsage.MEDIA)
        result = manager.file_url("test.png", mock_request)

        self.assertEqual(result, "http://example.com/media/public/test.png")

    @CONFIG.patch("storage.media.backend", "s3")
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
