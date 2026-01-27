from unittest import skipUnless

from django.test import TestCase

from authentik.admin.files.tests.utils import FileTestS3BackendMixin, s3_test_server_available
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


@skipUnless(s3_test_server_available(), "S3 test server not available")
class TestS3Backend(FileTestS3BackendMixin, TestCase):
    """Test S3 backend functionality"""

    def setUp(self):
        super().setUp()

    def test_base_path(self):
        """Test base_path property generates correct S3 key prefix"""
        expected = "media/public"
        self.assertEqual(self.media_s3_backend.base_path, expected)

    def test_supports_file_path_s3(self):
        """Test supports_file_path returns True for s3 backend"""
        self.assertTrue(self.media_s3_backend.supports_file("path/to/any-file.png"))
        self.assertTrue(self.media_s3_backend.supports_file("any-file.png"))

    def test_list_files(self):
        """Test list_files returns relative paths"""
        self.media_s3_backend.client.put_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/file1.png",
            Body=b"test content",
            ACL="private",
        )
        self.media_s3_backend.client.put_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/other/file1.png",
            Body=b"test content",
            ACL="private",
        )

        files = list(self.media_s3_backend.list_files())

        self.assertEqual(len(files), 1)
        self.assertIn("file1.png", files)

    def test_list_files_empty(self):
        """Test list_files with no files"""
        files = list(self.media_s3_backend.list_files())

        self.assertEqual(len(files), 0)

    def test_save_file(self):
        """Test save_file uploads to S3"""
        content = b"test file content"
        self.media_s3_backend.save_file("test.png", content)

    def test_save_file_stream(self):
        """Test save_file_stream uploads to S3 using context manager"""
        with self.media_s3_backend.save_file_stream("test.csv") as f:
            f.write(b"header1,header2\n")
            f.write(b"value1,value2\n")

    def test_delete_file(self):
        """Test delete_file removes from S3"""
        self.media_s3_backend.client.put_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/test.png",
            Body=b"test content",
            ACL="private",
        )
        self.media_s3_backend.delete_file("test.png")

    @CONFIG.patch("storage.s3.secure_urls", True)
    @CONFIG.patch("storage.s3.custom_domain", None)
    def test_file_url_basic(self):
        """Test file_url generates presigned URL with AWS signature format"""
        url = self.media_s3_backend.file_url("test.png")

        self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)
        self.assertIn("X-Amz-Signature=", url)
        self.assertIn("test.png", url)

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_file_exists_true(self):
        """Test file_exists returns True for existing file"""
        self.media_s3_backend.client.put_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/test.png",
            Body=b"test content",
            ACL="private",
        )

        exists = self.media_s3_backend.file_exists("test.png")

        self.assertTrue(exists)

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_file_exists_false(self):
        """Test file_exists returns False for non-existent file"""
        exists = self.media_s3_backend.file_exists("nonexistent.png")

        self.assertFalse(exists)

    def test_allowed_usages(self):
        """Test that S3Backend supports all usage types"""
        self.assertEqual(self.media_s3_backend.allowed_usages, list(FileUsage))

    def test_reports_usage(self):
        """Test S3Backend with REPORTS usage"""
        self.assertEqual(self.reports_s3_backend.usage, FileUsage.REPORTS)
        self.assertEqual(self.reports_s3_backend.base_path, "reports/public")

    @CONFIG.patch("storage.s3.secure_urls", True)
    @CONFIG.patch("storage.s3.addressing_style", "path")
    def test_file_url_custom_domain_with_bucket_no_duplicate(self):
        """Test file_url doesn't duplicate bucket name when custom_domain includes bucket.

        Regression test for https://github.com/goauthentik/authentik/issues/19521

        When using:
        - Path-style addressing (bucket name goes in URL path, not subdomain)
        - Custom domain that includes the bucket name (e.g., s3.example.com/bucket-name)

        The bucket name should NOT appear twice in the final URL.

        Example of the bug:
        - custom_domain = "s3.example.com/authentik-media"
        - boto3 presigned URL = "http://s3.example.com/authentik-media/media/public/file.png?..."
        - Buggy result = "https://s3.example.com/authentik-media/authentik-media/media/public/file.png?..."
        """
        bucket_name = self.media_s3_bucket_name

        # Custom domain includes the bucket name
        custom_domain = f"localhost:8020/{bucket_name}"

        with CONFIG.patch("storage.media.s3.custom_domain", custom_domain):
            url = self.media_s3_backend.file_url("application-icons/test.svg", use_cache=False)

        # The bucket name should appear exactly once in the URL path, not twice
        bucket_occurrences = url.count(bucket_name)
        self.assertEqual(
            bucket_occurrences,
            1,
            f"Bucket name '{bucket_name}' appears {bucket_occurrences} times in URL, expected 1. "
            f"URL: {url}",
        )

    def test_themed_urls_without_theme_variable(self):
        """Test themed_urls returns None when filename has no %(theme)s"""
        result = self.media_s3_backend.themed_urls("logo.png")
        self.assertIsNone(result)

    def test_themed_urls_with_theme_variable(self):
        """Test themed_urls returns dict of presigned URLs for each theme"""
        result = self.media_s3_backend.themed_urls("logo-%(theme)s.png")

        self.assertIsInstance(result, dict)
        self.assertIn("light", result)
        self.assertIn("dark", result)

        # Check URLs are valid presigned URLs with correct file paths
        self.assertIn("logo-light.png", result["light"])
        self.assertIn("logo-dark.png", result["dark"])
        self.assertIn("X-Amz-Signature=", result["light"])
        self.assertIn("X-Amz-Signature=", result["dark"])

    def test_themed_urls_multiple_theme_variables(self):
        """Test themed_urls with multiple %(theme)s in path"""
        result = self.media_s3_backend.themed_urls("%(theme)s/logo-%(theme)s.svg")

        self.assertIsInstance(result, dict)
        self.assertIn("light/logo-light.svg", result["light"])
        self.assertIn("dark/logo-dark.svg", result["dark"])

    def test_save_file_sets_content_type_svg(self):
        """Test save_file sets correct ContentType for SVG files"""
        self.media_s3_backend.save_file("test.svg", b"<svg></svg>")

        response = self.media_s3_backend.client.head_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/test.svg",
        )
        self.assertEqual(response["ContentType"], "image/svg+xml")

    def test_save_file_sets_content_type_png(self):
        """Test save_file sets correct ContentType for PNG files"""
        self.media_s3_backend.save_file("test.png", b"\x89PNG\r\n\x1a\n")

        response = self.media_s3_backend.client.head_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/test.png",
        )
        self.assertEqual(response["ContentType"], "image/png")

    def test_save_file_stream_sets_content_type(self):
        """Test save_file_stream sets correct ContentType"""
        with self.media_s3_backend.save_file_stream("test.css") as f:
            f.write(b"body { color: red; }")

        response = self.media_s3_backend.client.head_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/test.css",
        )
        self.assertEqual(response["ContentType"], "text/css")

    def test_save_file_unknown_extension_octet_stream(self):
        """Test save_file sets octet-stream for unknown extensions"""
        self.media_s3_backend.save_file("test.unknownext123", b"data")

        response = self.media_s3_backend.client.head_object(
            Bucket=self.media_s3_bucket_name,
            Key="media/public/test.unknownext123",
        )
        self.assertEqual(response["ContentType"], "application/octet-stream")
