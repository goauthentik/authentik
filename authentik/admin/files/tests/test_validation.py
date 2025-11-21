from django.core.exceptions import ValidationError
from django.test import TestCase

from authentik.admin.files.validation import (
    MAX_FILE_NAME_LENGTH,
    MAX_PATH_COMPONENT_LENGTH,
    validate_file_name,
)


class TestSanitizeFilePath(TestCase):
    """Test validate_file_name function"""

    def test_sanitize_valid_filename(self):
        """Test sanitizing valid filename"""
        validate_file_name("test.png")

    def test_sanitize_valid_path_with_directory(self):
        """Test sanitizing valid path with directory"""
        validate_file_name("images/test.png")

    def test_sanitize_valid_path_with_nested_dirs(self):
        """Test sanitizing valid path with nested directories"""
        validate_file_name("dir1/dir2/dir3/test.png")

    def test_sanitize_with_hyphens(self):
        """Test sanitizing filename with hyphens"""
        validate_file_name("test-file-name.png")

    def test_sanitize_with_underscores(self):
        """Test sanitizing filename with underscores"""
        validate_file_name("test_file_name.png")

    def test_sanitize_with_dots(self):
        """Test sanitizing filename with multiple dots"""
        validate_file_name("test.file.name.png")

    def test_sanitize_strips_whitespace(self):
        """Test sanitizing filename strips whitespace"""
        with self.assertRaises(ValidationError):
            validate_file_name("  test.png  ")

    def test_sanitize_removes_duplicate_slashes(self):
        """Test sanitizing path removes duplicate slashes"""
        with self.assertRaises(ValidationError):
            validate_file_name("dir1//dir2///test.png")

    def test_sanitize_empty_path_raises(self):
        """Test sanitizing empty path raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_file_name("")

    def test_sanitize_whitespace_only_raises(self):
        """Test sanitizing whitespace-only path raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_file_name("   ")

    def test_sanitize_invalid_characters_raises(self):
        """Test sanitizing path with invalid characters raises ValidationError"""
        invalid_paths = [
            "test file.png",  # space
            "test@file.png",  # @
            "test#file.png",  # #
            "test$file.png",  # $
            "test%file.png",  # %
            "test&file.png",  # &
            "test*file.png",  # *
            "test(file).png",  # parentheses
            "test[file].png",  # brackets
            "test{file}.png",  # braces
        ]

        for path in invalid_paths:
            with self.assertRaises(ValidationError):
                validate_file_name(path)

    def test_sanitize_absolute_path_raises(self):
        """Test sanitizing absolute path raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_file_name("/absolute/path/test.png")

    def test_sanitize_parent_directory_raises(self):
        """Test sanitizing path with parent directory reference raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_file_name("../test.png")

    def test_sanitize_nested_parent_directory_raises(self):
        """Test sanitizing path with nested parent directory reference raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_file_name("dir1/../test.png")

    def test_sanitize_starts_with_dot_raises(self):
        """Test sanitizing path starting with dot raises ValidationError"""
        with self.assertRaises(ValidationError):
            validate_file_name(".hidden")

    def test_sanitize_too_long_path_raises(self):
        """Test sanitizing too long path raises ValidationError"""
        long_path = "a" * (MAX_FILE_NAME_LENGTH + 1) + ".png"

        with self.assertRaises(ValidationError):
            validate_file_name(long_path)

    def test_sanitize_too_long_component_raises(self):
        """Test sanitizing path with too long component raises ValidationError"""
        long_component = "a" * (MAX_PATH_COMPONENT_LENGTH + 1)
        path = f"dir/{long_component}.png"

        with self.assertRaises(ValidationError):
            validate_file_name(path)
