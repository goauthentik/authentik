"""Test file validation utilities"""

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.admin.files.constants import (
    MAX_FILE_PATH_LENGTH,
    MAX_FILE_SIZE_BYTES,
    MAX_PATH_COMPONENT_LENGTH,
)
from authentik.admin.files.validation import (
    sanitize_file_path,
    validate_file_size,
    validate_file_type,
)


class TestSanitizeFilePath(TestCase):
    """Test sanitize_file_path function"""

    def test_sanitize_valid_filename(self):
        """Test sanitizing valid filename"""
        result = sanitize_file_path("test.png")
        self.assertEqual(result, "test.png")

    def test_sanitize_valid_path_with_directory(self):
        """Test sanitizing valid path with directory"""
        result = sanitize_file_path("images/test.png")
        self.assertEqual(result, "images/test.png")

    def test_sanitize_valid_path_with_nested_dirs(self):
        """Test sanitizing valid path with nested directories"""
        result = sanitize_file_path("dir1/dir2/dir3/test.png")
        self.assertEqual(result, "dir1/dir2/dir3/test.png")

    def test_sanitize_with_hyphens(self):
        """Test sanitizing filename with hyphens"""
        result = sanitize_file_path("test-file-name.png")
        self.assertEqual(result, "test-file-name.png")

    def test_sanitize_with_underscores(self):
        """Test sanitizing filename with underscores"""
        result = sanitize_file_path("test_file_name.png")
        self.assertEqual(result, "test_file_name.png")

    def test_sanitize_with_dots(self):
        """Test sanitizing filename with multiple dots"""
        result = sanitize_file_path("test.file.name.png")
        self.assertEqual(result, "test.file.name.png")

    def test_sanitize_strips_whitespace(self):
        """Test sanitizing filename strips whitespace"""
        result = sanitize_file_path("  test.png  ")
        self.assertEqual(result, "test.png")

    def test_sanitize_removes_duplicate_slashes(self):
        """Test sanitizing path removes duplicate slashes"""
        result = sanitize_file_path("dir1//dir2///test.png")
        self.assertEqual(result, "dir1/dir2/test.png")

    def test_sanitize_empty_path_raises(self):
        """Test sanitizing empty path raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            sanitize_file_path("")

        self.assertIn("cannot be empty", str(context.exception))

    def test_sanitize_whitespace_only_raises(self):
        """Test sanitizing whitespace-only path raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            sanitize_file_path("   ")

        # Whitespace gets stripped, then fails regex check (empty string doesn't match pattern)
        self.assertIn("can only contain", str(context.exception))

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
            with self.assertRaises(ValidationError) as context:
                sanitize_file_path(path)

            self.assertIn("can only contain", str(context.exception))

    def test_sanitize_absolute_path_raises(self):
        """Test sanitizing absolute path raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            sanitize_file_path("/absolute/path/test.png")

        self.assertIn("Absolute paths are not allowed", str(context.exception))

    def test_sanitize_parent_directory_raises(self):
        """Test sanitizing path with parent directory reference raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            sanitize_file_path("../test.png")

        self.assertIn("Parent directory references", str(context.exception))

    def test_sanitize_nested_parent_directory_raises(self):
        """Test sanitizing path with nested parent directory reference raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            sanitize_file_path("dir1/../test.png")

        self.assertIn("Parent directory references", str(context.exception))

    def test_sanitize_starts_with_dot_raises(self):
        """Test sanitizing path starting with dot raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            sanitize_file_path(".hidden")

        self.assertIn("cannot start with '.'", str(context.exception))

    def test_sanitize_too_long_path_raises(self):
        """Test sanitizing too long path raises ValidationError"""
        long_path = "a" * (MAX_FILE_PATH_LENGTH + 1) + ".png"

        with self.assertRaises(ValidationError) as context:
            sanitize_file_path(long_path)

        self.assertIn("File path too long", str(context.exception))

    def test_sanitize_too_long_component_raises(self):
        """Test sanitizing path with too long component raises ValidationError"""
        long_component = "a" * (MAX_PATH_COMPONENT_LENGTH + 1)
        path = f"dir/{long_component}.png"

        with self.assertRaises(ValidationError) as context:
            sanitize_file_path(path)

        self.assertIn("Path component too long", str(context.exception))


class TestValidateFileSize(TestCase):
    """Test validate_file_size function"""

    def test_validate_size_within_limit(self):
        """Test validating file size within limit"""
        # Should not raise
        validate_file_size(1024)  # 1KB
        validate_file_size(MAX_FILE_SIZE_BYTES)  # Exactly at limit

    def test_validate_size_exceeds_limit(self):
        """Test validating file size exceeding limit raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            validate_file_size(MAX_FILE_SIZE_BYTES + 1)

        error_dict = context.exception.detail
        self.assertIn("file", error_dict)
        self.assertIn("exceeds maximum", str(error_dict["file"]))

    def test_validate_size_custom_limit(self):
        """Test validating file size with custom limit"""
        custom_limit = 1024  # 1KB

        # Within limit - should not raise
        validate_file_size(512, custom_limit)

        # Exceeds limit - should raise
        with self.assertRaises(ValidationError):
            validate_file_size(2048, custom_limit)

    def test_validate_size_zero(self):
        """Test validating zero file size"""
        # Should not raise
        validate_file_size(0)

    def test_validate_size_error_message_format(self):
        """Test error message includes sizes in MB"""
        with self.assertRaises(ValidationError) as context:
            validate_file_size(10 * 1024 * 1024)  # 10MB (exceeds default 3MB)

        error_msg = str(context.exception.detail["file"])
        self.assertIn("MB", error_msg)
        self.assertIn("10", error_msg)  # Actual size
        self.assertIn("3", error_msg)  # Max size


class TestValidateFileType(TestCase):
    """Test validate_file_type function"""

    def test_validate_type_media_image(self):
        """Test validating image MIME type for media usage"""
        # Should not raise
        validate_file_type("image/png", "media")
        validate_file_type("image/jpeg", "media")
        validate_file_type("image/svg+xml", "media")
        validate_file_type("image/gif", "media")

    def test_validate_type_media_non_image_raises(self):
        """Test validating non-image MIME type for media raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            validate_file_type("application/pdf", "media")

        error_dict = context.exception.detail
        self.assertIn("file", error_dict)
        self.assertIn("not allowed", str(error_dict["file"]))
        self.assertIn("image/", str(error_dict["file"]))

    def test_validate_type_media_octet_stream_raises(self):
        """Test validating octet-stream MIME type for media raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            validate_file_type("application/octet-stream", "media")

        error_dict = context.exception.detail
        self.assertIn("not allowed", str(error_dict["file"]))

    def test_validate_type_reports_no_restriction(self):
        """Test validating any MIME type for reports usage (no restrictions)"""
        # Reports usage has no restrictions (None in ALLOWED_MIME_TYPES)
        # Should not raise for any type
        validate_file_type("application/pdf", "reports")
        validate_file_type("text/csv", "reports")
        validate_file_type("application/octet-stream", "reports")
        validate_file_type("image/png", "reports")

    def test_validate_type_empty_content_type(self):
        """Test validating empty content type"""
        with self.assertRaises(ValidationError):
            validate_file_type("", "media")

    def test_validate_type_none_content_type(self):
        """Test validating None content type"""
        with self.assertRaises(ValidationError):
            validate_file_type(None, "media")

    def test_validate_type_unknown_usage(self):
        """Test validating with unknown usage type"""
        # Unknown usage should have no restrictions (returns None from dict)
        # Should not raise
        validate_file_type("application/pdf", "unknown_usage")

    def test_validate_type_error_message_shows_allowed_types(self):
        """Test error message shows allowed MIME types"""
        with self.assertRaises(ValidationError) as context:
            validate_file_type("text/plain", "media")

        error_msg = str(context.exception.detail["file"])
        self.assertIn("Allowed types:", error_msg)
        self.assertIn("image/", error_msg)

    def test_validate_type_case_sensitive(self):
        """Test MIME type validation is case-sensitive (lowercase expected)"""
        # Standard MIME types are lowercase
        validate_file_type("image/png", "media")

        # Uppercase should not match (MIME types are case-insensitive in HTTP but
        # our validation uses startswith which is case-sensitive
        with self.assertRaises(ValidationError):
            validate_file_type("IMAGE/PNG", "media")

    def test_validate_type_prefix_matching(self):
        """Test MIME type validation uses prefix matching"""
        # Any image/* type should be allowed
        validate_file_type("image/png", "media")
        validate_file_type("image/jpeg", "media")
        validate_file_type("image/webp", "media")
        validate_file_type("image/x-icon", "media")
        validate_file_type("image/svg+xml", "media")
