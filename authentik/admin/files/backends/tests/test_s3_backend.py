from django.test import TestCase

from authentik.admin.files.tests.utils import FileTestS3BackendMixin
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


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
