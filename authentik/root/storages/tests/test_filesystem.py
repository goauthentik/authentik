"""Test filesystem storage backend."""

import io
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.exceptions import SuspiciousOperation
from django.test import TestCase
from PIL import Image

from authentik.root.storages.filesystem import FileStorage
from authentik.root.storages.exceptions import FileValidationError
from authentik.root.storages.connection import connection


class TestFileStorage(TestCase):
    """Test filesystem storage backend"""

    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileStorage(location=self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        shutil.rmtree(self.temp_dir)

    def create_test_image(self, name="test.png") -> ContentFile:
        """Create a test image file"""
        image = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        image.save(img_io, format="PNG")
        img_io.seek(0)
        content = ContentFile(img_io.getvalue(), name=name)
        content.content_type = "image/png"
        return content

    def test_directory_structure(self):
        """Test directory structure creation"""
        # Verify base directory exists
        self.assertTrue(os.path.exists(self.temp_dir))
        
        # Get the tenant prefix from storage
        tenant_prefix = self.storage.tenant_prefix
        
        # Verify storage directories are created with tenant prefix
        for directory in self.storage.STORAGE_DIRS:
            dir_path = os.path.join(self.temp_dir, tenant_prefix, directory)
            self.assertTrue(os.path.exists(dir_path))
            self.assertTrue(os.path.isdir(dir_path))

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

    def test_tenant_isolation(self):
        """Test tenant isolation in storage"""
        # Create test files for different tenants
        # First tenant
        connection.schema_name = "tenant1"
        file1 = self.create_test_image("tenant1.png")
        name1 = self.storage._save("test.png", file1)

        # Second tenant
        connection.schema_name = "tenant2"
        file2 = self.create_test_image("tenant2.png")
        name2 = self.storage._save("test.png", file2)

        # Verify files are stored in tenant-specific directories
        self.assertTrue(name1.startswith("tenant1/public/"))
        self.assertTrue(name2.startswith("tenant2/public/"))

        # Verify files are isolated
        self.assertTrue(self.storage.exists(name1))
        self.assertTrue(self.storage.exists(name2))

        # Switch back to first tenant
        connection.schema_name = "tenant1"
        self.assertTrue(self.storage.exists(name1))
        self.assertFalse(self.storage.exists(name2))

    def test_invalid_file_types(self):
        """Test handling of invalid file types"""
        # Create a non-image file
        text_file = ContentFile(b"not an image", name="test.txt")
        text_file.content_type = "text/plain"

        # Attempt to save non-image file
        with self.assertRaises(FileValidationError) as cm:
            self.storage._save("test.txt", text_file)
        self.assertIn("Invalid content type", str(cm.exception))

    def test_file_validation(self):
        """Test file validation during save"""
        # Create an invalid image file
        invalid_file = ContentFile(b"not an image", name="test.png")
        invalid_file.content_type = "image/png"

        # Attempt to save invalid image
        with self.assertRaises(FileValidationError) as cm:
            self.storage._save("test.png", invalid_file)
        self.assertIn("Invalid image format", str(cm.exception))

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

    def test_file_subdirectory(self):
        """Test file subdirectory determination"""
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

    def test_file_size(self):
        """Test file size retrieval"""
        # Create and save a test file
        test_file = self.create_test_image()
        name = self.storage._save("test.png", test_file)

        # Get file size
        size = self.storage.size(name)
        self.assertGreater(size, 0)
        self.assertEqual(size, len(test_file.read()))

    def test_file_url(self):
        """Test file URL generation"""
        # Create and save a test file
        test_file = self.create_test_image()
        name = self.storage._save("test.png", test_file)

        # Get file URL
        url = self.storage.url(name)
        self.assertTrue(url.startswith("/media/"))
        self.assertIn(name, url)

    def test_file_exists(self):
        """Test file existence checks"""
        # Create and save a test file
        test_file = self.create_test_image()
        name = self.storage._save("test.png", test_file)

        # Check file exists
        self.assertTrue(self.storage.exists(name))
        self.assertFalse(self.storage.exists("nonexistent.png"))

    def test_file_listing(self):
        """Test file listing operations"""
        # Create test files in different directories
        files = [
            ("app-icon-test.png", "application-icons"),
            ("source-icon-test.png", "source-icons"),
            ("flow-bg-test.png", "flow-backgrounds"),
            ("random-test.png", "public"),
        ]

        for filename, _ in files:
            test_file = self.create_test_image(filename)
            self.storage._save(filename, test_file)

        # List files in root directory
        dirs, files = self.storage.listdir("")
        self.assertEqual(set(dirs), {"application-icons", "source-icons", "flow-backgrounds", "public"})
        self.assertEqual(set(files), set())

        # List files in public directory
        dirs, files = self.storage.listdir("public")
        self.assertEqual(set(dirs), set())
        self.assertEqual(len(files), 1)
        self.assertTrue(any("random-test" in f for f in files)) 