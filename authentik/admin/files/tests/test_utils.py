"""Test file utility functions"""

from unittest.mock import MagicMock, patch

from django.http import HttpRequest
from django.test import TestCase

from authentik.admin.files.utils import (
    RequestWrapper,
    add_schema_prefix,
    get_mime_from_filename,
    get_schema_name,
    get_storage_config,
    get_web_path_prefix,
    strip_schema_prefix,
)


class TestRequestWrapper(TestCase):
    """Test RequestWrapper class"""

    def test_with_none_request(self):
        """Test wrapper with None request"""
        wrapper = RequestWrapper(None)
        self.assertIsNone(wrapper.host)
        self.assertEqual(wrapper.scheme, "https")
        self.assertEqual(wrapper.build_absolute_uri("/test"), "/test")

    def test_with_django_request(self):
        """Test wrapper with Django HttpRequest"""
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.get_host.return_value = "example.com"
        mock_request.is_secure.return_value = True
        # Make sure it doesn't have _request attribute (not a DRF request)
        del mock_request._request

        wrapper = RequestWrapper(mock_request)
        self.assertEqual(wrapper.host, "example.com")
        self.assertEqual(wrapper.scheme, "https")
        self.assertEqual(wrapper.build_absolute_uri("/test"), "https://example.com/test")

    def test_with_drf_request(self):
        """Test wrapper with DRF Request"""
        mock_django_request = MagicMock(spec=HttpRequest)
        mock_django_request.get_host.return_value = "api.example.com"
        mock_django_request.is_secure.return_value = False  # HTTP

        # Mock DRF request that wraps Django request
        drf_request = MagicMock()
        drf_request._request = mock_django_request

        wrapper = RequestWrapper(drf_request)
        self.assertEqual(wrapper.host, "api.example.com")
        self.assertEqual(wrapper.scheme, "http")
        self.assertEqual(wrapper.build_absolute_uri("/api/test"), "http://api.example.com/api/test")

    def test_host_error_handling(self):
        """Test host property handles errors gracefully"""
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.get_host.side_effect = AttributeError()
        # Configure mock to raise AttributeError when _request is accessed
        type(mock_request)._request = property(lambda self: (_ for _ in ()).throw(AttributeError()))

        wrapper = RequestWrapper(mock_request)
        self.assertIsNone(wrapper.host)

    def test_scheme_error_handling(self):
        """Test scheme property handles errors gracefully"""
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.is_secure.side_effect = TypeError()
        # Configure mock to raise AttributeError when _request is accessed
        type(mock_request)._request = property(lambda self: (_ for _ in ()).throw(AttributeError()))

        wrapper = RequestWrapper(mock_request)
        self.assertEqual(wrapper.scheme, "https")


class TestGetStorageConfig(TestCase):
    """Test get_storage_config function"""

    @patch("authentik.admin.files.utils.CONFIG")
    def test_get_config_value(self, mock_config):
        """Test getting config value"""
        mock_config.get.return_value = "test-bucket"

        result = get_storage_config("s3.bucket_name")

        self.assertEqual(result, "test-bucket")
        mock_config.get.assert_called_once_with("storage.s3.bucket_name", None)

    @patch("authentik.admin.files.utils.CONFIG")
    def test_get_config_with_default(self, mock_config):
        """Test getting config with default value"""
        mock_config.get.return_value = "default-value"

        _ = get_storage_config("missing.key", "default-value")

        mock_config.get.assert_called_once_with("storage.missing.key", "default-value")


class TestGetMimeFromFilename(TestCase):
    """Test get_mime_from_filename function"""

    def test_image_png(self):
        """Test PNG image MIME type"""
        self.assertEqual(get_mime_from_filename("test.png"), "image/png")

    def test_image_jpeg(self):
        """Test JPEG image MIME type"""
        self.assertEqual(get_mime_from_filename("test.jpg"), "image/jpeg")

    def test_image_svg(self):
        """Test SVG image MIME type"""
        self.assertEqual(get_mime_from_filename("test.svg"), "image/svg+xml")

    def test_text_plain(self):
        """Test text file MIME type"""
        self.assertEqual(get_mime_from_filename("test.txt"), "text/plain")

    def test_unknown_extension(self):
        """Test unknown extension returns octet-stream"""
        self.assertEqual(get_mime_from_filename("test.unknown"), "application/octet-stream")

    def test_no_extension(self):
        """Test no extension returns octet-stream"""
        self.assertEqual(get_mime_from_filename("test"), "application/octet-stream")


class TestGetWebPathPrefix(TestCase):
    """Test get_web_path_prefix function"""

    @patch("authentik.admin.files.utils.CONFIG")
    def test_default_path(self, mock_config):
        """Test default web path"""
        mock_config.get.return_value = "/"

        result = get_web_path_prefix()

        self.assertEqual(result, "")
        mock_config.get.assert_called_once_with("web.path", "/")

    @patch("authentik.admin.files.utils.CONFIG")
    def test_custom_path(self, mock_config):
        """Test custom web path"""
        mock_config.get.return_value = "/authentik/"

        result = get_web_path_prefix()

        self.assertEqual(result, "/authentik")


class TestGetSchemaName(TestCase):
    """Test get_schema_name function"""

    @patch("authentik.admin.files.utils.connection")
    def test_get_schema_name(self, mock_connection):
        """Test getting schema name"""
        mock_connection.schema_name = "public"

        result = get_schema_name()

        self.assertEqual(result, "public")


class TestStripSchemaPrefix(TestCase):
    """Test strip_schema_prefix function"""

    @patch("authentik.admin.files.utils.get_schema_name")
    def test_strip_prefix(self, mock_get_schema):
        """Test stripping schema prefix"""
        mock_get_schema.return_value = "public"

        result = strip_schema_prefix("public/test.png")

        self.assertEqual(result, "test.png")

    @patch("authentik.admin.files.utils.get_schema_name")
    def test_no_prefix(self, mock_get_schema):
        """Test file without prefix"""
        mock_get_schema.return_value = "public"

        result = strip_schema_prefix("test.png")

        self.assertEqual(result, "test.png")


class TestAddSchemaPrefix(TestCase):
    """Test add_schema_prefix function"""

    @patch("authentik.admin.files.utils.get_schema_name")
    def test_add_prefix(self, mock_get_schema):
        """Test adding schema prefix"""
        mock_get_schema.return_value = "public"

        result = add_schema_prefix("test.png")

        self.assertEqual(result, "public/test.png")
