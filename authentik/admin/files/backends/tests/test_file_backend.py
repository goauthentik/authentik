"""Test file backend"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from authentik.admin.files.backends.file import FileBackend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


class TestFileBackend(TestCase):
    """Test FileBackend class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.backend = FileBackend(FileUsage.MEDIA)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temp directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_usages(self):
        """Test that FileBackend supports all usage types"""
        self.assertEqual(self.backend.allowed_usages, list(FileUsage))

    def test_base_path(self):
        """Test base_path property constructs correct path"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            base_path = self.backend.base_path

            expected = Path(self.temp_dir) / "media" / "public"
            self.assertEqual(base_path, expected)

    def test_base_path_reports_usage(self):
        """Test base_path with reports usage"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            backend = FileBackend(FileUsage.REPORTS)
            base_path = backend.base_path

            expected = Path(self.temp_dir) / "reports" / "public"
            self.assertEqual(base_path, expected)

    def test_list_files_empty_directory(self):
        """Test list_files returns empty when directory is empty"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            # Create the directory but keep it empty
            self.backend.base_path.mkdir(parents=True, exist_ok=True)

            files = list(self.backend.list_files())
            self.assertEqual(files, [])

    def test_list_files_with_files(self):
        """Test list_files returns all files in directory"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            base_path = self.backend.base_path
            base_path.mkdir(parents=True, exist_ok=True)

            # Create some test files
            (base_path / "file1.txt").write_text("content1")
            (base_path / "file2.png").write_text("content2")
            (base_path / "subdir").mkdir()
            (base_path / "subdir" / "file3.csv").write_text("content3")

            files = sorted(list(self.backend.list_files()))
            expected = sorted(["file1.txt", "file2.png", "subdir/file3.csv"])
            self.assertEqual(files, expected)

    def test_list_files_nonexistent_directory(self):
        """Test list_files returns empty when directory doesn't exist"""
        with CONFIG.patch("storage.file.path", f"{self.temp_dir}/nonexistent"):
            files = list(self.backend.list_files())
            self.assertEqual(files, [])

    def test_save_file(self):
        with CONFIG.patch("storage.file.path", self.temp_dir):
            content = b"test file content"
            file_name = "test.txt"

            self.backend.save_file(file_name, content)

            # Verify file was created
            file_path = self.backend.base_path / file_name
            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.read_bytes(), content)

    def test_save_file_creates_subdirectories(self):
        """Test save_file creates parent directories as needed"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            content = b"nested file content"
            file_name = "subdir1/subdir2/nested.txt"

            self.backend.save_file(file_name, content)

            # Verify file and directories were created
            file_path = self.backend.base_path / file_name
            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.read_bytes(), content)

    def test_save_file_stream(self):
        """Test save_file_stream context manager writes file correctly"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            content = b"streamed content"
            file_name = "stream_test.txt"

            with self.backend.save_file_stream(file_name) as f:
                f.write(content)

            # Verify file was created
            file_path = self.backend.base_path / file_name
            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.read_bytes(), content)

    def test_save_file_stream_creates_subdirectories(self):
        """Test save_file_stream creates parent directories as needed"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            content = b"nested stream content"
            file_name = "dir1/dir2/stream.bin"

            with self.backend.save_file_stream(file_name) as f:
                f.write(content)

            # Verify file and directories were created
            file_path = self.backend.base_path / file_name
            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.read_bytes(), content)

    def test_delete_file(self):
        """Test delete_file removes existing file"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            file_name = "to_delete.txt"

            # Create file first
            self.backend.save_file(file_name, b"content")
            file_path = self.backend.base_path / file_name
            self.assertTrue(file_path.exists())

            # Delete it
            self.backend.delete_file(file_name)
            self.assertFalse(file_path.exists())

    def test_delete_file_nonexistent(self):
        """Test delete_file handles nonexistent file gracefully"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            file_name = "does_not_exist.txt"
            self.backend.delete_file(file_name)

    def test_file_url(self):
        """Test file_url generates correct URL"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            file_name = "icon.png"

            url = self.backend.file_url(file_name)
            expected = "/media/public/icon.png"
            self.assertEqual(url, expected)

    @CONFIG.patch("web.path", "/authentik/")
    def test_file_url_with_prefix(self):
        """Test file_url with web path prefix"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            file_name = "logo.svg"

            url = self.backend.file_url(file_name)
            expected = "/authentik/media/public/logo.svg"
            self.assertEqual(url, expected)

    def test_file_url_nested_path(self):
        """Test file_url with nested file path"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            file_name = "path/to/file.png"

            url = self.backend.file_url(file_name)
            expected = "/media/public/path/to/file.png"
            self.assertEqual(url, expected)

    def test_file_size_existing_file(self):
        """Test file_size returns correct size for existing file"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            content = b"12345"
            file_name = "size_test.txt"

            self.backend.save_file(file_name, content)
            size = self.backend.file_size(file_name)
            self.assertEqual(size, len(content))

    def test_file_size_nonexistent_file(self):
        """Test file_size returns 0 for nonexistent file"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            size = self.backend.file_size("does_not_exist.txt")
            self.assertEqual(size, 0)

    def test_file_size_oserror(self):
        """Test file_size returns 0 when OSError occurs"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            # Mock path.stat() to raise OSError
            with patch.object(Path, "stat", side_effect=OSError("Permission denied")):
                size = self.backend.file_size("error_file.txt")
                self.assertEqual(size, 0)

    def test_file_size_valueerror(self):
        """Test file_size returns 0 when ValueError occurs"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            # Mock path.stat() to raise ValueError
            with patch.object(Path, "stat", side_effect=ValueError("Invalid file")):
                size = self.backend.file_size("invalid_file.txt")
                self.assertEqual(size, 0)

    def test_file_exists_true(self):
        """Test file_exists returns True for existing file"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            file_name = "exists.txt"
            self.backend.base_path.mkdir(parents=True, exist_ok=True)
            (self.backend.base_path / file_name).touch()
            self.assertTrue(self.backend.file_exists(file_name))

    def test_file_exists_false(self):
        """Test file_exists returns False for nonexistent file"""
        with CONFIG.patch("storage.file.path", self.temp_dir):
            self.assertFalse(self.backend.file_exists("does_not_exist.txt"))
