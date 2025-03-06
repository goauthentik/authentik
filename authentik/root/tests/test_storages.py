"""Test storage backends"""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.base import ContentFile
from django.db import connection
from django.test import TestCase, override_settings

from authentik.root.storages import S3Storage


class TestS3Storage(TestCase):
    """Test S3 storage backend"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.mock_client = MagicMock()
        self.mock_bucket = MagicMock()
        self.mock_object = MagicMock()

        # Setup mock responses
        self.mock_client.Bucket.return_value = self.mock_bucket
        self.mock_bucket.Object.return_value = self.mock_object
        self.mock_bucket.name = "test-bucket"

        # Setup successful validation by default
        self.mock_client.list_buckets.return_value = {"Buckets": [{"Name": "test-bucket"}]}
        self.mock_client.head_bucket.return_value = {}

        # Mock the configuration before creating the storage instance
        self.config_patcher = patch("authentik.lib.config.CONFIG.refresh")
        self.mock_config = self.config_patcher.start()
        self.mock_config.side_effect = lambda key, default: {
            "storage.media.s3.access_key": "test-key",
            "storage.media.s3.secret_key": "test-secret",
            "storage.media.s3.bucket_name": "test-bucket",
        }.get(key, default)

        # Create test storage with mocked client
        with patch("boto3.Session") as mock_session:
            mock_session.return_value.client.return_value = self.mock_client
            self.storage = S3Storage()
            self.storage._bucket = self.mock_bucket

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        self.config_patcher.stop()

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test conflicting auth methods
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.session_profile": "test-profile",
                "storage.media.s3.access_key": "test-key",
                "storage.media.s3.secret_key": "test-secret",
            }.get(key, default)

            with self.assertRaises(ImproperlyConfigured) as cm:
                S3Storage()
            self.assertIn("should not be provided with", str(cm.exception))

        # Test missing auth configuration
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.bucket_name": "test-bucket",
            }.get(key, default)

            with self.assertRaises(ImproperlyConfigured) as cm:
                S3Storage()
            self.assertIn("Either AWS session profile or access key/secret pair", str(cm.exception))

        # Test missing bucket name
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.access_key": "test-key",
                "storage.media.s3.secret_key": "test-secret",
            }.get(key, default)

            with self.assertRaises(ImproperlyConfigured) as cm:
                S3Storage()
            self.assertIn("BUCKET_NAME must be configured", str(cm.exception))

    def test_bucket_validation(self):
        """Test bucket validation and access checks"""
        # Reset storage to test bucket validation
        self.storage._bucket = None

        # Test invalid credentials
        self.mock_client.list_buckets.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessKeyId", "Message": "Invalid access key"}},
            "list_buckets",
        )

        with self.assertRaises(ImproperlyConfigured) as cm:
            _ = self.storage.bucket
        self.assertIn("Invalid AWS credentials", str(cm.exception))

        # Reset for bucket not found test
        self.mock_client.list_buckets.side_effect = None
        self.mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "head_bucket"
        )

        with self.assertRaises(ImproperlyConfigured) as cm:
            _ = self.storage.bucket
        self.assertIn("does not exist", str(cm.exception))

        # Test permission denied
        self.mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}}, "head_bucket"
        )

        with self.assertRaises(ImproperlyConfigured) as cm:
            _ = self.storage.bucket
        self.assertIn("Permission denied accessing S3 bucket", str(cm.exception))

        # Test successful validation
        self.mock_client.head_bucket.side_effect = None
        self.storage._bucket = None
        bucket = self.storage.bucket
        self.assertEqual(bucket, self.mock_bucket)

    def test_randomize_filename(self):
        """Test filename randomization and tenant isolation"""
        original_name = "test.jpg"
        randomized = self.storage._randomize_filename(original_name)

        # Verify format: {tenant_hash}_{uuid4}{extension}
        parts = randomized.split("_")
        self.assertEqual(len(parts), 2)

        # Verify tenant hash length (8 chars)
        self.assertEqual(len(parts[0]), 8)

        # Verify extension preserved and lowercased
        self.assertTrue(parts[1].endswith(".jpg"))

        # Test with uppercase extension
        upper_name = "TEST.JPG"
        randomized_upper = self.storage._randomize_filename(upper_name)
        self.assertTrue(randomized_upper.endswith(".jpg"))

        # Verify different names for same file
        another_random = self.storage._randomize_filename(original_name)
        self.assertNotEqual(randomized, another_random)

        # Verify tenant isolation
        with patch.object(connection, "schema_name", "another_tenant"):
            different_tenant = self.storage._randomize_filename(original_name)
            self.assertNotEqual(randomized[:8], different_tenant[:8])

    def test_normalize_name(self):
        """Test S3 key normalization"""
        test_name = "test.txt"
        normalized = self.storage._normalize_name(test_name)

        # Verify tenant path is included
        self.assertIn(connection.schema_name, normalized)

        # Test with suspicious path
        with self.assertRaises(SuspiciousOperation):
            self.storage._normalize_name("../test.txt")

    def test_save_and_delete(self):
        """Test file save and delete operations"""
        test_content = b"test content"
        test_file = ContentFile(test_content, name="test.txt")

        # Mock successful upload
        self.mock_object.load.return_value = None

        # Save file
        name = self.storage._save("test.txt", test_file)

        # Verify file was uploaded with correct name format
        self.assertTrue("_" in name)
        self.assertTrue(name.endswith(".txt"))

        # Verify mapping was created
        self.assertIn("test.txt", self.storage._file_mapping)

        # Delete file
        self.storage.delete("test.txt")

        # Verify delete was called
        self.mock_object.delete.assert_called_once()

        # Verify mapping was cleaned up
        self.assertNotIn("test.txt", self.storage._file_mapping)

    def test_file_replacement(self):
        """Test file replacement and old file cleanup"""
        # Setup initial file
        initial_content = ContentFile(b"initial", name="test.txt")
        self.mock_object.load.return_value = None

        initial_name = self.storage._save("test.txt", initial_content)
        initial_normalized = self.storage._file_mapping["test.txt"]

        # Replace file
        replacement_content = ContentFile(b"replacement", name="test.txt")
        replacement_name = self.storage._save("test.txt", replacement_content)

        # Verify different random name was generated
        self.assertNotEqual(initial_name, replacement_name)

        # Verify mapping was updated
        self.assertNotEqual(initial_normalized, self.storage._file_mapping["test.txt"])

    def test_failed_upload_cleanup(self):
        """Test cleanup of failed uploads"""
        test_content = ContentFile(b"test", name="test.txt")

        # Mock failed upload verification
        self.mock_object.load.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
        )

        # Attempt save
        with self.assertRaises(ClientError):
            self.storage._save("test.txt", test_content)

        # Verify delete was attempted
        self.mock_object.delete.assert_called_once()

        # Verify no mapping was retained
        self.assertNotIn("test.txt", self.storage._file_mapping)

    @override_settings(MEDIA_URL="https://cdn.example.com/")
    def test_url_generation(self):
        """Test URL generation with custom domain"""
        self.storage.custom_domain = "cdn.example.com"

        # Mock successful file check
        self.mock_object.load.return_value = None

        # Save test file
        test_content = ContentFile(b"test", name="test.txt")
        name = self.storage._save("test.txt", test_content)

        # Generate URL
        url = self.storage.url(name)

        # Verify URL format
        self.assertTrue(url.startswith("https://cdn.example.com/"))
        self.assertTrue(url.endswith(".txt"))

        # Verify no AWS signing parameters
        self.assertNotIn("X-Amz-Algorithm", url)
        self.assertNotIn("X-Amz-Credential", url)
        self.assertNotIn("X-Amz-Date", url)
        self.assertNotIn("X-Amz-Expires", url)
        self.assertNotIn("X-Amz-SignedHeaders", url)
        self.assertNotIn("X-Amz-Signature", url)

    def test_delete_nonexistent(self):
        """Test deleting non-existent file"""
        # Mock 404 response
        self.mock_object.load.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
        )

        # Should not raise an error
        self.storage.delete("nonexistent.txt")

        # Verify delete was still attempted
        self.mock_object.delete.assert_called_once()
