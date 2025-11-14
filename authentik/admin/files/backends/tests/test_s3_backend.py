"""Test S3 backend implementation"""

from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

from botocore.exceptions import ClientError
from django.test import TestCase

from authentik.admin.files.backend import Usage
from authentik.admin.files.backends.s3 import S3Backend
from authentik.admin.files.constants import S3_DEFAULT_ACL, S3_PRESIGNED_URL_EXPIRY_SECONDS


class TestS3Backend(TestCase):
    """Test S3 backend functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.usage = Usage.MEDIA

    @patch("authentik.admin.files.backends.s3.boto3.Session")
    @patch("authentik.admin.files.backends.s3.connection")
    def test_init(self, mock_connection, mock_boto_session):
        """Test S3Backend initialization"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.return_value = "s3"
            backend = S3Backend(self.usage)

            self.assertEqual(backend.usage, self.usage)
            self.assertEqual(backend._backend_type, "s3")

    @patch("authentik.admin.files.backends.s3.connection")
    def test_base_path(self, mock_connection):
        """Test base_path property generates correct S3 key prefix"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.return_value = "s3"
            backend = S3Backend(self.usage)

            expected = f"{self.usage.value}/public/"
            self.assertEqual(backend.base_path, expected)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_bucket_name(self, mock_connection):
        """Test bucket_name property retrieves from config"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "my-test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)
            self.assertEqual(backend.bucket_name, "my-test-bucket")

    @patch("authentik.admin.files.backends.s3.boto3.Session")
    @patch("authentik.admin.files.backends.s3.connection")
    def test_session_with_profile(self, mock_connection, mock_boto_session):
        """Test session property with profile_name"""
        mock_connection.schema_name = "public"
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.session_profile": "my-profile",
            }.get(key, default)

            backend = S3Backend(self.usage)
            session = backend.session

            mock_boto_session.assert_called_once_with(profile_name="my-profile")
            self.assertEqual(session, mock_session_instance)

    @patch("authentik.admin.files.backends.s3.boto3.Session")
    @patch("authentik.admin.files.backends.s3.connection")
    def test_session_with_credentials(self, mock_connection, mock_boto_session):
        """Test session property with explicit credentials"""
        mock_connection.schema_name = "public"
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.session_profile": None,
                "s3.access_key": "test-access-key",
                "s3.secret_key": "test-secret-key",
                "s3.security_token": "test-token",
            }.get(key, default)

            backend = S3Backend(self.usage)
            session = backend.session

            mock_boto_session.assert_called_once_with(
                aws_access_key_id="test-access-key",
                aws_secret_access_key="test-secret-key",
                aws_session_token="test-token",
            )
            self.assertEqual(session, mock_session_instance)

    @patch("authentik.admin.files.backends.s3.boto3.Session")
    @patch("authentik.admin.files.backends.s3.connection")
    def test_client_creation(self, mock_connection, mock_boto_session):
        """Test S3 client creation with configuration"""
        mock_connection.schema_name = "public"
        mock_session_instance = MagicMock()
        mock_client_instance = MagicMock()
        mock_session_instance.client.return_value = mock_client_instance
        mock_boto_session.return_value = mock_session_instance

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.session_profile": None,
                "s3.endpoint": "https://s3.example.com",
                "s3.region": "us-west-2",
                "s3.addressing_style": "path",
            }.get(key, default)

            backend = S3Backend(self.usage)
            client = backend.client

            # Verify client was created with correct parameters
            mock_session_instance.client.assert_called_once()
            call_args = mock_session_instance.client.call_args
            self.assertEqual(call_args[0][0], "s3")
            self.assertEqual(call_args[1]["endpoint_url"], "https://s3.example.com")
            self.assertEqual(call_args[1]["region_name"], "us-west-2")

    @patch("authentik.admin.files.backends.s3.connection")
    def test_supports_file_path_s3(self, mock_connection):
        """Test supports_file_path returns True for s3 backend"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.return_value = "s3"
            backend = S3Backend(self.usage)

            self.assertTrue(backend.supports_file_path("any-file.png"))

    @patch("authentik.admin.files.backend.get_storage_config")
    @patch("authentik.admin.files.backends.s3.connection")
    def test_supports_file_path_not_s3(self, mock_connection, mock_get_storage_config):
        """Test supports_file_path returns False for non-s3 backend"""
        mock_connection.schema_name = "public"
        # Mock the storage config to return 'file' backend type
        mock_get_storage_config.return_value = "file"

        backend = S3Backend(self.usage)

        self.assertFalse(backend.supports_file_path("any-file.png"))

    @patch("authentik.admin.files.backends.s3.connection")
    def test_list_files(self, mock_connection):
        """Test list_files returns relative paths"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

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

            with patch.object(backend, "client") as mock_client:
                mock_client.get_paginator.return_value = mock_paginator

                files = list(backend.list_files())

                self.assertEqual(len(files), 3)
                self.assertIn("file1.png", files)
                self.assertIn("subdir/file2.jpg", files)
                self.assertIn("file3.svg", files)

                # Verify paginate was called with correct parameters
                mock_paginator.paginate.assert_called_once_with(
                    Bucket="test-bucket", Prefix="media/public/"
                )

    @patch("authentik.admin.files.backends.s3.connection")
    def test_list_files_empty(self, mock_connection):
        """Test list_files with no files"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            mock_paginator = MagicMock()
            mock_paginator.paginate.return_value = [{}]

            with patch.object(backend, "client") as mock_client:
                mock_client.get_paginator.return_value = mock_paginator

                files = list(backend.list_files())

                self.assertEqual(len(files), 0)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_save_file(self, mock_connection):
        """Test save_file uploads to S3"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                content = b"test file content"
                backend.save_file("test.png", content)

                mock_client.put_object.assert_called_once_with(
                    Bucket="test-bucket",
                    Key="media/public/test.png",
                    Body=content,
                    ACL=S3_DEFAULT_ACL,
                )

    @patch("authentik.admin.files.backends.s3.connection")
    def test_save_file_stream(self, mock_connection):
        """Test save_file_stream uploads to S3 using context manager"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                with backend.save_file_stream("test.csv") as f:
                    f.write(b"header1,header2\n")
                    f.write(b"value1,value2\n")

                # Verify put_object was called after context exits
                mock_client.put_object.assert_called_once()
                call_args = mock_client.put_object.call_args[1]

                self.assertEqual(call_args["Bucket"], "test-bucket")
                self.assertEqual(call_args["Key"], "media/public/test.csv")
                self.assertEqual(call_args["Body"], b"header1,header2\nvalue1,value2\n")
                self.assertEqual(call_args["ACL"], S3_DEFAULT_ACL)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_delete_file(self, mock_connection):
        """Test delete_file removes from S3"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                backend.delete_file("test.png")

                mock_client.delete_object.assert_called_once_with(
                    Bucket="test-bucket",
                    Key="media/public/test.png",
                )

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_url_basic(self, mock_connection):
        """Test file_url generates presigned URL with AWS signature format"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
                "s3.secure_urls": True,
                "s3.presigned_expiry": S3_PRESIGNED_URL_EXPIRY_SECONDS,
                "s3.custom_domain": None,
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
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

                url = backend.file_url("test.png")

                mock_client.generate_presigned_url.assert_called_once_with(
                    "get_object",
                    Params={"Bucket": "test-bucket", "Key": "media/public/test.png"},
                    ExpiresIn=S3_PRESIGNED_URL_EXPIRY_SECONDS,
                    HttpMethod="GET",
                )
                self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)
                self.assertIn("X-Amz-Signature=", url)
                self.assertIn("test.png", url)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_url_with_custom_domain(self, mock_connection):
        """Test file_url with custom domain replacement"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
                "s3.secure_urls": True,
                "s3.presigned_expiry": S3_PRESIGNED_URL_EXPIRY_SECONDS,
                "s3.custom_domain": "cdn.example.com",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
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

                url = backend.file_url("test.png")

                # Should replace domain but keep path and query parameters
                self.assertTrue(url.startswith("https://cdn.example.com/"))
                self.assertIn("X-Amz-Signature=signature123", url)
                self.assertIn("X-Amz-Algorithm=AWS4-HMAC-SHA256", url)
                self.assertIn("media/public/test.png", url)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_url_insecure(self, mock_connection):
        """Test file_url with secure_urls=false"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
                "s3.secure_urls": "false",
                "s3.presigned_expiry": S3_PRESIGNED_URL_EXPIRY_SECONDS,
                "s3.custom_domain": "cdn.example.com",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                mock_client.generate_presigned_url.return_value = (
                    "https://s3.amazonaws.com/test-bucket/media/public/test.png?"
                    "X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Signature=abc123"
                )

                url = backend.file_url("test.png")

                # Should use http instead of https
                self.assertTrue(url.startswith("http://cdn.example.com/"))

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_url_custom_expiry(self, mock_connection):
        """Test file_url with custom expiry time"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
                "s3.secure_urls": True,
                "s3.presigned_expiry": "7200",  # String value - should be converted to int
                "s3.custom_domain": None,
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                mock_client.generate_presigned_url.return_value = (
                    "https://example.com/file?X-Amz-Expires=7200&X-Amz-Signature=abc"
                )

                backend.file_url("test.png")

                call_args = mock_client.generate_presigned_url.call_args[1]
                self.assertEqual(call_args["ExpiresIn"], 7200)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_size(self, mock_connection):
        """Test file_size retrieves from S3"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                mock_client.head_object.return_value = {"ContentLength": 12345}

                size = backend.file_size("test.png")

                self.assertEqual(size, 12345)
                mock_client.head_object.assert_called_once_with(
                    Bucket="test-bucket",
                    Key="media/public/test.png",
                )

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_size_not_found(self, mock_connection):
        """Test file_size returns 0 for non-existent file"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                mock_client.head_object.side_effect = ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
                )

                size = backend.file_size("nonexistent.png")

                self.assertEqual(size, 0)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_exists_true(self, mock_connection):
        """Test file_exists returns True for existing file"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                mock_client.head_object.return_value = {}

                exists = backend.file_exists("test.png")

                self.assertTrue(exists)
                mock_client.head_object.assert_called_once_with(
                    Bucket="test-bucket",
                    Key="media/public/test.png",
                )

    @patch("authentik.admin.files.backends.s3.connection")
    def test_file_exists_false(self, mock_connection):
        """Test file_exists returns False for non-existent file"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "backend": "s3",
                "s3.bucket_name": "test-bucket",
            }.get(key, default)

            backend = S3Backend(self.usage)

            with patch.object(backend, "client") as mock_client:
                mock_client.head_object.side_effect = ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
                )

                exists = backend.file_exists("nonexistent.png")

                self.assertFalse(exists)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_allowed_usages(self, mock_connection):
        """Test that S3Backend supports all usage types"""
        mock_connection.schema_name = "public"

        self.assertEqual(S3Backend.allowed_usages, list(Usage))

    @patch("authentik.admin.files.backends.s3.connection")
    def test_manageable(self, mock_connection):
        """Test that S3Backend is manageable"""
        mock_connection.schema_name = "public"

        self.assertTrue(S3Backend.manageable)

    @patch("authentik.admin.files.backends.s3.connection")
    def test_reports_usage(self, mock_connection):
        """Test S3Backend with REPORTS usage"""
        mock_connection.schema_name = "public"

        with patch.object(S3Backend, "get_config") as mock_config:
            mock_config.return_value = "s3"
            backend = S3Backend(Usage.REPORTS)

            self.assertEqual(backend.usage, Usage.REPORTS)
            self.assertEqual(backend.base_path, "reports/public/")
