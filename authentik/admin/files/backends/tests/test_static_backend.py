"""Test Static backend implementation"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from authentik.admin.files.backend import Usage
from authentik.admin.files.backends.static import StaticBackend
from authentik.admin.files.constants import (
    STATIC_ASSETS_DIRS,
    STATIC_FILE_EXTENSIONS,
    STATIC_PATH_PREFIX,
    STATIC_SOURCES_DIR,
)


class TestStaticBackend(TestCase):
    """Test Static backend functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.usage = Usage.MEDIA

    def test_init(self):
        """Test StaticBackend initialization"""
        backend = StaticBackend(self.usage)

        self.assertEqual(backend.usage, self.usage)
        # Static backend is not manageable, so no backend_type is set
        self.assertIsNone(backend._backend_type)

    def test_allowed_usages(self):
        """Test that StaticBackend only supports MEDIA usage"""
        self.assertEqual(StaticBackend.allowed_usages, [Usage.MEDIA])

    def test_manageable(self):
        """Test that StaticBackend is not manageable"""
        self.assertFalse(StaticBackend.manageable)

    def test_supports_file_path_static_prefix(self):
        """Test supports_file_path returns True for /static prefix"""
        backend = StaticBackend(self.usage)

        self.assertTrue(backend.supports_file_path("/static/assets/icons/test.svg"))
        self.assertTrue(backend.supports_file_path("/static/authentik/sources/icon.png"))

    def test_supports_file_path_web_dist(self):
        """Test supports_file_path returns True for web/dist/assets prefix"""
        backend = StaticBackend(self.usage)

        self.assertTrue(backend.supports_file_path("web/dist/assets/icons/test.svg"))
        self.assertTrue(backend.supports_file_path("web/dist/assets/images/logo.png"))

    def test_supports_file_path_not_static(self):
        """Test supports_file_path returns False for non-static paths"""
        backend = StaticBackend(self.usage)

        self.assertFalse(backend.supports_file_path("media/public/test.png"))
        self.assertFalse(backend.supports_file_path("/media/test.svg"))
        self.assertFalse(backend.supports_file_path("test.jpg"))

    @patch("authentik.admin.files.backends.static.STATIC_SOURCES_DIR")
    def test_list_files_sources(self, mock_sources_dir):
        """Test list_files includes source icons"""
        backend = StaticBackend(self.usage)

        # Mock source directory
        mock_sources_path = MagicMock(spec=Path)
        mock_sources_path.exists.return_value = True

        # Mock file entries
        mock_file1 = MagicMock(spec=Path)
        mock_file1.is_file.return_value = True
        mock_file1.suffix = ".svg"
        mock_file1.name = "github.svg"

        mock_file2 = MagicMock(spec=Path)
        mock_file2.is_file.return_value = True
        mock_file2.suffix = ".png"
        mock_file2.name = "google.png"

        mock_dir = MagicMock(spec=Path)
        mock_dir.is_file.return_value = False

        mock_sources_path.iterdir.return_value = [mock_file1, mock_file2, mock_dir]
        mock_sources_dir.__bool__.return_value = True
        mock_sources_dir.exists.return_value = True
        mock_sources_dir.iterdir.return_value = mock_sources_path.iterdir.return_value

        with patch("authentik.admin.files.backends.static.STATIC_ASSETS_DIRS", []):
            files = list(backend.list_files())

            self.assertEqual(len(files), 2)
            self.assertIn("/static/authentik/sources/github.svg", files)
            self.assertIn("/static/authentik/sources/google.png", files)

    @patch("authentik.admin.files.backends.static.Path")
    @patch("authentik.admin.files.backends.static.STATIC_SOURCES_DIR")
    def test_list_files_assets(self, mock_sources_dir, mock_path):
        """Test list_files includes asset files"""
        backend = StaticBackend(self.usage)

        # Mock sources directory as not existing
        mock_sources_dir.exists.return_value = False

        # Mock assets directory structure
        mock_icons_dir = MagicMock(spec=Path)
        mock_icons_dir.exists.return_value = True

        mock_icon1 = MagicMock(spec=Path)
        mock_icon1.is_file.return_value = True
        mock_icon1.suffix = ".svg"
        mock_icon1.name = "icon1.svg"

        mock_icon2 = MagicMock(spec=Path)
        mock_icon2.is_file.return_value = True
        mock_icon2.suffix = ".png"
        mock_icon2.name = "icon2.png"

        mock_icons_dir.rglob.return_value = [mock_icon1, mock_icon2]

        # Setup Path mock to return our mocked directory
        def path_side_effect(arg):
            if arg == "web/dist/assets/icons":
                return mock_icons_dir
            return MagicMock(exists=lambda: False)

        mock_path.side_effect = path_side_effect

        with patch("authentik.admin.files.backends.static.STATIC_ASSETS_DIRS", ["assets/icons"]):
            files = list(backend.list_files())

            self.assertEqual(len(files), 2)
            self.assertIn("/static/assets/icons/icon1.svg", files)
            self.assertIn("/static/assets/icons/icon2.png", files)

    @patch("authentik.admin.files.backends.static.Path")
    @patch("authentik.admin.files.backends.static.STATIC_SOURCES_DIR")
    def test_list_files_filters_extensions(self, mock_sources_dir, mock_path):
        """Test list_files only includes allowed extensions"""
        backend = StaticBackend(self.usage)

        mock_sources_dir.exists.return_value = False

        # Mock directory with various file types
        mock_dir = MagicMock(spec=Path)
        mock_dir.exists.return_value = True

        mock_svg = MagicMock(spec=Path)
        mock_svg.is_file.return_value = True
        mock_svg.suffix = ".svg"
        mock_svg.name = "icon.svg"

        mock_txt = MagicMock(spec=Path)
        mock_txt.is_file.return_value = True
        mock_txt.suffix = ".txt"
        mock_txt.name = "readme.txt"

        mock_js = MagicMock(spec=Path)
        mock_js.is_file.return_value = True
        mock_js.suffix = ".js"
        mock_js.name = "script.js"

        mock_dir.rglob.return_value = [mock_svg, mock_txt, mock_js]

        mock_path.return_value = mock_dir

        with patch("authentik.admin.files.backends.static.STATIC_ASSETS_DIRS", ["assets/icons"]):
            files = list(backend.list_files())

            # Only .svg should be included (basing myself from STATIC_FILE_EXTENSIONS)
            self.assertEqual(len(files), 1)
            self.assertIn("/static/assets/icons/icon.svg", files)

    @patch("authentik.admin.files.backends.static.STATIC_SOURCES_DIR")
    def test_list_files_empty(self, mock_sources_dir):
        """Test list_files with no files"""
        backend = StaticBackend(self.usage)

        mock_sources_dir.exists.return_value = False

        with patch("authentik.admin.files.backends.static.STATIC_ASSETS_DIRS", []):
            files = list(backend.list_files())

            self.assertEqual(len(files), 0)

    @patch("authentik.admin.files.backends.static.get_web_path_prefix")
    def test_file_url_static_prefix(self, mock_get_prefix):
        """Test file_url with /static prefix"""
        backend = StaticBackend(self.usage)
        mock_get_prefix.return_value = "/authentik"

        url = backend.file_url("/static/authentik/sources/icon.svg")

        self.assertEqual(url, "/authentik/static/authentik/sources/icon.svg")

    @patch("authentik.admin.files.backends.static.get_web_path_prefix")
    def test_file_url_web_dist_prefix(self, mock_get_prefix):
        """Test file_url with web/dist/assets prefix"""
        backend = StaticBackend(self.usage)
        mock_get_prefix.return_value = ""

        url = backend.file_url("web/dist/assets/icons/test.svg")

        self.assertEqual(url, "/static/dist/assets/icons/test.svg")

    @patch("authentik.admin.files.backends.static.get_web_path_prefix")
    def test_file_url_with_custom_prefix(self, mock_get_prefix):
        """Test file_url with custom web path prefix"""
        backend = StaticBackend(self.usage)
        mock_get_prefix.return_value = "/custom-path"

        url = backend.file_url("/static/assets/icons/icon.png")

        self.assertEqual(url, "/custom-path/static/assets/icons/icon.png")

    def test_file_url_invalid_path(self):
        """Test file_url raises ValueError for invalid paths"""
        backend = StaticBackend(self.usage)

        with self.assertRaises(ValueError) as context:
            backend.file_url("invalid/path/test.png")

        self.assertIn("Invalid static file path", str(context.exception))

    def test_file_size(self):
        """Test file_size always returns 0 for static files"""
        backend = StaticBackend(self.usage)

        # Static files don't track size
        self.assertEqual(backend.file_size("/static/test.svg"), 0)
        self.assertEqual(backend.file_size("web/dist/assets/icon.png"), 0)

    def test_file_exists_static_path(self):
        """Test file_exists returns True for static paths"""
        backend = StaticBackend(self.usage)

        # Static files are assumed to exist if they match the pattern
        self.assertTrue(backend.file_exists("/static/authentik/sources/icon.svg"))
        self.assertTrue(backend.file_exists("web/dist/assets/icons/test.png"))

    def test_file_exists_non_static_path(self):
        """Test file_exists returns False for non-static paths"""
        backend = StaticBackend(self.usage)

        self.assertFalse(backend.file_exists("media/public/test.png"))
        self.assertFalse(backend.file_exists("/media/icon.svg"))

    def test_save_file_not_supported(self):
        """Test save_file raises NotImplementedError"""
        backend = StaticBackend(self.usage)

        with self.assertRaises(NotImplementedError) as context:
            backend.save_file("test.png", b"content")

        self.assertIn("Cannot save files to static backend", str(context.exception))

    def test_save_file_stream_not_supported(self):
        """Test save_file_stream raises NotImplementedError"""
        backend = StaticBackend(self.usage)

        with self.assertRaises(NotImplementedError) as context:
            with backend.save_file_stream("test.png"):
                pass

        self.assertIn("Cannot save files to static backend", str(context.exception))

    def test_delete_file_not_supported(self):
        """Test delete_file raises NotImplementedError"""
        backend = StaticBackend(self.usage)

        with self.assertRaises(NotImplementedError) as context:
            backend.delete_file("test.png")

        self.assertIn("Cannot delete files from static backend", str(context.exception))

    @patch("authentik.admin.files.backends.static.STATIC_SOURCES_DIR")
    @patch("authentik.admin.files.backends.static.Path")
    def test_list_files_multiple_directories(self, mock_path, mock_sources_dir):
        """Test list_files combines files from multiple directories"""
        backend = StaticBackend(self.usage)

        # Mock sources directory
        mock_sources_dir.exists.return_value = True
        mock_source_file = MagicMock(spec=Path)
        mock_source_file.is_file.return_value = True
        mock_source_file.suffix = ".svg"
        mock_source_file.name = "source.svg"
        mock_sources_dir.iterdir.return_value = [mock_source_file]

        # Mock icons directory
        mock_icons_dir = MagicMock(spec=Path)
        mock_icons_dir.exists.return_value = True
        mock_icon_file = MagicMock(spec=Path)
        mock_icon_file.is_file.return_value = True
        mock_icon_file.suffix = ".png"
        mock_icon_file.name = "icon.png"
        mock_icons_dir.rglob.return_value = [mock_icon_file]

        # Mock images directory
        mock_images_dir = MagicMock(spec=Path)
        mock_images_dir.exists.return_value = True
        mock_image_file = MagicMock(spec=Path)
        mock_image_file.is_file.return_value = True
        mock_image_file.suffix = ".jpg"
        mock_image_file.name = "image.jpg"
        mock_images_dir.rglob.return_value = [mock_image_file]

        def path_side_effect(arg):
            if arg == "web/dist/assets/icons":
                return mock_icons_dir
            elif arg == "web/dist/assets/images":
                return mock_images_dir
            return MagicMock(exists=lambda: False)

        mock_path.side_effect = path_side_effect

        with patch(
            "authentik.admin.files.backends.static.STATIC_ASSETS_DIRS",
            ["assets/icons", "assets/images"],
        ):
            files = list(backend.list_files())

            self.assertEqual(len(files), 3)
            self.assertIn("/static/authentik/sources/source.svg", files)
            self.assertIn("/static/assets/icons/icon.png", files)
            self.assertIn("/static/assets/images/image.jpg", files)

    @patch("authentik.admin.files.backends.static.STATIC_SOURCES_DIR")
    def test_list_files_skips_non_files(self, mock_sources_dir):
        """Test list_files skips directories and non-file entries"""
        backend = StaticBackend(self.usage)

        mock_sources_dir.exists.return_value = True

        # Mix of files and directories
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.suffix = ".svg"
        mock_file.name = "file.svg"

        mock_directory = MagicMock(spec=Path)
        mock_directory.is_file.return_value = False
        mock_directory.suffix = ""
        mock_directory.name = "subdir"

        mock_sources_dir.iterdir.return_value = [mock_file, mock_directory]

        with patch("authentik.admin.files.backends.static.STATIC_ASSETS_DIRS", []):
            files = list(backend.list_files())

            # Should only include the file, not the directory
            self.assertEqual(len(files), 1)
            self.assertIn("/static/authentik/sources/file.svg", files)
