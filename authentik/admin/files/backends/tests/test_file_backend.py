"""Test file backend"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.admin.files.backend import Usage
from authentik.admin.files.backends.file import FileBackend


class TestFileBackend(TestCase):
    """Test FileBackend class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.backend = FileBackend(Usage.MEDIA)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temp directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_usages(self):
        """Test that FileBackend supports all usage types"""
        self.assertEqual(FileBackend.allowed_usages, list(Usage))

    def test_manageable(self):
        """Test that FileBackend is manageable"""
        self.assertTrue(FileBackend.manageable)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_base_path(self, mock_get_config, mock_connection):
        """Test base_path property constructs correct path"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        base_path = backend.base_path

        expected = Path(self.temp_dir) / "media" / "public"
        self.assertEqual(base_path, expected)
        mock_get_config.assert_called_with("file.path", "/data")

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_base_path_reports_usage(self, mock_get_config, mock_connection):
        """Test base_path with reports usage"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "tenant1"

        backend = FileBackend(Usage.REPORTS)
        base_path = backend.base_path

        expected = Path(self.temp_dir) / "reports" / "tenant1"
        self.assertEqual(base_path, expected)

    def test_supports_file_path_true(self):
        """Test supports_file_path returns True when backend is 'file'"""
        backend = FileBackend(Usage.MEDIA)
        backend._backend_type = "file"
        self.assertTrue(backend.supports_file_path("any/path"))

    def test_supports_file_path_false(self):
        """Test supports_file_path returns False when backend is not 'file'"""
        backend = FileBackend(Usage.MEDIA)
        backend._backend_type = "s3"
        self.assertFalse(backend.supports_file_path("any/path"))

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_list_files_empty_directory(self, mock_get_config, mock_connection):
        """Test list_files returns empty when directory is empty"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        # Create the directory but keep it empty
        backend.base_path.mkdir(parents=True, exist_ok=True)

        files = list(backend.list_files())
        self.assertEqual(files, [])

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_list_files_with_files(self, mock_get_config, mock_connection):
        """Test list_files returns all files in directory"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        base_path = backend.base_path
        base_path.mkdir(parents=True, exist_ok=True)

        # Create some test files
        (base_path / "file1.txt").write_text("content1")
        (base_path / "file2.png").write_text("content2")
        (base_path / "subdir").mkdir()
        (base_path / "subdir" / "file3.csv").write_text("content3")

        files = sorted(list(backend.list_files()))
        expected = ["file1.txt", "file2.png", "subdir/file3.csv"]
        self.assertEqual(files, sorted(expected))

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_list_files_nonexistent_directory(self, mock_get_config, mock_connection):
        """Test list_files returns empty when directory doesn't exist"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        # Don't create the directory

        files = list(backend.list_files())
        self.assertEqual(files, [])

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_save_file(self, mock_get_config, mock_connection):
        """Test save_file creates file with correct content"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        content = b"test file content"
        file_name = "test.txt"

        backend.save_file(file_name, content)

        # Verify file was created
        file_path = backend.base_path / file_name
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), content)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_save_file_creates_subdirectories(self, mock_get_config, mock_connection):
        """Test save_file creates parent directories as needed"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        content = b"nested file content"
        file_name = "subdir1/subdir2/nested.txt"

        backend.save_file(file_name, content)

        # Verify file and directories were created
        file_path = backend.base_path / file_name
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), content)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_save_file_stream(self, mock_get_config, mock_connection):
        """Test save_file_stream context manager writes file correctly"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        content = b"streamed content"
        file_name = "stream_test.txt"

        with backend.save_file_stream(file_name) as f:
            f.write(content)

        # Verify file was created
        file_path = backend.base_path / file_name
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), content)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_save_file_stream_creates_subdirectories(self, mock_get_config, mock_connection):
        """Test save_file_stream creates parent directories as needed"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        content = b"nested stream content"
        file_name = "dir1/dir2/stream.bin"

        with backend.save_file_stream(file_name) as f:
            f.write(content)

        # Verify file and directories were created
        file_path = backend.base_path / file_name
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), content)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_delete_file(self, mock_get_config, mock_connection):
        """Test delete_file removes existing file"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        file_name = "to_delete.txt"

        # Create file first
        backend.save_file(file_name, b"content")
        file_path = backend.base_path / file_name
        self.assertTrue(file_path.exists())

        # Delete it
        backend.delete_file(file_name)
        self.assertFalse(file_path.exists())

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_delete_file_nonexistent(self, mock_get_config, mock_connection):
        """Test delete_file handles nonexistent file gracefully"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        file_name = "does_not_exist.txt"

        # Should not raise an error
        backend.delete_file(file_name)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.get_web_path_prefix")
    def test_file_url(self, mock_get_prefix, mock_connection):
        """Test file_url generates correct URL"""
        mock_get_prefix.return_value = ""
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        file_name = "icon.png"

        url = backend.file_url(file_name)
        expected = "/static/media/public/icon.png"
        self.assertEqual(url, expected)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.get_web_path_prefix")
    def test_file_url_with_prefix(self, mock_get_prefix, mock_connection):
        """Test file_url with web path prefix"""
        mock_get_prefix.return_value = "/authentik"
        mock_connection.schema_name = "tenant1"

        backend = FileBackend(Usage.MEDIA)
        file_name = "logo.svg"

        url = backend.file_url(file_name)
        expected = "/authentik/static/media/tenant1/logo.svg"
        self.assertEqual(url, expected)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.get_web_path_prefix")
    def test_file_url_nested_path(self, mock_get_prefix, mock_connection):
        """Test file_url with nested file path"""
        mock_get_prefix.return_value = ""
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.REPORTS)
        file_name = "2024/01/report.csv"

        url = backend.file_url(file_name)
        expected = "/static/reports/public/2024/01/report.csv"
        self.assertEqual(url, expected)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_file_size_existing_file(self, mock_get_config, mock_connection):
        """Test file_size returns correct size for existing file"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        content = b"12345"
        file_name = "size_test.txt"

        backend.save_file(file_name, content)
        size = backend.file_size(file_name)
        self.assertEqual(size, len(content))

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_file_size_nonexistent_file(self, mock_get_config, mock_connection):
        """Test file_size returns 0 for nonexistent file"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        size = backend.file_size("does_not_exist.txt")
        self.assertEqual(size, 0)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_file_size_oserror(self, mock_get_config, mock_connection):
        """Test file_size returns 0 when OSError occurs"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)

        # Mock path.stat() to raise OSError
        with patch.object(Path, "stat", side_effect=OSError("Permission denied")):
            size = backend.file_size("error_file.txt")
            self.assertEqual(size, 0)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_file_size_valueerror(self, mock_get_config, mock_connection):
        """Test file_size returns 0 when ValueError occurs"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)

        # Mock path.stat() to raise ValueError
        with patch.object(Path, "stat", side_effect=ValueError("Invalid file")):
            size = backend.file_size("invalid_file.txt")
            self.assertEqual(size, 0)

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_file_exists_true(self, mock_get_config, mock_connection):
        """Test file_exists returns True for existing file"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        file_name = "exists.txt"

        backend.save_file(file_name, b"content")
        self.assertTrue(backend.file_exists(file_name))

    @patch("authentik.admin.files.backends.file.connection")
    @patch("authentik.admin.files.backends.file.FileBackend.get_config")
    def test_file_exists_false(self, mock_get_config, mock_connection):
        """Test file_exists returns False for nonexistent file"""
        mock_get_config.return_value = self.temp_dir
        mock_connection.schema_name = "public"

        backend = FileBackend(Usage.MEDIA)
        self.assertFalse(backend.file_exists("does_not_exist.txt"))
