from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.test import TestCase

from authentik.admin.files.backends.s3 import S3Backend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


class TestS3Backend(TestCase):
    """Test S3 backend functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.usage = FileUsage.MEDIA
        self.backend = S3Backend(self.usage)

    def test_init(self):
        """Test S3Backend initialization"""
        self.assertEqual(self.backend.usage, self.usage)

    def test_base_path(self):
        """Test base_path property generates correct S3 key prefix"""
        expected = f"{self.usage.value}/public"
        self.assertEqual(self.backend.base_path, expected)

    @CONFIG.patch("storage.s3.bucket_name", "my-test-bucket")
    def test_bucket_name(self):
        """Test bucket_name property retrieves from config"""
        self.assertEqual(self.backend.bucket_name, "my-test-bucket")

    @CONFIG.patch("storage.s3.session_profile", "my-profile")
    @patch("authentik.admin.files.backends.s3.boto3.Session")
    def test_session_with_profile(self, mock_boto_session):
        """Test session property with profile_name"""
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        session = self.backend.session

        mock_boto_session.assert_called_once_with(profile_name="my-profile")
        self.assertEqual(session, mock_session_instance)

    @CONFIG.patch("storage.s3.access_key", "my-access-key")
    @CONFIG.patch("storage.s3.secret_key", "my-secret-key")
    @CONFIG.patch("storage.s3.security_token", "my-security-token")
    @patch("authentik.admin.files.backends.s3.boto3.Session")
    def test_session_with_credentials(self, mock_boto_session):
        """Test session property with explicit credentials"""
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        session = self.backend.session

        mock_boto_session.assert_called_once_with(
            aws_access_key_id="my-access-key",
            aws_secret_access_key="my-secret-key",
            aws_session_token="my-security-token",
        )
        self.assertEqual(session, mock_session_instance)

    @CONFIG.patch("storage.s3.endpoint", "https://s3.example.com")
    @CONFIG.patch("storage.s3.region", "us-west-2")
    @CONFIG.patch("storage.s3.addressing_style", "path")
    @patch("authentik.admin.files.backends.s3.boto3.Session")
    def test_client_creation(self, mock_boto_session):
        """Test S3 client creation with configuration"""
        mock_session_instance = MagicMock()
        mock_client_instance = MagicMock()
        mock_session_instance.client.return_value = mock_client_instance
        mock_boto_session.return_value = mock_session_instance

        _ = self.backend.client

        # Verify client was created with correct parameters
        mock_session_instance.client.assert_called_once()
        call_args = mock_session_instance.client.call_args
        self.assertEqual(call_args[0][0], "s3")
        self.assertEqual(call_args[1]["endpoint_url"], "https://s3.example.com")
        self.assertEqual(call_args[1]["region_name"], "us-west-2")

    def test_supports_file_path_s3(self):
        """Test supports_file_path returns True for s3 backend"""
        self.assertTrue(self.backend.supports_file("path/to/any-file.png"))
        self.assertTrue(self.backend.supports_file("any-file.png"))

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_list_files(self):
        """Test list_files returns relative paths"""
        # Mock the client and paginator
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "media/public/file1.png"},
                    {"Key": "media/public/subdir/file2.jpg"},
                    {"Key": "media/public/"},  # Directory entry - should be skipped
                ]
            },
            {
                "Contents": [
                    {"Key": "media/public/file3.svg"},
                ]
            },
        ]

        with patch.object(self.backend, "client") as mock_client:
            mock_client.get_paginator.return_value = mock_paginator

            files = list(self.backend.list_files())

            self.assertEqual(len(files), 3)
            self.assertIn("file1.png", files)
            self.assertIn("subdir/file2.jpg", files)
            self.assertIn("file3.svg", files)

            # Verify paginate was called with correct parameters
            mock_paginator.paginate.assert_called_once_with(
                Bucket="test-bucket", Prefix="media/public/"
            )

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_list_files_empty(self):
        """Test list_files with no files"""
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{}]

        with patch.object(self.backend, "client") as mock_client:
            mock_client.get_paginator.return_value = mock_paginator

            files = list(self.backend.list_files())

            self.assertEqual(len(files), 0)

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_save_file(self):
        """Test save_file uploads to S3"""
        with patch.object(self.backend, "client") as mock_client:
            content = b"test file content"
            self.backend.save_file("test.png", content)

            mock_client.put_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="media/public/test.png",
                Body=content,
                ACL="private",
            )

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_save_file_stream(self):
        """Test save_file_stream uploads to S3 using context manager"""
        with patch.object(self.backend, "client") as mock_client:
            with self.backend.save_file_stream("test.csv") as f:
                f.write(b"header1,header2\n")
                f.write(b"value1,value2\n")

            # Verify put_object was called after context exits
            mock_client.upload_fileobj.assert_called_once()
            call_args = mock_client.upload_fileobj.call_args[1]

            self.assertEqual(call_args["Bucket"], "test-bucket")
            self.assertEqual(call_args["Key"], "media/public/test.csv")
            self.assertEqual(call_args["ExtraArgs"]["ACL"], "private")

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_delete_file(self):
        """Test delete_file removes from S3"""
        with patch.object(self.backend, "client") as mock_client:
            self.backend.delete_file("test.png")

            mock_client.delete_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="media/public/test.png",
            )

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    @CONFIG.patch("storage.s3.secure_urls", True)
    @CONFIG.patch("storage.s3.custom_domain", None)
    def test_file_url_basic(self):
        """Test file_url generates presigned URL with AWS signature format"""
        with patch.object(self.backend, "client") as mock_client:
            # Mock presigned URL with AWS SigV4 query parameters
            mock_client.generate_presigned_url.return_value = (
                "https://test-bucket.s3.amazonaws.com/media/public/test.png?"
                "X-Amz-Algorithm=AWS4-HMAC-SHA256&"
                "X-Amz-Credential=AKIAEXAMPLE%2F20251114%2Fus-east-1%2Fs3%2Faws4_request&"
                "X-Amz-Date=20251114T015841Z&"
                "X-Amz-Expires=3600&"
                "X-Amz-SignedHeaders=host&"
                "X-Amz-Signature=abcdef1234567890"
            )

            url = self.backend.file_url("test.png")

            mock_client.generate_presigned_url.assert_called_once_with(
                "get_object",
                Params={"Bucket": "test-bucket", "Key": "media/public/test.png"},
                ExpiresIn=60 * 15,
                HttpMethod="GET",
            )
            self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)
            self.assertIn("X-Amz-Signature=", url)
            self.assertIn("test.png", url)

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    @CONFIG.patch("storage.s3.secure_urls", True)
    @CONFIG.patch("storage.s3.custom_domain", "cdn.example.com")
    def test_file_url_with_custom_domain(self):
        """Test file_url with custom domain replacement"""
        with patch.object(self.backend, "client") as mock_client:
            # Mock S3-compatible storage presigned URL
            mock_client.generate_presigned_url.return_value = (
                "https://storage.provider.com/bucket-name/media/public/test.png?"
                "X-Amz-Algorithm=AWS4-HMAC-SHA256&"
                "X-Amz-Credential=KEY123%2F20251114%2Fus-east-1%2Fs3%2Faws4_request&"
                "X-Amz-Date=20251114T015841Z&"
                "X-Amz-Expires=3600&"
                "X-Amz-SignedHeaders=host&"
                "X-Amz-Signature=signature123"
            )

            url = self.backend.file_url("test.png")

            # Should replace domain but keep path and query parameters
            self.assertTrue(url.startswith("https://cdn.example.com/"))
            self.assertIn("X-Amz-Signature=signature123", url)
            self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)
            self.assertIn("media/public/test.png", url)

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    @CONFIG.patch("storage.s3.secure_urls", False)
    @CONFIG.patch("storage.s3.custom_domain", "cdn.example.com")
    def test_file_url_insecure(self):
        """Test file_url with secure_urls=false"""
        with patch.object(self.backend, "client") as mock_client:
            mock_client.generate_presigned_url.return_value = (
                "https://s3.amazonaws.com/test-bucket/media/public/test.png?"
                "X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Signature=abc123"
            )

            url = self.backend.file_url("test.png")

            # Should use http instead of https
            self.assertTrue(url.startswith("http://cdn.example.com/"))

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    @CONFIG.patch("storage.s3.secure_urls", True)
    @CONFIG.patch("storage.s3.custom_domain", None)
    @CONFIG.patch("storage.s3.presigned_expiry", "minutes=1")
    def test_file_url_custom_expiry(self):
        """Test file_url with custom expiry time"""
        with patch.object(self.backend, "client") as mock_client:
            mock_client.generate_presigned_url.return_value = (
                "https://example.com/file?X-Amz-Expires=7200&X-Amz-Signature=abc"
            )

            self.backend.file_url("test.png")

            call_args = mock_client.generate_presigned_url.call_args[1]
            self.assertEqual(call_args["ExpiresIn"], 60)

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_file_exists_true(self):
        """Test file_exists returns True for existing file"""
        with patch.object(self.backend, "client") as mock_client:
            mock_client.head_object.return_value = {}

            exists = self.backend.file_exists("test.png")

            self.assertTrue(exists)
            mock_client.head_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="media/public/test.png",
            )

    @CONFIG.patch("storage.s3.bucket_name", "test-bucket")
    def test_file_exists_false(self):
        """Test file_exists returns False for non-existent file"""
        with patch.object(self.backend, "client") as mock_client:
            mock_client.head_object.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
            )

            exists = self.backend.file_exists("nonexistent.png")

            self.assertFalse(exists)

    def test_allowed_usages(self):
        """Test that S3Backend supports all usage types"""
        self.assertEqual(self.backend.allowed_usages, list(FileUsage))

    def test_reports_usage(self):
        """Test S3Backend with REPORTS usage"""
        backend = S3Backend(FileUsage.REPORTS)

        self.assertEqual(backend.usage, FileUsage.REPORTS)
        self.assertEqual(backend.base_path, "reports/public")
