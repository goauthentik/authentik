"""Test file service layer"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.admin.files.backend import Usage
from authentik.admin.files.service import (
    is_file_path_supported,
    resolve_file_url,
    resolve_file_url_full,
)


class TestResolveFileUrl(TestCase):
    """Test resolve_file_url function"""

    def test_resolve_empty_path(self):
        """Test resolving empty file path"""
        result = resolve_file_url("", Usage.MEDIA)
        self.assertEqual(result, "")

    def test_resolve_none_path(self):
        """Test resolving None file path"""
        result = resolve_file_url(None, Usage.MEDIA)
        self.assertIsNone(result)

    @patch("authentik.admin.files.service.BackendFactory.get_passthrough_backend")
    def test_resolve_font_awesome(self, mock_get_backend):
        """Test resolving Font Awesome icon"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "fa://fa-check"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url("fa://fa-check", Usage.MEDIA)

        self.assertEqual(result, "fa://fa-check")
        mock_get_backend.assert_called_once_with(Usage.MEDIA)
        mock_backend.file_url.assert_called_once_with("fa://fa-check")

    @patch("authentik.admin.files.service.BackendFactory.get_passthrough_backend")
    def test_resolve_http_url(self, mock_get_backend):
        """Test resolving HTTP URL"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "http://example.com/icon.png"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url("http://example.com/icon.png", Usage.MEDIA)

        self.assertEqual(result, "http://example.com/icon.png")
        mock_backend.file_url.assert_called_once_with("http://example.com/icon.png")

    @patch("authentik.admin.files.service.BackendFactory.get_passthrough_backend")
    def test_resolve_https_url(self, mock_get_backend):
        """Test resolving HTTPS URL"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "https://example.com/icon.png"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url("https://example.com/icon.png", Usage.MEDIA)

        self.assertEqual(result, "https://example.com/icon.png")
        mock_backend.file_url.assert_called_once_with("https://example.com/icon.png")

    @patch("authentik.admin.files.service.BackendFactory.get_static_backend")
    def test_resolve_static_path(self, mock_get_backend):
        """Test resolving static file path"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "/static/authentik/sources/icon.svg"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url("/static/authentik/sources/icon.svg", Usage.MEDIA)

        self.assertEqual(result, "/static/authentik/sources/icon.svg")
        mock_get_backend.assert_called_once_with(Usage.MEDIA)

    @patch("authentik.admin.files.service.BackendFactory.get_static_backend")
    def test_resolve_web_dist_assets(self, mock_get_backend):
        """Test resolving web/dist/assets path"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "/static/dist/assets/icon.svg"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url("web/dist/assets/icon.svg", Usage.MEDIA)

        self.assertEqual(result, "/static/dist/assets/icon.svg")
        mock_get_backend.assert_called_once_with(Usage.MEDIA)

    @patch("authentik.admin.files.service.BackendFactory.create")
    def test_resolve_storage_file(self, mock_factory):
        """Test resolving uploaded storage file"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "/media/public/test.png"
        mock_factory.return_value = mock_backend

        result = resolve_file_url("test.png", Usage.MEDIA)

        self.assertEqual(result, "/media/public/test.png")
        mock_factory.assert_called_once_with(Usage.MEDIA)
        mock_backend.file_url.assert_called_once_with("test.png")

    @patch("authentik.admin.files.service.strip_schema_prefix")
    @patch("authentik.admin.files.service.BackendFactory.create")
    def test_resolve_storage_file_with_schema_prefix(self, mock_factory, mock_strip):
        """Test resolving storage file with schema prefix"""
        mock_strip.return_value = "test.png"
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "/media/public/test.png"
        mock_factory.return_value = mock_backend

        result = resolve_file_url("public/test.png", Usage.MEDIA)

        self.assertEqual(result, "/media/public/test.png")
        mock_strip.assert_called_once_with("public/test.png")
        mock_backend.file_url.assert_called_once_with("test.png")


class TestResolveFileUrlFull(TestCase):
    """Test resolve_file_url_full function"""

    def test_resolve_full_empty_path(self):
        """Test resolving empty file path"""
        result = resolve_file_url_full("", Usage.MEDIA)
        self.assertEqual(result, "")

    def test_resolve_full_none_path(self):
        """Test resolving None file path"""
        result = resolve_file_url_full(None, Usage.MEDIA)
        self.assertIsNone(result)

    @patch("authentik.admin.files.service.BackendFactory.get_passthrough_backend")
    def test_resolve_full_font_awesome(self, mock_get_backend):
        """Test resolving Font Awesome returns as-is"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "fa://fa-check"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url_full("fa://fa-check", Usage.MEDIA)

        self.assertEqual(result, "fa://fa-check")

    @patch("authentik.admin.files.service.BackendFactory.get_passthrough_backend")
    def test_resolve_full_external_url(self, mock_get_backend):
        """Test resolving external URL returns as-is"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "https://example.com/icon.png"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url_full("https://example.com/icon.png", Usage.MEDIA)

        self.assertEqual(result, "https://example.com/icon.png")

    @patch("authentik.admin.files.service.BackendFactory.get_static_backend")
    def test_resolve_full_static_with_request(self, mock_get_backend):
        """Test resolving static file with request builds absolute URI"""
        from django.http import HttpRequest

        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "/static/icon.svg"
        mock_get_backend.return_value = mock_backend

        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
            "SERVER_PORT": "443",
            "wsgi.url_scheme": "https",
        }
        # Mock is_secure() to return True for HTTPS
        # Note: can't use HTTPS: "on" in META because HttpRequest.is_secure() doesn't check that
        # in test environment it requires proper WSGI setup which we can't easily mock and it's just impractical to do
        mock_request.is_secure = MagicMock(return_value=True)

        result = resolve_file_url_full("/static/icon.svg", Usage.MEDIA, mock_request)

        self.assertEqual(result, "https://example.com/static/icon.svg")

    @patch("authentik.admin.files.service.BackendFactory.get_static_backend")
    def test_resolve_full_static_without_request(self, mock_get_backend):
        """Test resolving static file without request returns relative URL"""
        mock_backend = MagicMock()
        mock_backend.file_url.return_value = "/static/icon.svg"
        mock_get_backend.return_value = mock_backend

        result = resolve_file_url_full("/static/icon.svg", Usage.MEDIA, None)

        self.assertEqual(result, "/static/icon.svg")

    @patch("authentik.admin.files.service.BackendFactory.create")
    def test_resolve_full_file_backend_with_request(self, mock_factory):
        """Test resolving FileBackend file with request"""
        from django.http import HttpRequest

        from authentik.admin.files.backends import FileBackend

        mock_backend = FileBackend(Usage.MEDIA)
        mock_backend.file_url = MagicMock(return_value="/media/public/test.png")
        mock_factory.return_value = mock_backend

        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "example.com",
            "SERVER_PORT": "443",
            "wsgi.url_scheme": "https",
        }
        # Mock is_secure() to return True for HTTPS
        mock_request.is_secure = MagicMock(return_value=True)

        result = resolve_file_url_full("test.png", Usage.MEDIA, mock_request)

        self.assertEqual(result, "https://example.com/media/public/test.png")

    @patch("authentik.admin.files.service.BackendFactory.create")
    def test_resolve_full_s3_backend(self, mock_factory):
        """Test resolving S3Backend returns presigned URL as-is"""
        from django.http import HttpRequest

        from authentik.admin.files.backends import S3Backend

        mock_backend = MagicMock(spec=S3Backend)
        mock_backend.file_url.return_value = "https://s3.example.com/presigned-url"
        mock_factory.return_value = mock_backend

        mock_request = HttpRequest()
        mock_request.META = {
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "https",
            "HTTPS": "on",  # This makes is_secure() return True
        }

        result = resolve_file_url_full("test.png", Usage.MEDIA, mock_request)

        # S3 URLs should be returned as-is (already absolute)
        self.assertEqual(result, "https://s3.example.com/presigned-url")

    @patch("authentik.admin.files.service.BackendFactory.create")
    def test_resolve_full_file_backend_without_request(self, mock_factory):
        """Test resolving FileBackend file without request returns relative URL"""
        from authentik.admin.files.backends import FileBackend

        mock_backend = FileBackend(Usage.MEDIA)
        mock_backend.file_url = MagicMock(return_value="/media/public/test.png")
        mock_factory.return_value = mock_backend

        result = resolve_file_url_full("test.png", Usage.MEDIA, None)

        self.assertEqual(result, "/media/public/test.png")


class TestIsFilePathSupported(TestCase):
    """Test is_file_path_supported function"""

    def test_static_backend_static_prefix(self):
        """Test static backend supports /static/ paths"""
        self.assertTrue(is_file_path_supported("/static/icon.svg", "static"))

    def test_static_backend_web_dist(self):
        """Test static backend supports web/dist/assets paths"""
        self.assertTrue(is_file_path_supported("web/dist/assets/icon.svg", "static"))

    def test_static_backend_other_path(self):
        """Test static backend doesn't support other paths"""
        self.assertFalse(is_file_path_supported("test.png", "static"))

    def test_passthrough_backend_font_awesome(self):
        """Test passthrough backend supports Font Awesome"""
        self.assertTrue(is_file_path_supported("fa://fa-check", "passthrough"))

    def test_passthrough_backend_http(self):
        """Test passthrough backend supports HTTP URLs"""
        self.assertTrue(is_file_path_supported("http://example.com/icon.png", "passthrough"))

    def test_passthrough_backend_https(self):
        """Test passthrough backend supports HTTPS URLs"""
        self.assertTrue(is_file_path_supported("https://example.com/icon.png", "passthrough"))

    def test_passthrough_backend_other_path(self):
        """Test passthrough backend doesn't support other paths"""
        self.assertFalse(is_file_path_supported("test.png", "passthrough"))

    def test_file_backend_normal_path(self):
        """Test file backend supports normal uploaded files"""
        self.assertTrue(is_file_path_supported("test.png", "file"))

    def test_file_backend_not_static(self):
        """Test file backend doesn't support static paths"""
        self.assertFalse(is_file_path_supported("/static/icon.svg", "file"))

    def test_file_backend_not_passthrough(self):
        """Test file backend doesn't support passthrough paths"""
        self.assertFalse(is_file_path_supported("fa://fa-check", "file"))
        self.assertFalse(is_file_path_supported("https://example.com/icon.png", "file"))

    def test_s3_backend_normal_path(self):
        """Test s3 backend supports normal uploaded files"""
        self.assertTrue(is_file_path_supported("test.png", "s3"))

    def test_s3_backend_not_static(self):
        """Test s3 backend doesn't support static paths"""
        self.assertFalse(is_file_path_supported("/static/icon.svg", "s3"))
