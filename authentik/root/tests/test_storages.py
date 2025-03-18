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
from django.db import connection
from django.test import TestCase
from PIL import Image

from authentik.root.storages import (
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
        self.assertFalse(validate_image_file(png_file))

    def test_invalid_extension(self):
        """Test validation with invalid extension"""
        png_file = self.create_test_image("PNG", "image/png")
        png_file.name = "test.txt"
        self.assertFalse(validate_image_file(png_file))

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
        self.assertFalse(validate_image_file(invalid_svg))

    def test_non_image_file(self):
        """Test validation of non-image file"""
        text_file = InMemoryUploadedFile(
            io.BytesIO(b"test content"), "meta_icon", "test.txt", "text/plain", 12, None
        )
        self.assertFalse(validate_image_file(text_file))

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
        self.assertFalse(validate_image_file(corrupted_file))

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
        self.assertFalse(validate_image_file(truncated_file))

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
        self.assertFalse(validate_image_file(incomplete_svg))

        # Test with non-SVG XML
        non_svg_xml = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><not_svg></not_svg>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        self.assertFalse(validate_image_file(non_svg_xml))

        # Test with malformed XML
        malformed_xml = InMemoryUploadedFile(
            io.BytesIO(b'<?xml version="1.0"?><svg><unclosed>'),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            11,
            None,
        )
        self.assertFalse(validate_image_file(malformed_xml))

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
        self.assertFalse(validate_image_file(invalid_ico))

        # Test with truncated ICO
        truncated_ico = InMemoryUploadedFile(
            io.BytesIO(b"\x00\x00"),  # Too short
            "meta_icon",
            "test.ico",
            "image/x-icon",
            2,
            None,
        )
        self.assertFalse(validate_image_file(truncated_ico))


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

        # Mock objects
        self.mock_objects = {}
        self.mock_bucket.Object.side_effect = lambda key: self.mock_objects.setdefault(
            key, MagicMock()
        )

        # Setup successful validation by default
        self.mock_client.list_buckets.return_value = {"Buckets": [{"Name": "test-bucket"}]}
        self.mock_client.head_bucket.return_value = {}

        # Mock the configuration before creating the storage instance
        self.config_patcher = patch("authentik.lib.config.CONFIG.refresh")
        self.mock_config = self.config_patcher.start()
        self.mock_config.side_effect = lambda key, default=None, sep=".": {
            "storage.media.s3.access_key": "test-key",
            "storage.media.s3.secret_key": "test-secret",
            "storage.media.s3.bucket_name": "test-bucket",
            "storage.media.s3.region_name": "us-east-1",
        }.get(key, default)

        # Create test storage with mocked client
        self.session_patcher = patch("boto3.Session")
        self.mock_session = self.session_patcher.start()
        self.mock_session.return_value.client.return_value = self.mock_client
        self.storage = S3Storage()
        self.storage._bucket = self.mock_bucket

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
        """Test bucket validation during initialization"""
        # Test bucket doesn't exist
        self.mock_client.buckets.all.return_value = []
        with self.assertRaises(ImproperlyConfigured):
            storage = S3Storage()
            _ = storage.bucket  # Access bucket property to trigger validation

        # Test permission denied
        self.mock_client.buckets.all.return_value = [MagicMock(name="test-bucket")]
        self.mock_bucket.objects.limit.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "Access Denied",
                }
            },
            "HeadObject",
        )
        with self.assertRaises(ImproperlyConfigured):
            storage = S3Storage()
            _ = storage.bucket  # Access bucket property to trigger validation

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
        test_name = "test.txt"
        normalized = self.storage._normalize_name(test_name)

        # Verify tenant path is included
        self.assertIn(connection.schema_name, normalized)

        # Test with suspicious path
        with self.assertRaises(SuspiciousOperation):
            self.storage._normalize_name("../test.txt")

    def test_save_and_delete(self):
        """Test file save and delete operations"""
        test_file = self.create_test_image()

        # Mock successful upload
        self.mock_object.load.return_value = None

        # Save file
        name = self.storage._save("test.png", test_file)

        # Verify file was saved with tenant prefix
        self.assertTrue(name.startswith(self.storage.tenant_prefix))
        self.assertTrue(name.endswith(".png"))

        # Delete file
        self.storage.delete(name)
        self.mock_object.delete.assert_called_once()

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
        self.mock_object.load.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "head_object"
        )

        # Attempt save
        with self.assertRaises(ClientError):
            self.storage._save("test.png", test_file)

        # Verify cleanup was attempted
        self.mock_object.delete.assert_called_once()

    def test_url_generation(self):
        """Test URL generation for S3 objects"""
        # Mock tenant_prefix
        with patch.object(self.storage, "tenant_prefix", "test_tenant"):
            filename = "test.png"
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
        self.assertIn("Failed to validate image", str(context.exception))

    def test_save_non_image(self):
        """Test rejection of non-image files"""
        text_file = ContentFile(b"test content", name="test.txt")

        with self.assertRaises(SuspiciousOperation) as cm:
            self.storage._save("test.txt", text_file)

        self.assertIn("only accepts valid image files", str(cm.exception))

    def test_delete_nonexistent(self):
        """Test deleting a nonexistent file"""
        # Set up mock to raise ClientError when trying to delete
        self.mock_object.delete.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "DeleteObject",
        )

        # Call delete method
        self.storage.delete("nonexistent.txt")

        # Verify delete was called
        self.mock_bucket.Object.assert_called_once_with("nonexistent.txt")
        self.mock_object.delete.assert_called_once()

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
        # Create a test image file
        test_file = self.create_test_image()

        # Save initial icon
        old_key = self.storage._save("test_icon.png", test_file)
        old_mock_object = self.mock_objects[old_key]

        # Replace with new icon
        new_file = self.create_test_image()
        new_key = self.storage._save("new_icon.png", new_file)

        # Verify old file was deleted
        old_mock_object.delete.assert_called_once()

        # Verify new file was saved
        new_mock_object = self.mock_objects[new_key]
        new_mock_object.load.assert_called_once()

    def test_file_listing(self):
        """Test file listing operations"""
        # Setup mock objects for listing
        self.mock_bucket.objects.filter.return_value = [
            MagicMock(key="tenant1/file1.txt"),
            MagicMock(key="tenant1/dir1/file2.txt"),
            MagicMock(key="tenant2/file3.txt"),  # Should not be listed
        ]

        # Test listing with tenant isolation
        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = "tenant1"

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

        # Make our mock object available
        self.mock_objects[test_file] = mock_obj

        # Test size method
        size = self.storage.size(test_file)
        self.assertEqual(size, 1234)

        # Test modified time method
        modified_time = self.storage.get_modified_time(test_file)
        self.assertIsNotNone(modified_time)

    def test_file_exists(self):
        """Test file existence checks"""

        # Setup mock responses
        def mock_head_object(Key):
            if Key == "tenant1/exists.txt":
                return {}
            raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "head_object")

        self.mock_client.head_object = MagicMock(side_effect=mock_head_object)

        with patch("django.db.connection") as mock_conn:
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
            ("test.png", "text/plain", False),
            ("test.jpg", "application/octet-stream", False),
            ("test.svg", "text/xml", False),
            ("test.ico", "application/octet-stream", False),
        ]

        for filename, content_type, should_succeed in test_cases:
            # Create test file with appropriate content
            if filename.endswith(".svg"):
                content = b'<?xml version="1.0"?><svg></svg>'
            elif filename.endswith(".ico"):
                content = b"\x00\x00\x01\x00"  # Valid ICO header
            else:
                # Create a valid image for other formats
                image = Image.new("RGB", (10, 10), color="red")
                img_io = io.BytesIO()
                image.save(img_io, format=filename.split(".")[-1].upper())
                content = img_io.getvalue()

            test_file = ContentFile(content, name=filename)
            test_file.content_type = content_type

            # Mock successful upload
            mock_obj = MagicMock()
            self.mock_objects[f"tenant1/{filename}"] = mock_obj

            with patch("django.db.connection") as mock_conn:
                mock_conn.schema_name = "tenant1"

                if should_succeed:
                    # Should succeed for valid image types
                    name = self.storage._save(filename, test_file)
                    self.assertTrue(name.endswith(filename))
                    mock_obj.upload_fileobj.assert_called_once()
                else:
                    # Should fail for non-image types
                    with self.assertRaises(SuspiciousOperation) as cm:
                        self.storage._save(filename, test_file)
                    self.assertIn("only accepts valid image files", str(cm.exception))

    def test_large_file_operations(self):
        """Test handling of large files with multipart upload"""
        # Create a large file (5MB)
        large_file = io.BytesIO(b"0" * (5 * 1024 * 1024))

        with patch.object(self.storage.bucket, "upload_fileobj") as mock_upload:
            # Mock transfer config
            self.storage.transfer_config = Config(
                multipart_threshold=1 * 1024 * 1024, max_concurrency=2  # 1MB
            )

            # Save large file
            self.storage._save("large.bin", large_file)

            # Verify multipart upload was used
            mock_upload.assert_called_once()
            _, kwargs = mock_upload.call_args
            self.assertIn("Config", str(kwargs))

    def test_error_handling(self):
        """Test various error conditions"""
        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = "tenant1"

            # Test network error
            self.mock_object.upload_fileobj.side_effect = ClientError(
                {"Error": {"Code": "NetworkError", "Message": "Network Error"}}, "upload_fileobj"
            )
            with self.assertRaises(ClientError):
                self.storage._save("test.txt", ContentFile(b"content"))

            # Test permission denied
            self.mock_object.upload_fileobj.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "upload_fileobj"
            )
            with self.assertRaises(ClientError):
                self.storage._save("test.txt", ContentFile(b"content"))

            # Test bucket not found
            self.mock_object.upload_fileobj.side_effect = ClientError(
                {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}}, "upload_fileobj"
            )
            with self.assertRaises(ClientError):
                self.storage._save("test.txt", ContentFile(b"content"))

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

        # Get URL
        url = self.storage.url(name)

        # Verify URL uses custom domain
        self.assertTrue(url.startswith("https://bucket.xn--idk5byd.net/"))
        self.assertTrue("X-Amz-Algorithm=AWS4-HMAC-SHA256" in url)
        self.assertTrue("X-Amz-SignedHeaders=host" in url)
        self.assertTrue("X-Amz-Signature=test" in url)


class TestTenantAwareStorage(TestCase):
    """Test tenant-aware storage functionality"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        # Create a simple TenantAwareStorage for testing
        self.storage = TenantAwareStorage()
        # Mock the connection schema_name
        self.connection_patcher = patch("django.db.connection")
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
        self.connection_patcher = patch("django.db.connection")
        self.mock_connection = self.connection_patcher.start()
        self.mock_connection.schema_name = "test_tenant"
        # Initialize storage with temp directory
        self.storage = FileStorage(location=self.temp_dir, base_url="/media/")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
        self.connection_patcher.stop()
        super().tearDown()

    def test_init_creates_directory(self):
        """Test storage directory creation on init"""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.isdir(self.temp_dir))

    def test_init_permission_error(self):
        """Test __init__ with permission error"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError()
            with self.assertRaises(PermissionError):
                FileStorage(location="/root/test")  # Should fail due to permissions

    def test_init_os_error(self):
        """Test __init__ with OS error"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError()
            with self.assertRaises(OSError):
                FileStorage(location="\0invalid")  # Should fail due to invalid path

    def test_base_location(self):
        """Test base_location property"""
        # Mock tenant prefix
        with patch.object(self.storage, "tenant_prefix", return_value="test_tenant"):
            self.assertEqual(self.storage.base_location, Path(self.temp_dir) / "test_tenant")

    def test_location(self):
        """Test location property"""
        # Mock tenant prefix
        with patch.object(self.storage, "tenant_prefix", return_value="test_tenant"):
            self.assertEqual(
                self.storage.location, os.path.abspath(Path(self.temp_dir) / "test_tenant")
            )

    def test_base_url(self):
        """Test base_url property"""
        # Mock tenant prefix
        with patch.object(self.storage, "tenant_prefix", return_value="test_tenant"):
            self.assertEqual(self.storage.base_url, "/media/test_tenant/")

    def test_path(self):
        """Test path calculation"""
        # Set up tenant-aware path testing
        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = "test_tenant"
            # Full path to a file should include tenant prefix
            expected_path = os.path.abspath(Path(self.temp_dir) / "test_tenant" / "test.txt")
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
            self.storage._validate_path("/etc/passwd")

        with self.assertRaises(SuspiciousOperation):
            self.storage._validate_path("folder/../../../etc/passwd")

    def test_save(self):
        """Test _save method"""
        content = ContentFile(b"test content")
        name = self.storage._save("test.txt", content)

        # Verify file was saved
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, name)))

        # Verify content
        with open(os.path.join(self.temp_dir, name), "rb") as f:
            self.assertEqual(f.read(), b"test content")

        # Test with nested directory
        content = ContentFile(b"nested content")
        name = self.storage._save("dir/test.txt", content)

        # Verify file was saved
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, name)))

        # Verify content
        with open(os.path.join(self.temp_dir, name), "rb") as f:
            self.assertEqual(f.read(), b"nested content")

    def test_file_operations(self):
        """Test basic file operations"""
        # Create a valid test image file
        image = Image.new("RGB", (10, 10), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        # Create a test file with proper image content type
        content = ContentFile(img_io.getvalue())
        content.content_type = "image/png"
        content.name = "test.png"

        # Test save
        name = self.storage._save("test.png", content)
        self.assertTrue(self.storage.exists(name))

        # Test open/read
        with self.storage.open(name, "rb") as f:
            data = f.read()
            self.assertEqual(data, img_io.getvalue())

        # Test delete
        self.storage.delete(name)
        self.assertFalse(self.storage.exists(name))

    def test_tenant_isolation(self):
        """Test tenant isolation in file operations"""
        # Create a valid test image file
        image = Image.new("RGB", (10, 10), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)

        # Create a test file with proper image content type
        content = ContentFile(img_io.getvalue())
        content.content_type = "image/png"
        content.name = "test.png"

        # Test with first tenant
        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = "tenant1"
            name1 = self.storage._save("test.png", content)
            self.assertTrue(name1.startswith("tenant1/"))
            self.assertTrue(self.storage.exists(name1))

        # Test with second tenant
        with patch("django.db.connection") as mock_conn:
            mock_conn.schema_name = "tenant2"
            # Same filename should create different path
            name2 = self.storage._save("test.png", content)
            self.assertTrue(name2.startswith("tenant2/"))
            self.assertTrue(self.storage.exists(name2))

            # Should not see tenant1's file
            self.assertFalse(self.storage.exists(name1))

    def test_file_overwrite(self):
        """Test file overwrite behavior"""
        # Create valid test image files
        image1 = Image.new("RGB", (10, 10), color="red")
        img_io1 = io.BytesIO()
        image1.save(img_io1, format="PNG")
        img_io1.seek(0)

        image2 = Image.new("RGB", (10, 10), color="blue")
        img_io2 = io.BytesIO()
        image2.save(img_io2, format="PNG")
        img_io2.seek(0)

        # Create test files with proper image content type
        content1 = ContentFile(img_io1.getvalue())
        content1.content_type = "image/png"
        content1.name = "test.png"

        content2 = ContentFile(img_io2.getvalue())
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

        # Verify contents
        with self.storage.open(name, "rb") as f:
            self.assertEqual(f.read(), img_io1.getvalue())
        with self.storage.open(name2, "rb") as f:
            self.assertEqual(f.read(), img_io2.getvalue())

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
        with patch("django.db.connection") as mock_conn:
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
