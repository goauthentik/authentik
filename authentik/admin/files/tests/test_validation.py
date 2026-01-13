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
            "test%file.png",  # % (but %(theme)s is allowed)
            "test&file.png",  # &
            "test*file.png",  # *
            "test(file).png",  # parentheses (but %(theme)s is allowed)
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

    def test_sanitize_theme_variable_valid(self):
        """Test sanitizing filename with %(theme)s variable"""
        # These should all be valid
        validate_file_name("logo-%(theme)s.png")
        validate_file_name("brand/logo-%(theme)s.svg")
        validate_file_name("images/icon-%(theme)s.png")
        validate_file_name("%(theme)s/logo.png")
        validate_file_name("brand/%(theme)s/logo.png")

    def test_sanitize_theme_variable_multiple(self):
        """Test sanitizing filename with multiple %(theme)s variables"""
        validate_file_name("%(theme)s/logo-%(theme)s.png")

    def test_sanitize_theme_variable_invalid_format(self):
        """Test that partial or malformed theme variables are rejected"""
        invalid_paths = [
            "test%(theme.png",  # missing )s
            "test%theme)s.png",  # missing (
            "test%(themes).png",  # wrong variable name
            "test%(THEME)s.png",  # wrong case
            "test%()s.png",  # empty variable name
        ]

        for path in invalid_paths:
            with self.assertRaises(ValidationError):
                validate_file_name(path)
