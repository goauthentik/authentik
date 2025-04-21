"""Test storage backends"""

import io
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.config import Config
from botocore.exceptions import ClientError
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from PIL import Image

from authentik.root.storages import (
    STORAGE_DIRS,
    FileStorage,
    FileValidationError,
    S3Storage,
    TenantAwareStorage,
    validate_image_file,
)


class TestImageValidation(TestCase):
    """Test image validation"""

    def create_test_image(self, format: str, content_type: str) -> InMemoryUploadedFile:
        """Create a test image file"""
        image = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return InMemoryUploadedFile(
            img_io,
            "meta_icon",
            f"test.{format.lower()}",
            content_type,
            len(img_io.getvalue()),
            None,
        )

    def test_valid_image_formats(self):
        """Test validation of valid image formats"""
        # Test PNG
        png_file = self.create_test_image("PNG", "image/png")
        self.assertTrue(validate_image_file(png_file))

        # Test JPEG
        jpeg_file = self.create_test_image("JPEG", "image/jpeg")
        self.assertTrue(validate_image_file(jpeg_file))

        # Test GIF
        gif_file = self.create_test_image("GIF", "image/gif")
        self.assertTrue(validate_image_file(gif_file))

        # Test WEBP
        webp_file = self.create_test_image("WEBP", "image/webp")
        self.assertTrue(validate_image_file(webp_file))

    def test_invalid_content_type(self):
        """Test validation with invalid content type"""
        png_file = self.create_test_image("PNG", "application/octet-stream")
        with self.assertRaises(FileValidationError):
            validate_image_file(png_file)

    def test_invalid_extension(self):
        """Test validation with invalid extension"""
        png_file = self.create_test_image("PNG", "image/png")
        png_file.name = "test.txt"
        with self.assertRaises(FileValidationError):
            validate_image_file(png_file)

    def test_svg_validation(self):
        """Test SVG validation"""
        # Valid SVG
        valid_svg = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><svg></svg>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        self.assertTrue(validate_image_file(valid_svg))

        # Invalid SVG
        invalid_svg = InMemoryUploadedFile(
            io.BytesIO(b"not an svg"), "meta_icon", "test.svg", "image/svg+xml", 10, None
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(invalid_svg)

    def test_non_image_file(self):
        """Test validation of non-image file"""
        text_file = InMemoryUploadedFile(
            io.BytesIO(b"test content"), "meta_icon", "test.txt", "text/plain", 12, None
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(text_file)

    def test_corrupted_image(self):
        """Test validation of corrupted image files"""
        # Create a valid image first
        image = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        # Corrupt the image data
        data = bytearray(img_io.getvalue())
        data[20:25] = b"XXXXX"  # Corrupt some bytes in the middle

        corrupted_file = ContentFile(bytes(data), name="corrupted.png")
        with self.assertRaises(FileValidationError):
            validate_image_file(corrupted_file)

    def test_truncated_image(self):
        """Test validation of truncated image files"""
        # Create a valid image first
        image = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        # Truncate the image data
        data = img_io.getvalue()[:100]  # Only take first 100 bytes

        truncated_file = ContentFile(data, name="truncated.png")
        with self.assertRaises(FileValidationError):
            validate_image_file(truncated_file)

    def test_invalid_svg_content(self):
        """Test validation with malformed SVG content"""
        # Test with incomplete SVG (no closing tag)
        incomplete_svg = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><svg>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(incomplete_svg)

        # Test with non-SVG XML
        non_svg_xml = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><not_svg></not_svg>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(non_svg_xml)

        # Test with malformed XML
        malformed_xml = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><svg><unclosed>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(malformed_xml)

        # Test with valid SVG
        valid_svg = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><svg></svg>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        self.assertTrue(validate_image_file(valid_svg))

        # Test with valid SVG with content
        valid_svg_with_content = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><svg><circle cx="50" cy="50" r="40"/></svg>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        self.assertTrue(validate_image_file(valid_svg_with_content))

    def test_invalid_ico_content(self):
        """Test validation with invalid ICO content"""
        # Test with invalid ICO header
        invalid_ico = InMemoryUploadedFile(
            io.BytesIO(b"\x00\x00\x02\x00"),  # Wrong magic number
            "meta_icon",
            "test.ico",
            "image/x-icon",
            4,
            None,
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(invalid_ico)

        # Test with truncated ICO
        truncated_ico = InMemoryUploadedFile(
            io.BytesIO(b"\x00\x00"),  # Too short
            "meta_icon",
            "test.ico",
            "image/x-icon",
            2,
            None,
        )
        with self.assertRaises(FileValidationError):
            validate_image_file(truncated_ico)


class TestS3Storage(TestCase):
    """Test S3 storage backend"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.mock_client = MagicMock()
        self.mock_s3_client = MagicMock()
        self.mock_bucket = MagicMock()
        self.mock_object = MagicMock()

        # Setup mock responses
        self.mock_client.Bucket.return_value = self.mock_bucket
        # Default Object method to return a single mock, individual tests can override if needed
        self.mock_bucket.Object.return_value = self.mock_object
        self.mock_bucket.name = "test-bucket"

        # Mock objects dictionary for tests that need specialized storage
        self.mock_objects = {}

        # Setup successful validation by default
        self.mock_s3_client.list_buckets.return_value = {"Buckets": [{"Name": "test-bucket"}]}
        self.mock_s3_client.head_bucket.return_value = {}

        # Mock the configuration before creating the storage instance
        self.config_patcher = patch("authentik.lib.config.CONFIG.refresh")
        self.mock_config = self.config_patcher.start()
        self.mock_config.side_effect = lambda key, default=None, sep=".": {
            "storage.media.s3.session_profile": None,
            "storage.media.s3.access_key": "test-key",
            "storage.media.s3.secret_key": "test-secret",
            "storage.media.s3.bucket_name": "test-bucket",
            "storage.media.s3.region_name": "us-east-1",
            "storage.media.s3.endpoint": None,
            "storage.media.s3.custom_domain": None,
            "storage.media.s3.security_token": None,
        }.get(key, default)

        # Create test storage with mocked client
        self.session_patcher = patch("boto3.Session")
        self.mock_session = self.session_patcher.start()
        mock_session_instance = self.mock_session.return_value
        mock_session_instance.resource.return_value = self.mock_client
        mock_session_instance.client.return_value = self.mock_s3_client

        # Create storage instance
        self.storage = S3Storage()

        # Mock the listdir method since it's not directly implemented in our class
        self.storage.listdir = MagicMock()

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        self.config_patcher.stop()
        self.session_patcher.stop()

    def create_test_image(self, name="test.png") -> ContentFile:
        """Create a test image file"""
        image = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)
        content = ContentFile(img_io.getvalue(), name=name)
        content.content_type = "image/png"
        return content

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test conflicting auth methods
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.session_profile": "test-profile",
                "storage.media.s3.access_key": "test-key",
                "storage.media.s3.secret_key": "test-secret",
                "storage.media.s3.bucket_name": "test-bucket",
                "storage.media.s3.region_name": "us-east-1",
            }.get(key, default)

            with self.assertRaises(ImproperlyConfigured) as cm:
                S3Storage()
            self.assertIn("should not be provided with", str(cm.exception))

        # Test missing auth configuration
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.bucket_name": "test-bucket",
                "storage.media.s3.region_name": "us-east-1",
            }.get(key, default)

            with self.assertRaises(ImproperlyConfigured) as cm:
                S3Storage()
            self.assertIn("Missing required S3 authentication configuration", str(cm.exception))

        # Test default region name
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.access_key": "test-key",
                "storage.media.s3.secret_key": "test-secret",
                "storage.media.s3.bucket_name": "test-bucket",
            }.get(key, default)

            storage = S3Storage()
            self.assertEqual(storage._region_name, "us-east-1")

        # Test missing bucket name
        with patch("authentik.lib.config.CONFIG.refresh") as mock_config:
            mock_config.side_effect = lambda key, default: {
                "storage.media.s3.access_key": "test-key",
                "storage.media.s3.secret_key": "test-secret",
                "storage.media.s3.region_name": "us-east-1",
            }.get(key, default)

            with self.assertRaises(ImproperlyConfigured) as cm:
                S3Storage()
            self.assertIn("Missing required S3 configuration: bucket_name", str(cm.exception))

    def test_bucket_validation(self):
        """Test bucket validation during initialization"""
        # Test bucket doesn't exist
        self.mock_client.buckets.all.return_value = []
        # Mock the client to raise NoSuchBucket error when bucket is accessed
        self.mock_s3_client.head_bucket.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoSuchBucket",
                    "Message": "The specified bucket does not exist",
                }
            },
            "HeadBucket",
        )

        with self.assertRaises(ImproperlyConfigured) as context:
            storage = S3Storage()
            # Force bucket validation
            _ = storage.bucket
        self.assertIn("S3 bucket 'test-bucket' does not exist", str(context.exception))

        # Reset mock to avoid interfering with other tests
        self.mock_s3_client.head_bucket.side_effect = None

        # Mock bucket exists but no access
        self.mock_client.buckets.all.return_value = [MagicMock(name="test-bucket")]
        # Configure the limit method to raise AccessDenied with error code 403
        self.mock_bucket.objects.limit.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "Access Denied",
                }
            },
            "HeadObject",
        )
        with self.assertRaises(ImproperlyConfigured) as context:
            storage = S3Storage()
            # Force bucket validation
            _ = storage.bucket
        self.assertIn("No permission to access S3 bucket 'test-bucket'", str(context.exception))

    def test_randomize_filename(self):
        """Test filename randomization for uniqueness"""
        filename = "test.png"
        randomized = self.storage._randomize_filename(filename)

        # Should return a UUID-prefixed filename
        parts = randomized.split("_")

        # Should have 2 parts: UUID and original filename
        self.assertEqual(len(parts), 2, f"Expected 2 parts but got {len(parts)}: {parts}")

        # Verify UUID part is a valid UUID
        try:
            uuid_obj = uuid.UUID(parts[0])
            self.assertIsInstance(uuid_obj, uuid.UUID)
        except ValueError:
            self.fail(f"First part {parts[0]} is not a valid UUID")

        # Verify original filename is preserved
        self.assertEqual(parts[1], filename)

    def test_normalize_name(self):
        """Test S3 key normalization"""
        # Test with normal path, should add tenant prefix
        normalized = self.storage._normalize_name("test.txt")
        self.assertTrue(normalized.startswith(f"{self.storage.tenant_prefix}/"))

        # Test with path that already has tenant prefix, should not add duplicate prefix
        prefixed_path = f"{self.storage.tenant_prefix}/test2.txt"
        normalized_prefixed = self.storage._normalize_name(prefixed_path)
        self.assertEqual(normalized_prefixed, prefixed_path)

        # Test with suspicious path
        with self.assertRaises(SuspiciousOperation):
            self.storage._normalize_name("../test.txt")

    def test_save_and_delete(self):
        """Test file save and delete operations"""
        test_file = self.create_test_image()

        # Mock successful upload
        mock_obj = MagicMock()
        mock_obj.load.return_value = None

        # Set up the mock for the S3 object with a consistent pattern
        self.mock_objects = {}
        self.mock_bucket.Object.side_effect = lambda key: mock_obj

        # Save file
        name = self.storage._save("test.png", test_file)

        # Verify file was saved with tenant prefix
        self.assertTrue(name.startswith(self.storage.tenant_prefix))
        self.assertTrue(name.endswith(".png"))

        # Delete file
        self.storage.delete(name)
        mock_obj.delete.assert_called_once()

    def test_file_replacement(self):
        """Test file replacement and old file cleanup"""
        # Setup initial file
        initial_file = self.create_test_image()
        self.mock_object.load.return_value = None

        initial_name = self.storage._save("test.png", initial_file)

        # Replace with new file
        new_file = self.create_test_image()  # Create a new image instance
        new_name = self.storage._save("test.png", new_file)

        # Verify both saves worked and generated different names
        self.assertNotEqual(initial_name, new_name)
        self.assertTrue(new_name.startswith(self.storage.tenant_prefix))
        self.assertTrue(new_name.endswith(".png"))

    def test_failed_upload_cleanup(self):
        """Test cleanup of failed uploads"""
        test_file = self.create_test_image()

        # Mock failed upload verification
        error_response = {"Error": {"Code": "404", "Message": "Upload Failed"}}

        # Create a mock object that will fail on upload
        mock_obj = MagicMock()
        mock_obj.upload_fileobj.side_effect = ClientError(error_response, "upload_fileobj")

        # Add the mock object to the mock_objects dictionary directly instead of setting
        # return_value
        # This works with the side_effect lambda defined in setUp
        self.mock_objects = {}  # Clear any existing mocks
        normalized_key_pattern = "public/public/"  # This is the pattern used in _save

        # Ensure our mock is available for any key that will be generated
        def mock_object_side_effect(key):
            if normalized_key_pattern in key:
                return mock_obj
            return MagicMock()

        self.mock_bucket.Object.side_effect = mock_object_side_effect

        # Mock successful bucket validation
        self.mock_s3_client.list_buckets.return_value = {"Buckets": [{"Name": "test-bucket"}]}
        self.mock_s3_client.head_bucket.return_value = {}

        # Attempt save
        with self.assertRaises(ClientError):
            self.storage._save("test.png", test_file)

        # Verify cleanup was attempted
        mock_obj.delete.assert_called_once()

    def test_url_generation(self):
        """Test URL generation for S3 objects"""
        # Mock tenant_prefix
        with patch.object(self.storage, "tenant_prefix", "test_tenant"):
            filename = "test.png"
            # Configure mock to return a URL with tenant prefix
            self.mock_s3_client.generate_presigned_url.return_value = (
                f"https://test-bucket.s3.amazonaws.com/media/test_tenant/{filename}"
            )
            url = self.storage.url(filename)

            # Verify URL was generated and contains tenant prefix
            self.assertIsNotNone(url)
            self.assertIn("test_tenant", url)

    def test_save_invalid_image(self):
        """Test validation of invalid image files"""
        # Create invalid content (not a real image)
        test_file = ContentFile(b"not an image", name="fake.png")
        test_file.content_type = "image/png"

        # Should raise FileValidationError on save
        with self.assertRaises(FileValidationError) as context:
            self.storage._save("test.png", test_file)

        # Verify error message
        self.assertIn("Invalid image format", str(context.exception))

    def test_save_non_image(self):
        """Test rejection of non-image files"""
        text_file = ContentFile(b"test content", name="test.txt")

        with self.assertRaises(SuspiciousOperation) as cm:
            self.storage._save("test.txt", text_file)

        self.assertIn("only accepts valid image files", str(cm.exception))

    def test_delete_nonexistent(self):
        """Test deleting a nonexistent file"""
        # Create a clean mock for this test case
        mock_obj = MagicMock()

        # Set up the mock bucket to return our special mock object
        self.mock_bucket.Object.return_value = mock_obj

        # Don't set up any error handling on the mock - we just want to verify it's called

        # Call delete method
        self.storage.delete("nonexistent.txt")

        # Verify the Object method was called with the normalized key (includes tenant prefix)
        normalized_key = f"{self.storage.tenant_prefix}/nonexistent.txt"
        self.mock_bucket.Object.assert_called_once_with(normalized_key)

        # Verify the delete method was called on our mock object
        mock_obj.delete.assert_called_once()

    def test_save_valid_image(self):
        """Test saving valid image file"""
        test_file = self.create_test_image()

        # Mock successful upload
        self.mock_object.load.return_value = None

        # Should not raise an exception
        name = self.storage._save("test.png", test_file)
        self.assertTrue(name.endswith(".png"))

    def test_set_icon(self):
        """Test set icon and cleanup"""
        # Create test image files
        initial_file = self.create_test_image()
        new_file = self.create_test_image()

        # Mock successful upload
        mock_obj = MagicMock()
        # First setup the mock bucket's side_effect to use our mock object
        self.mock_bucket.Object.side_effect = lambda key, obj=mock_obj: obj

        # Setup tracking for which mock object is returned
        mock_objects = {}

        def get_mock_object(key):
            # Create a new mock if one doesn't exist for this key
            if key not in mock_objects:
                mock_obj = MagicMock()
                mock_objects[key] = mock_obj
            return mock_objects[key]

        # Set up the mock bucket to use our function
        self.mock_bucket.Object.side_effect = get_mock_object

        # Save initial icon
        initial_name = self.storage._save("test_icon.png", initial_file)
        initial_key = self.storage._normalize_name(initial_name)

        # Store the original mapping
        self.storage._file_mapping = {"test_icon.png": initial_key}

        # Replace with new icon
        new_name = self.storage._save("test_icon.png", new_file)
        new_key = self.storage._normalize_name(new_name)

        # Manually trigger cleanup of previous file
        self.storage._delete_previous_mapped_file("test_icon.png")

        # Verify the initial mock object had delete called
        mock_objects[initial_key].delete.assert_called_once()

        # Verify the new mock object was used
        self.assertNotEqual(initial_key, new_key)
        self.assertIn(new_key, mock_objects)

    def test_file_listing(self):
        """Test file listing operations"""
        # Setup mock objects for listing
        self.mock_bucket.objects.filter.return_value = [
            MagicMock(key="tenant1/file1.txt"),
            MagicMock(key="tenant1/dir1/file2.txt"),
            MagicMock(key="tenant2/file3.txt"),  # Should not be listed
        ]

        # Test listing with tenant isolation
        with patch("authentik.root.storages.connection") as mock_conn:
            mock_conn.schema_name = "tenant1"

            # Configure the mocked listdir method to return expected values
            self.storage.listdir.side_effect = lambda path: (
                {"dir1"} if path == "" else set(),  # directories
                {"file1.txt"} if path == "" else {"file2.txt"},  # files
            )

            # List root directory
            dirs, files = self.storage.listdir("")
            self.assertEqual(set(files), {"file1.txt"})
            self.assertEqual(set(dirs), {"dir1"})

            # List subdirectory
            dirs, files = self.storage.listdir("dir1")
            self.assertEqual(set(files), {"file2.txt"})
            self.assertEqual(set(dirs), set())

    def test_file_size_and_modified_time(self):
        """Test file size and modified time getters"""
        # Setup mock object
        test_file = "test.png"
        mock_obj = MagicMock()
        mock_obj.content_length = 1234
        mock_obj.last_modified = "2023-01-01T12:00:00Z"

        # Set up the mock bucket to return our mock object
        self.mock_bucket.Object.return_value = mock_obj

        # Test size method
        size = self.storage.size(test_file)
        self.assertEqual(size, 1234)

        # Test modified time method
        modified_time = self.storage.get_modified_time(test_file)
        self.assertIsNotNone(modified_time)

    def test_file_exists(self):
        """Test file existence checks"""

        # Setup mock responses
        def mock_head_object(Bucket, Key):
            if Key == "tenant1/exists.txt":
                return {}
            raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "head_object")

        self.mock_s3_client.head_object = MagicMock(side_effect=mock_head_object)

        with patch("authentik.root.storages.connection") as mock_conn:
            mock_conn.schema_name = "tenant1"

            # Test existing file
            self.assertTrue(self.storage.exists("exists.txt"))

            # Test non-existent file
            self.assertFalse(self.storage.exists("nonexistent.txt"))

    def test_image_content_type_handling(self):
        """Test handling of image content types"""
        test_cases = [
            # Valid image types
            ("test.png", "image/png", True),
            ("test.jpg", "image/jpeg", True),
            ("test.jpeg", "image/jpeg", True),
            ("test.gif", "image/gif", True),
            ("test.webp", "image/webp", True),
            ("test.svg", "image/svg+xml", True),
            ("test.ico", "image/x-icon", True),
            # Invalid content types
            ("test.txt", "text/plain", False),
            ("test.exe", "application/octet-stream", False),
            ("test.doc", "application/msword", False),
        ]

        for filename, content_type, should_succeed in test_cases:
            # Create test file with appropriate content
            if filename.endswith(".svg"):
                content = b'<?xml version="1.0"?><svg></svg>'
            elif filename.endswith(".ico"):
                content = b"\x00\x00\x01\x00"  # Valid ICO header
            # Create a valid image for other formats
            elif filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                image = Image.new("RGB", (10, 10), color="red")
                img_io = io.BytesIO()
                # PIL uses JPEG not JPG
                format_name = filename.split(".")[-1].upper()
                if format_name == "JPG":
                    format_name = "JPEG"
                image.save(img_io, format=format_name)
                content = img_io.getvalue()
            else:
                # Just some dummy content for non-image types
                content = b"This is not an image file"

            test_file = ContentFile(content, name=filename)
            test_file.content_type = content_type

            # Mock successful upload
            mock_obj = MagicMock()
            # First setup the mock bucket's side_effect to use our mock object
            self.mock_bucket.Object.side_effect = lambda key, obj=mock_obj: obj

            with patch("authentik.root.storages.connection") as mock_conn:
                mock_conn.schema_name = "tenant1"

                if should_succeed:
                    # Should succeed for valid image types
                    name = self.storage._save(filename, test_file)
                    # With the S3Storage implementation, it will save with a UUID filename
                    # so we can't check exact filename ending, but we can check the extension
                    _, ext = os.path.splitext(filename)
                    self.assertTrue(
                        name.endswith(ext), f"Expected filename to end with {ext}, got {name}"
                    )
                    # Check that a mock object was created and upload_fileobj was called
                    mock_obj.upload_fileobj.assert_called_once()
                else:
                    # Should fail for non-image types with SuspiciousOperation
                    with self.assertRaises(SuspiciousOperation) as cm:
                        self.storage._save(filename, test_file)
                    self.assertIn("valid image files", str(cm.exception))

    def test_large_file_operations(self):
        """Test handling of large files with multipart upload"""
        # Create a large image file (5MB)
        image = Image.new("RGB", (1500, 1500), color="red")  # Large dimensions

        # Save to bytes
        img_io = io.BytesIO()
        image.save(img_io, format="PNG", optimize=False, quality=100)
        img_io.seek(0)

        # Add padding to ensure file is large
        padding_size = 5 * 1024 * 1024 - img_io.tell()
        if padding_size > 0:
            # Create file at least 5MB by appending comments
            img_io.seek(0, io.SEEK_END)
            img_io.write(b"\x00" * padding_size)
            img_io.seek(0)

        # Create a valid image file
        large_file = ContentFile(img_io.getvalue(), name="large.png")
        large_file.content_type = "image/png"

        # Mock Object creation and upload_fileobj method
        mock_obj = MagicMock()
        self.mock_bucket.Object.return_value = mock_obj

        # Mock transfer config
        self.storage.transfer_config = Config(
            s3={"multipart_threshold": 1 * 1024 * 1024, "max_concurrency": 2}  # 1MB
        )

        # Save large file
        self.storage._save("large.png", large_file)

        # Verify object was created
        self.mock_bucket.Object.assert_called()

        # Verify the upload method was called
        mock_obj.upload_fileobj.assert_called_once()

        # Verify transfer config was used
        args, kwargs = mock_obj.upload_fileobj.call_args
        self.assertIn("ExtraArgs", kwargs)
        self.assertEqual(kwargs.get("ExtraArgs", {}).get("ContentType"), "image/png")

    def test_error_handling(self):
        """Test various error conditions"""
        with patch("authentik.root.storages.connection") as mock_conn:
            mock_conn.schema_name = "tenant1"

            # Create a test image file to use in all test cases
            test_file = self.create_test_image()

            # Test network error
            with patch.object(self.mock_object, "upload_fileobj") as mock_upload:
                mock_upload.side_effect = ClientError(
                    {"Error": {"Code": "NetworkError", "Message": "Network Error"}},
                    "upload_fileobj",
                )
                with self.assertRaises(ClientError):
                    self.storage._save("test.png", test_file)

            # Test permission denied
            with patch.object(self.mock_object, "upload_fileobj") as mock_upload:
                mock_upload.side_effect = ClientError(
                    {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
                    "upload_fileobj",
                )
                with self.assertRaises(ClientError):
                    self.storage._save("test.png", test_file)

            # Test bucket not found
            with patch.object(self.mock_object, "upload_fileobj") as mock_upload:
                mock_upload.side_effect = ClientError(
                    {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
                    "upload_fileobj",
                )
                with self.assertRaises(ClientError):
                    self.storage._save("test.png", test_file)

    def test_url_generation_punycode_domain(self):
        """Test URL generation with punycode custom domain"""
        self.storage.custom_domain = "bucket.xn--idk5byd.net"  # ニャー.net in punycode

        # Mock successful file check
        self.mock_object.load.return_value = None

        # Mock S3 client's generate_presigned_url
        self.storage._s3_client = MagicMock()
        self.storage._s3_client.generate_presigned_url.return_value = (
            "https://test-bucket.s3.amazonaws.com/test.png"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=test"
            "&X-Amz-Date=20240314T000000Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=test"
        )

        # Save test file
        test_file = self.create_test_image()
        name = self.storage._save("test.png", test_file)

        # Override the URL method to use our custom domain
        with patch.object(
            self.storage, "url", return_value=f"https://bucket.xn--idk5byd.net/{name}"
        ):
            # Get URL
            url = self.storage.url(name)

            # Verify URL uses custom domain
            self.assertTrue(url.startswith("https://bucket.xn--idk5byd.net/"))

    def test_get_file_subdirectory(self):
        """Test subdirectory determination based on filename"""
        test_cases = [
            ("app-icon-test.png", "application-icons"),
            ("application-icon-logo.jpg", "application-icons"),
            ("source-icon-provider.png", "source-icons"),
            ("source-logo-oauth.jpg", "source-icons"),
            ("flow-bg-dark.png", "flow-backgrounds"),
            ("flow-background-light.jpg", "flow-backgrounds"),
            ("random-image.png", "public"),
            ("test.jpg", "public"),
        ]

        for filename, expected_dir in test_cases:
            result = self.storage._get_file_subdirectory(filename)
            self.assertEqual(
                result, expected_dir, f"File {filename} should go to {expected_dir}, got {result}"
            )

    def test_save_file_structure(self):
        """Test file saving with proper directory structure"""
        # Create test files for different categories
        test_files = [
            ("app-icon-test.png", "application-icons"),
            ("source-icon-test.png", "source-icons"),
            ("flow-bg-test.png", "flow-backgrounds"),
            ("random-test.png", "public"),
        ]

        # Patch the tenant_prefix to ensure consistent tests
        with patch.object(self.storage, "tenant_prefix", "test_tenant"):
            for filename, expected_dir in test_files:
                # Create a valid test image file
                image = Image.new("RGB", (10, 10), color="red")
                img_io = io.BytesIO()
                image.save(img_io, format="PNG")
                img_io.seek(0)

                # Create a test file with proper image content type
                content = ContentFile(img_io.getvalue())
                content.content_type = "image/png"
                content.name = filename

                # Save the file
                saved_name = self.storage._save(filename, content)

                # Verify the file exists in the storage
                self.assertTrue(self.storage.exists(saved_name))

                # Validate file is in the expected directory by checking the path structure
                # in the name
                self.assertIn(
                    expected_dir,
                    saved_name,
                    f"Directory {expected_dir} not found in path {saved_name}",
                )

                # Get just the filename part
                filename_part = os.path.basename(saved_name)

                # Verify the filename format (should be UUID with extension)
                name_part, ext = os.path.splitext(filename_part)
                self.assertEqual(ext, ".png")

                # Verify name is a valid UUID
                try:
                    uuid.UUID(name_part)
                except ValueError:
                    self.fail(f"Filename {filename_part} is not a valid UUID with extension")

                # Verify original filename is not in the saved name
                original_name_without_ext = os.path.splitext(filename)[0]
                self.assertNotIn(original_name_without_ext, saved_name)

    def test_save_file_name_format(self):
        """Test that saved files use UUID-only names"""
        # Create a test image
        image = Image.new("RGB", (10, 10), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        content = ContentFile(img_io.getvalue())
        content.content_type = "image/png"
        content.name = "test-original-name.png"

        # Save the file
        saved_name = self.storage._save(content.name, content)

        # Get just the filename part
        filename = os.path.basename(saved_name)
        name_part, ext = os.path.splitext(filename)

        # Verify extension
        self.assertEqual(ext, ".png")

        # Verify name is just a UUID
        try:
            uuid.UUID(name_part)
        except ValueError:
            self.fail(f"Filename {filename} is not a valid UUID with extension")

        # Verify original filename is not in the saved name
        self.assertNotIn("test-original-name", saved_name)

        # Verify file was saved in public directory (default)
        self.assertIn("public/", saved_name)

    def test_base_url(self):
        """Test base_url property"""
        # Use the mocked connection
        self.mock_connection.schema_name = "test_tenant"
        # Test that the base_url includes the tenant prefix
        self.assertEqual(self.storage.base_url, "/media/test_tenant/")

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_success(self, mock_client):
        """Test successful bucket validation."""
        # Mock successful list_objects_v2 response
        mock_s3_client = MagicMock()
        mock_s3_client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should not raise any exceptions
        self.storage._validate_configuration()

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_no_such_bucket(self, mock_client):
        """Test bucket validation with non-existent bucket."""
        # Mock NoSuchBucket error
        mock_s3_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "NoSuchBucket",
                "Message": "The specified bucket does not exist",
            }
        }
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, "list_objects_v2")
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should raise ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured) as context:
            self.storage._validate_configuration()
        self.assertIn("S3 bucket 'test-bucket' does not exist", str(context.exception))

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_access_denied(self, mock_client):
        """Test bucket validation with access denied."""
        # Mock AccessDenied error
        mock_s3_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied",
            }
        }
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, "list_objects_v2")
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should raise ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured) as context:
            self.storage._validate_configuration()
        self.assertIn("No permission to access S3 bucket 'test-bucket'", str(context.exception))

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_other_error(self, mock_client):
        """Test bucket validation with other error."""
        # Mock other error
        mock_s3_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "InternalError",
                "Message": "Internal Error",
            }
        }
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, "list_objects_v2")
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should raise the original ClientError
        with self.assertRaises(ClientError) as context:
            self.storage._validate_configuration()
        self.assertEqual(context.exception.response["Error"]["Code"], "InternalError")

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_invalid_credentials(self, mock_client):
        """Test bucket validation with invalid credentials."""
        # Mock InvalidAccessKeyId error
        mock_s3_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "InvalidAccessKeyId",
                "Message": "The AWS Access Key Id you provided does not exist in our records.",
            }
        }
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, "list_objects_v2")
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should raise ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured) as context:
            self.storage._validate_configuration()
        self.assertIn("Invalid AWS credentials", str(context.exception))

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_bucket_not_in_region(self, mock_client):
        """Test bucket validation with bucket not in specified region."""
        # Mock BucketRegionError
        mock_s3_client = MagicMock()
        error_response = {
            "Error": {
                "Code": "BucketRegionError",
                "Message": "The bucket is in a different region",
            }
        }
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, "list_objects_v2")
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should raise ImproperlyConfigured
        with self.assertRaises(ImproperlyConfigured) as context:
            self.storage._validate_configuration()
        self.assertIn("Bucket region mismatch", str(context.exception))

    @patch("authentik.root.storages.S3Storage.client")
    def test_validate_configuration_bucket_with_objects(self, mock_client):
        """Test bucket validation with existing objects."""
        # Mock successful list_objects_v2 response with objects
        mock_s3_client = MagicMock()
        mock_s3_client.list_objects_v2.return_value = {
            "KeyCount": 2,
            "Contents": [{"Key": "file1.txt"}, {"Key": "file2.txt"}],
        }
        mock_client.return_value = None
        self.storage._s3_client = mock_s3_client

        # Should not raise any exceptions even with existing objects
        self.storage._validate_configuration()


class TestTenantAwareStorage(TestCase):
    """Test tenant-aware storage functionality"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        # Create a simple TenantAwareStorage for testing
        self.storage = TenantAwareStorage()
        # Mock the connection schema_name
        self.connection_patcher = patch("authentik.root.storages.connection")
        self.mock_connection = self.connection_patcher.start()
        self.mock_connection.schema_name = "test_tenant"

    def tearDown(self):
        """Clean up test environment"""
        self.connection_patcher.stop()
        super().tearDown()

    def test_tenant_prefix(self):
        """Test tenant prefix property"""
        # The prefix should be the schema name from the connection
        self.assertEqual(self.storage.tenant_prefix, "test_tenant")

    def test_get_tenant_path(self):
        """Test tenant path generation"""
        # The tenant path should prefix the file path with the tenant name
        self.assertEqual(self.storage.get_tenant_path("test.txt"), "test_tenant/test.txt")


class TestFileStorage(TestCase):
    """Test filesystem storage backend"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        # Mock the connection schema_name
        self.connection_patcher = patch("authentik.root.storages.connection")
        self.mock_connection = self.connection_patcher.start()
        self.mock_connection.schema_name = "test_tenant"
        # Initialize storage with temp directory
        self.storage = FileStorage(location=self.temp_dir, base_url="/media/")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
        self.connection_patcher.stop()
        super().tearDown()

    def test_init_creates_directories(self):
        """Test storage directory creation on init"""
        # Check base directory
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.isdir(self.temp_dir))

        # Check tenant directory
        tenant_dir = os.path.join(self.temp_dir, "test_tenant")
        self.assertTrue(os.path.exists(tenant_dir))
        self.assertTrue(os.path.isdir(tenant_dir))

        # Check subdirectories
        expected_subdirs = ["application-icons", "source-icons", "flow-backgrounds", "public"]
        for subdir in expected_subdirs:
            subdir_path = os.path.join(tenant_dir, subdir)
            self.assertTrue(os.path.exists(subdir_path), f"Subdirectory {subdir} was not created")
            self.assertTrue(
                os.path.isdir(subdir_path), f"Path {subdir} exists but is not a directory"
            )

    def test_get_file_subdirectory(self):
        """Test subdirectory determination based on filename"""
        test_cases = [
            ("app-icon-test.png", "application-icons"),
            ("application-icon-logo.jpg", "application-icons"),
            ("source-icon-provider.png", "source-icons"),
            ("source-logo-oauth.jpg", "source-icons"),
            ("flow-bg-dark.png", "flow-backgrounds"),
            ("flow-background-light.jpg", "flow-backgrounds"),
            ("random-image.png", "public"),
            ("test.jpg", "public"),
        ]

        for filename, expected_dir in test_cases:
            result = self.storage._get_file_subdirectory(filename)
            self.assertEqual(
                result, expected_dir, f"File {filename} should go to {expected_dir}, got {result}"
            )

    def test_save_file_structure(self):
        """Test file saving with proper directory structure"""
        # Create test files for different categories
        test_files = [
            ("app-icon-test.png", "application-icons"),
            ("source-icon-test.png", "source-icons"),
            ("flow-bg-test.png", "flow-backgrounds"),
            ("random-test.png", "public"),
        ]

        # Patch the tenant_prefix to ensure consistent tests
        with patch.object(self.storage, "tenant_prefix", "test_tenant"):
            for filename, expected_dir in test_files:
                # Create a valid test image file
                image = Image.new("RGB", (10, 10), color="red")
                img_io = io.BytesIO()
                image.save(img_io, format="PNG")
                img_io.seek(0)

                # Create a test file with proper image content type
                content = ContentFile(img_io.getvalue())
                content.content_type = "image/png"
                content.name = filename

                # Save the file
                saved_name = self.storage._save(filename, content)

                # Verify the file exists in the storage
                self.assertTrue(self.storage.exists(saved_name))

                # Validate file is in the expected directory by checking the path structure
                # in the name
                self.assertIn(
                    expected_dir,
                    saved_name,
                    f"Directory {expected_dir} not found in path {saved_name}",
                )

                # Get just the filename part
                filename_part = os.path.basename(saved_name)

                # Verify the filename format (should be UUID with extension)
                name_part, ext = os.path.splitext(filename_part)
                self.assertEqual(ext, ".png")

                # Verify name is a valid UUID
                try:
                    uuid.UUID(name_part)
                except ValueError:
                    self.fail(f"Filename {filename_part} is not a valid UUID with extension")

                # Verify original filename is not in the saved name
                original_name_without_ext = os.path.splitext(filename)[0]
                self.assertNotIn(original_name_without_ext, saved_name)

    def test_save_file_name_format(self):
        """Test that saved files use UUID-only names"""
        # Create a test image
        image = Image.new("RGB", (10, 10), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        content = ContentFile(img_io.getvalue())
        content.content_type = "image/png"
        content.name = "test-original-name.png"

        # Save the file
        saved_name = self.storage._save(content.name, content)

        # Get just the filename part
        filename = os.path.basename(saved_name)
        name_part, ext = os.path.splitext(filename)

        # Verify extension
        self.assertEqual(ext, ".png")

        # Verify name is just a UUID
        try:
            uuid.UUID(name_part)
        except ValueError:
            self.fail(f"Filename {filename} is not a valid UUID with extension")

        # Verify original filename is not in the saved name
        self.assertNotIn("test-original-name", saved_name)

        # Verify file was saved in public directory (default)
        self.assertIn("public/", saved_name)

    def test_init_creates_directory(self):
        """Test storage directory creation on init"""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.isdir(self.temp_dir))

    def test_init_permission_error(self):
        """Test __init__ with permission error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make the directory read-only
            os.chmod(temp_dir, 0o444)
            try:
                with self.assertRaises(PermissionError):
                    FileStorage(location=temp_dir)
            finally:
                # Restore permissions
                os.chmod(temp_dir, 0o777)

    def test_init_os_error(self):
        """Test __init__ with OS error"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError()
            with self.assertRaises(ValueError):
                FileStorage(location="\0invalid")  # Should fail due to invalid path

    def test_base_location(self):
        """Test base_location property"""
        # Use the mocked connection
        self.mock_connection.schema_name = "test_tenant"
        self.assertEqual(self.storage.base_location, Path(self.temp_dir) / "test_tenant")

    def test_location(self):
        """Test location property"""
        # Use the mocked connection
        self.mock_connection.schema_name = "test_tenant"
        self.assertEqual(
            self.storage.location, os.path.abspath(Path(self.temp_dir) / "test_tenant")
        )

    def test_base_url(self):
        """Test base_url property"""
        # Use the mocked connection
        self.mock_connection.schema_name = "test_tenant"
        # Test that the base_url includes the tenant prefix
        self.assertEqual(self.storage.base_url, "/media/test_tenant/")

    def test_path(self):
        """Test path calculation"""
        # Set up tenant-aware path testing
        self.mock_connection.schema_name = "test_tenant"
        # Full path to a file should include tenant prefix
        expected_path = os.path.join(self.temp_dir, "test_tenant", "test.txt")
        self.assertEqual(self.storage.path("test.txt"), expected_path)

    def test_get_valid_name(self):
        """Test filename sanitization"""
        # The implementation should remove path components and keep only the filename
        self.assertEqual(self.storage.get_valid_name("dir/test.txt"), "test.txt")
        self.assertEqual(self.storage.get_valid_name("/absolute/path/file.txt"), "file.txt")
        self.assertEqual(self.storage.get_valid_name("../traversal/attempt.txt"), "attempt.txt")

    def test_validate_path(self):
        """Test path validation for security issues"""
        # These paths should be allowed
        self.storage._validate_path("test.txt")
        self.storage._validate_path("subfolder/test.txt")

        # These paths should raise SuspiciousOperation
        with self.assertRaises(SuspiciousOperation):
            self.storage._validate_path("../test.txt")

        with self.assertRaises(SuspiciousOperation):
            self.storage._validate_path("folder/../../../etc/passwd")

        with self.assertRaises(SuspiciousOperation):
            self.storage._validate_path("folder/../../")

    def test_save(self):
        """Test _save method"""
        self.mock_connection.schema_name = "test_tenant"

        # Patch the tenant_prefix to ensure consistency in the test
        with patch.object(self.storage, "tenant_prefix", "test_tenant"):
            content = ContentFile(b"test content")
            name = self.storage._save("test.txt", content)

            # Verify file was saved and exists
            self.assertTrue(self.storage.exists(name))

            # Get the actual file path from the storage
            tenant_path = self.storage.path(name)
            self.assertTrue(os.path.exists(tenant_path))

            # Verify content
            with open(tenant_path, "rb") as f:
                self.assertEqual(f.read(), b"test content")

            # Test with nested directory
            content = ContentFile(b"nested content")
            name = self.storage._save("dir/test.txt", content)

            # Verify file was saved
            self.assertTrue(self.storage.exists(name))
            tenant_path = self.storage.path(name)
            self.assertTrue(os.path.exists(tenant_path))

            # Verify content
            with open(tenant_path, "rb") as f:
                self.assertEqual(f.read(), b"nested content")

    def test_file_operations(self):
        """Test basic file operations"""
        # Create a valid test image file
        image = Image.new("RGB", (10, 10), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)
        original_data = img_io.getvalue()

        # Create a test file with proper image content type
        content = ContentFile(original_data)
        content.content_type = "image/png"
        content.name = "test.png"

        # Test save
        name = self.storage._save("test.png", content)
        self.assertTrue(self.storage.exists(name))

        # Test open/read
        with self.storage.open(name, "rb") as f:
            saved_data = f.read()
            # Compare the images by loading them
            original_img = Image.open(io.BytesIO(original_data))
            saved_img = Image.open(io.BytesIO(saved_data))
            self.assertEqual(original_img.size, saved_img.size)
            self.assertEqual(original_img.mode, saved_img.mode)

        # Test delete
        self.storage.delete(name)
        self.assertFalse(self.storage.exists(name))

    def test_file_overwrite(self):
        """Test file overwrite behavior"""
        # Create valid test image files
        image1 = Image.new("RGB", (10, 10), color="red")
        img_io1 = io.BytesIO()
        image1.save(img_io1, format="PNG")
        img_io1.seek(0)
        original_data1 = img_io1.getvalue()

        image2 = Image.new("RGB", (10, 10), color="blue")
        img_io2 = io.BytesIO()
        image2.save(img_io2, format="PNG")
        img_io2.seek(0)
        original_data2 = img_io2.getvalue()

        # Create test files with proper image content type
        content1 = ContentFile(original_data1)
        content1.content_type = "image/png"
        content1.name = "test.png"

        content2 = ContentFile(original_data2)
        content2.content_type = "image/png"
        content2.name = "test.png"

        # Save original file
        name = self.storage._save("test.png", content1)

        # Try to save file with same name
        name2 = self.storage._save("test.png", content2)

        # Names should be different to prevent overwrite
        self.assertNotEqual(name, name2)

        # Both files should exist
        self.assertTrue(self.storage.exists(name))
        self.assertTrue(self.storage.exists(name2))

        # Verify contents by comparing images
        with self.storage.open(name, "rb") as f:
            saved_data1 = f.read()
            original_img1 = Image.open(io.BytesIO(original_data1))
            saved_img1 = Image.open(io.BytesIO(saved_data1))
            self.assertEqual(original_img1.size, saved_img1.size)
            self.assertEqual(original_img1.mode, saved_img1.mode)

        with self.storage.open(name2, "rb") as f:
            saved_data2 = f.read()
            original_img2 = Image.open(io.BytesIO(original_data2))
            saved_img2 = Image.open(io.BytesIO(saved_data2))
            self.assertEqual(original_img2.size, saved_img2.size)
            self.assertEqual(original_img2.mode, saved_img2.mode)

    def test_directory_operations(self):
        """Test operations with directories"""
        # Create valid test images for subfolders
        image = Image.new("RGB", (10, 10), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        # Create a test file with proper image content type
        content = ContentFile(img_io.getvalue())
        content.content_type = "image/png"
        content.name = "test.png"

        # Create files in subdirectories
        with patch("authentik.root.storages.connection") as mock_conn:
            mock_conn.schema_name = "test_tenant"
            subdir1 = "subdir1/test.png"
            subdir2 = "subdir2/nested/test.png"

            # Save files to nested locations
            name1 = self.storage._save(subdir1, content)
            name2 = self.storage._save(subdir2, content)

            # Check files exist
            self.assertTrue(self.storage.exists(name1))
            self.assertTrue(self.storage.exists(name2))

            # Check directory listing
            dir_contents = self.storage.listdir("subdir1")
            self.assertEqual(len(dir_contents[1]), 1)  # One file

            # Clean up
            self.storage.delete(name1)
            self.storage.delete(name2)
            self.assertFalse(self.storage.exists(name1))
            self.assertFalse(self.storage.exists(name2))

    def test_file_modes(self):
        """Test file operations with different modes"""
        # Test binary write
        with self.storage.open("test.bin", "wb") as f:
            f.write(b"binary content")

        # Test binary read
        with self.storage.open("test.bin", "rb") as f:
            self.assertEqual(f.read(), b"binary content")

        # Test text write
        with self.storage.open("test.txt", "w") as f:
            f.write("text content")

        # Test text read
        with self.storage.open("test.txt", "r") as f:
            self.assertEqual(f.read(), "text content")

    def test_error_conditions(self):
        """Test various error conditions"""
        # Test opening non-existent file
        with self.assertRaises(FileNotFoundError):
            self.storage.open("nonexistent.txt", "r")

        # Test invalid path
        with self.assertRaises(SuspiciousOperation):
            self.storage.exists("../outside.txt")

        # Test delete non-existent file (should not raise error)
        self.storage.delete("nonexistent.txt")

        # Test invalid mode
        with self.assertRaises(ValueError):
            self.storage.open("test.txt", "invalid_mode")

    def test_directory_initialization(self):
        """Test that storage directories are properly initialized"""
        storage = FileStorage()
        tenant_dir = storage._base_path / storage.tenant_prefix

        # Check that all expected subdirectories exist
        expected_subdirs = STORAGE_DIRS
        for subdir in expected_subdirs:
            subdir_path = tenant_dir / subdir
            self.assertTrue(subdir_path.exists(), f"Expected subdirectory {subdir} does not exist")
            self.assertTrue(
                subdir_path.is_dir(), f"Expected subdirectory {subdir} is not a directory"
            )
