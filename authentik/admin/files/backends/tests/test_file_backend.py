from pathlib import Path

from django.test import TestCase

from authentik.admin.files.backends.file import FileBackend
from authentik.admin.files.tests.utils import FileTestFileBackendMixin
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG


class TestFileBackend(FileTestFileBackendMixin, TestCase):
    """Test FileBackend class"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.backend = FileBackend(FileUsage.MEDIA)

    def test_allowed_usages(self):
        """Test that FileBackend supports all usage types"""
        self.assertEqual(self.backend.allowed_usages, list(FileUsage))

    def test_base_path(self):
        """Test base_path property constructs correct path"""
        base_path = self.backend.base_path

        expected = Path(self.media_backend_path) / "media" / "public"
        self.assertEqual(base_path, expected)

    def test_base_path_reports_usage(self):
        """Test base_path with reports usage"""
        backend = FileBackend(FileUsage.REPORTS)
        base_path = backend.base_path

        expected = Path(self.reports_backend_path) / "reports" / "public"
        self.assertEqual(base_path, expected)

    def test_list_files_empty_directory(self):
        """Test list_files returns empty when directory is empty"""
        # Create the directory but keep it empty
        self.backend.base_path.mkdir(parents=True, exist_ok=True)

        files = list(self.backend.list_files())
        self.assertEqual(files, [])

    def test_list_files_with_files(self):
        """Test list_files returns all files in directory"""
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
        files = list(self.backend.list_files())
        self.assertEqual(files, [])

    def test_save_file(self):
        content = b"test file content"
        file_name = "test.txt"

        self.backend.save_file(file_name, content)

        # Verify file was created
        file_path = self.backend.base_path / file_name
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), content)

    def test_save_file_creates_subdirectories(self):
        """Test save_file creates parent directories as needed"""
        content = b"nested file content"
        file_name = "subdir1/subdir2/nested.txt"

        self.backend.save_file(file_name, content)

        # Verify file and directories were created
        file_path = self.backend.base_path / file_name
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.read_bytes(), content)

    def test_save_file_stream(self):
        """Test save_file_stream context manager writes file correctly"""
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
        file_name = "does_not_exist.txt"
        self.backend.delete_file(file_name)

    def test_file_url(self):
        """Test file_url generates correct URL"""
        file_name = "icon.png"

        url = self.backend.file_url(file_name).split("?")[0]
        expected = "/files/media/public/icon.png"
        self.assertEqual(url, expected)

    @CONFIG.patch("web.path", "/authentik/")
    def test_file_url_with_prefix(self):
        """Test file_url with web path prefix"""
        file_name = "logo.svg"

        url = self.backend.file_url(file_name).split("?")[0]
        expected = "/authentik/files/media/public/logo.svg"
        self.assertEqual(url, expected)

    def test_file_url_nested_path(self):
        """Test file_url with nested file path"""
        file_name = "path/to/file.png"

        url = self.backend.file_url(file_name).split("?")[0]
        expected = "/files/media/public/path/to/file.png"
        self.assertEqual(url, expected)

    def test_file_exists_true(self):
        """Test file_exists returns True for existing file"""
        file_name = "exists.txt"
        self.backend.base_path.mkdir(parents=True, exist_ok=True)
        (self.backend.base_path / file_name).touch()
        self.assertTrue(self.backend.file_exists(file_name))

    def test_file_exists_false(self):
        """Test file_exists returns False for nonexistent file"""
        self.assertFalse(self.backend.file_exists("does_not_exist.txt"))
