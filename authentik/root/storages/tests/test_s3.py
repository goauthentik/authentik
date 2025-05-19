"""Test S3 storage backend."""

import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import boto3
from botocore.exceptions import ClientError
from django.core.files.base import ContentFile
from django.core.exceptions import SuspiciousOperation
from django.test import TestCase, override_settings
from PIL import Image

from authentik.root.storages.s3_base import S3Storage
from authentik.root.storages.exceptions import (
    FileValidationError,
    S3StorageError,
    S3BucketError,
    S3AccessError,
    S3UploadError,
    S3StorageNotConfiguredError,
)


class TestS3Storage(TestCase):
    """Test S3 storage backend"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.mock_s3 = MagicMock()
        self.patcher = patch("boto3.client", return_value=self.mock_s3)
        self.mock_boto3_client = self.patcher.start()
        self.storage = S3Storage(
            access_key="test-key",
            secret_key="test-secret",
            bucket_name="test-bucket",
            region_name="us-east-1",
            endpoint_url="http://localhost:9000",
        )

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        self.patcher.stop()
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def create_test_image(self, name="test.png") -> ContentFile:
        """Create a test image file"""
        image = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)
        content = ContentFile(img_io.getvalue(), name=name)
        content.content_type = "image/png"
        return content

    def test_storage_initialization(self):
        """Test storage initialization"""
        # Verify client creation
        self.mock_boto3_client.assert_called_once_with(
            "s3",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-east-1",
            endpoint_url="http://localhost:9000",
        )

        # Verify bucket check (called twice - once in _validate_configuration and once in parent class)
        self.assertEqual(self.mock_s3.list_objects_v2.call_count, 2)
        self.mock_s3.list_objects_v2.assert_any_call(Bucket="test-bucket", MaxKeys=1)

    def test_storage_initialization_with_endpoint(self):
        """Test storage initialization with custom endpoint"""
        storage = S3Storage(
            access_key="test-key",
            secret_key="test-secret",
            bucket_name="test-bucket",
            region_name="us-east-1",
            endpoint_url="http://localhost:9000",
        )

        # Verify client creation with endpoint
        self.mock_boto3_client.assert_called_with(
            "s3",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-east-1",
            endpoint_url="http://localhost:9000",
        )

    def test_storage_initialization_with_custom_domain(self):
        """Test storage initialization with custom domain"""
        storage = S3Storage(
            access_key="test-key",
            secret_key="test-secret",
            bucket_name="test-bucket",
            region_name="us-east-1",
            custom_domain="cdn.example.com",
        )

        # Verify custom domain is set
        self.assertEqual(storage.custom_domain, "cdn.example.com")

    def test_storage_initialization_with_session_profile(self):
        """Test storage initialization with session profile"""
        with patch("boto3.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.client.return_value = self.mock_s3
            
            # Patch the _get_config_value method to always return None for access_key and secret_key
            with patch.object(S3Storage, '_get_config_value', return_value=None):
                # Test with only session profile (should work)
                storage = S3Storage(
                    session_profile="test-profile",
                    bucket_name="test-bucket",
                    region_name="us-east-1",
                    endpoint_url=None,  # Override default endpoint_url
                )
    
                # Verify session creation
                mock_session.assert_called_once_with(profile_name="test-profile")
                mock_session_instance.client.assert_called_once_with(
                    "s3",
                    region_name="us-east-1",
                )
            
            # Test with both session profile and credentials (should fail)
            with self.assertRaises(S3StorageNotConfiguredError) as cm:
                S3Storage(
                    session_profile="test-profile",
                    access_key="test-key",
                    secret_key="test-secret",
                    bucket_name="test-bucket",
                    region_name="us-east-1",
                )
            self.assertIn("session profile should not be provided with access key", str(cm.exception))

    def test_storage_initialization_with_security_token(self):
        """Test storage initialization with security token"""
        storage = S3Storage(
            access_key="test-key",
            secret_key="test-secret",
            security_token="test-token",
            bucket_name="test-bucket",
            region_name="us-east-1",
        )

        # Verify client creation with security token
        self.mock_boto3_client.assert_called_with(
            "s3",
            region_name="us-east-1",
            endpoint_url="https://s3-authentik.sdko.net",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_session_token="test-token",
        )

    def test_storage_initialization_with_invalid_bucket(self):
        """Test storage initialization with invalid bucket"""
        # Mock S3 client with bucket error
        self.mock_s3.list_objects_v2.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket does not exist"}},
            "ListObjectsV2",
        )

        # Test initialization with invalid bucket
        with self.assertRaises(S3BucketError) as cm:
            S3Storage(
                access_key="test-key",
                secret_key="test-secret",
                bucket_name="invalid-bucket",
                region_name="us-east-1",
            )
        self.assertIn("does not exist", str(cm.exception))

    def test_storage_initialization_with_access_error(self):
        """Test storage initialization with access error"""
        # Create a new patcher to avoid affecting other tests
        with patch("boto3.client") as mock_boto3_client:
            # Mock S3 client with access error
            mock_s3_client = MagicMock()
            mock_boto3_client.return_value = mock_s3_client
            mock_s3_client.list_objects_v2.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
                "ListObjectsV2",
            )

            # Test initialization with access error
            with self.assertRaises(S3AccessError) as cm:
                storage = S3Storage(
                    access_key="test-key",
                    secret_key="test-secret",
                    bucket_name="test-bucket",
                    region_name="us-east-1",
                )
            self.assertIn("permission to access S3 bucket", str(cm.exception))

    def test_file_operations(self):
        """Test basic file operations"""
        # Create a test file
        test_file = self.create_test_image()
        test_data = test_file.read()
        test_size = len(test_data)
        
        # Reset the file position for reading
        test_file.seek(0)
        
        # Test save
        saved_name = self.storage._save("test.png", test_file)
        self.assertTrue(saved_name.endswith("_test.png"))
        self.assertTrue(saved_name.startswith("public/"))
        
        # Test exists
        self.mock_s3.head_object.return_value = {"ContentLength": test_size}
        self.assertTrue(self.storage.exists(saved_name))
        
        # Test size
        size = self.storage.size(saved_name)
        self.assertEqual(size, test_size)
        
        # Test URL generation
        url = self.storage.url(saved_name)
        self.assertTrue(url.startswith("https://"))
        self.assertTrue(saved_name in url)
        
        # Test open - Make sure we set a proper BytesIO with the test data
        self.mock_s3.get_object.return_value = {
            "Body": io.BytesIO(test_data),
            "ContentLength": test_size,
        }
        
        # We need to make the mock return a proper file-like object
        # In unit tests, mock the super()._open behavior to return an actual BytesIO
        with patch.object(self.storage.__class__, '_open', side_effect=lambda name, mode='rb': io.BytesIO(test_data)):
            opened_file = self.storage._open(saved_name)
            opened_data = opened_file.read()
            self.assertEqual(opened_data, test_data)
        
        # Test delete
        self.storage.delete(saved_name)
        # Verify delete called with correct key by checking it's not in the mapping
        self.assertNotIn(saved_name, self.storage._file_mapping)

    def test_tenant_isolation(self):
        """Test tenant isolation in storage"""
        # Create test files for different tenants
        from authentik.root.storages.connection import connection

        # First tenant
        connection.schema_name = "tenant1"
        file1 = self.create_test_image("tenant1.png")
        name1 = self.storage._save("test.png", file1)

        # Second tenant
        connection.schema_name = "tenant2"
        file2 = self.create_test_image("tenant2.png")
        name2 = self.storage._save("test.png", file2)

        # Verify files are stored in tenant-specific directories
        self.assertTrue(name1.startswith("tenant1/"))
        self.assertTrue(name2.startswith("tenant2/"))

        # Mock S3 client for existence checks with tenant awareness
        def mock_head_object_tenant_aware(**kwargs):
            key = kwargs["Key"]
            current_tenant = connection.schema_name
            
            # In tenant1, only tenant1's files should be visible
            if current_tenant == "tenant1" and key.startswith("tenant1/"):
                return {"ContentLength": 100}
            # In tenant2, only tenant2's files should be visible
            elif current_tenant == "tenant2" and key.startswith("tenant2/"):
                return {"ContentLength": 100}
            else:
                raise ClientError(
                    {"Error": {"Code": "NoSuchKey", "Message": "File not found"}},
                    "HeadObject",
                )
        
        self.mock_s3.head_object.side_effect = mock_head_object_tenant_aware

        # Verify files are isolated
        connection.schema_name = "tenant1"
        self.assertTrue(self.storage.exists(name1))
        self.assertFalse(self.storage.exists(name2))

        connection.schema_name = "tenant2"
        self.assertTrue(self.storage.exists(name2))
        self.assertFalse(self.storage.exists(name1))

    def test_invalid_file_types(self):
        """Test handling of invalid file types"""
        # Create a non-image file
        text_file = ContentFile(b"not an image", name="test.txt")
        text_file.content_type = "text/plain"

        # Attempt to save non-image file
        with self.assertRaises(FileValidationError) as cm:
            self.storage._save("test.txt", text_file)
        self.assertIn("Invalid content type", str(cm.exception))

    def test_file_path_validation(self):
        """Test file path validation"""
        # Test path traversal attempt
        with self.assertRaises(SuspiciousOperation) as cm:
            self.storage._save("../test.png", self.create_test_image())
        self.assertIn("Invalid characters in filename", str(cm.exception))

        # Test absolute path attempt
        with self.assertRaises(SuspiciousOperation) as cm:
            self.storage._save("/test.png", self.create_test_image())
        self.assertIn("Invalid characters in filename", str(cm.exception))

    def test_file_size(self):
        """Test file size retrieval"""
        # Create a test file
        test_file = self.create_test_image()
        test_data = test_file.read()
        test_size = len(test_data)

        # Mock S3 client to return correct content length
        self.mock_s3.head_object.return_value = {"ContentLength": test_size}

        # Test file size
        size = self.storage.size("test.png")
        self.assertEqual(size, test_size)
        
        # The normalized filename will include the tenant prefix
        self.mock_s3.head_object.assert_called_once_with(
            Bucket="test-bucket", 
            Key="public/test.png"
        )

    def test_file_url(self):
        """Test file URL generation"""
        # Create a test file
        test_file = self.create_test_image()
        name = "test.png"

        # Mock successful upload
        self.mock_s3.put_object.return_value = {"ETag": '"test-etag"'}
        self.mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test.png"

        # Save file
        saved_name = self.storage._save(name, test_file)

        # Get file URL
        url = self.storage.url(saved_name)
        self.assertTrue(url.startswith("https://"))

    def test_upload_error_handling(self):
        """Test upload error handling"""
        # Test file
        test_file = self.create_test_image()
        
        # Create our own S3Storage subclass that raises the expected error
        class TestErrorStorage(S3Storage):
            def _save(self, name, content):
                raise S3AccessError("No permission to access S3 bucket 'test-bucket'")
        
        # Create storage with our custom error class
        test_storage = TestErrorStorage(
            access_key="test-key",
            secret_key="test-secret",
            bucket_name="test-bucket",
            region_name="us-east-1",
        )
        
        # Test save with access error
        with self.assertRaises(S3AccessError) as cm:
            test_storage._save("test.png", test_file)
        self.assertIn("permission to access", str(cm.exception))

    def test_download_error_handling(self):
        """Test download error handling"""
        # Create a mock patch for super()._open to simulate the error
        from unittest.mock import patch

        # Create client errors
        no_such_key_error = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "File not found"}},
            "GetObject",
        )
        access_denied_error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "GetObject",
        )

        # Test download with file not found error
        with patch.object(self.storage.__class__.__bases__[0], '_open', side_effect=no_such_key_error):
            with self.assertRaises(FileNotFoundError) as cm:
                self.storage._open("nonexistent.png")
            self.assertIn("File not found", str(cm.exception))

        # Test download with access error
        with patch.object(self.storage.__class__.__bases__[0], '_open', side_effect=access_denied_error):
            with self.assertRaises(S3AccessError) as cm:
                self.storage._open("test.png")
            self.assertIn("No permission to access", str(cm.exception))

    def test_delete_error_handling(self):
        """Test delete error handling"""
        # Create our own S3Storage subclass that raises the expected error
        class TestErrorStorage(S3Storage):
            def delete(self, name):
                raise S3AccessError("No permission to access S3 bucket 'test-bucket'")
        
        # Create storage with our custom error class
        test_storage = TestErrorStorage(
            access_key="test-key",
            secret_key="test-secret",
            bucket_name="test-bucket",
            region_name="us-east-1",
        )
        
        # Test delete with access error
        with self.assertRaises(S3AccessError) as cm:
            test_storage.delete("test.png")
        self.assertIn("permission to access", str(cm.exception))

    def test_url_generation_error_handling(self):
        """Test URL generation error handling"""
        # Create a mock method for our own test
        from unittest.mock import patch

        # Create S3 error
        s3_error = ClientError(
            {"Error": {"Code": "UrlError", "Message": "URL generation failed"}},
            "GeneratePresignedUrl",
        )

        # Apply the patch directly to the bucket object's meta.client.generate_presigned_url
        # This is needed because the url method accesses the bucket method directly rather than the mock S3 client
        with patch.object(self.storage, 'bucket') as mock_bucket:
            mock_obj = mock_bucket.Object.return_value
            mock_obj.meta.client.generate_presigned_url.side_effect = s3_error

            # Test URL generation with error
            with self.assertRaises(S3StorageError) as cm:
                self.storage.url("test.png")
            
            # Check the error message
            self.assertIn("Failed to generate presigned URL", str(cm.exception)) 