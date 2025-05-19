"""Test image validation functions."""

import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from PIL import Image

from authentik.root.storages.validation import validate_image_file
from authentik.root.storages.exceptions import FileValidationError


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

    def test_invalid_image_formats(self):
        """Test validation of invalid image formats"""
        # Test invalid content type
        png_file = self.create_test_image("PNG", "text/plain")
        with self.assertRaises(FileValidationError) as cm:
            validate_image_file(png_file)
        self.assertIn("Invalid content type", str(cm.exception))

        # Test invalid file content
        invalid_file = InMemoryUploadedFile(
            io.BytesIO(b"not an image"),
            "meta_icon",
            "test.png",
            "image/png",
            len(b"not an image"),
            None,
        )
        with self.assertRaises(FileValidationError) as cm:
            validate_image_file(invalid_file)
        self.assertIn("Invalid image format", str(cm.exception))

    def test_svg_validation(self):
        """Test SVG validation"""
        # Test valid SVG
        valid_svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        svg_file = InMemoryUploadedFile(
            io.BytesIO(valid_svg),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            len(valid_svg),
            None,
        )
        self.assertTrue(validate_image_file(svg_file))

        # Test invalid SVG
        invalid_svg = b'<?xml version="1.0"?><not-svg></not-svg>'
        svg_file = InMemoryUploadedFile(
            io.BytesIO(invalid_svg),
            "meta_icon",
            "test.svg",
            "image/svg+xml",
            len(invalid_svg),
            None,
        )
        with self.assertRaises(FileValidationError) as cm:
            validate_image_file(svg_file)
        self.assertIn("Invalid SVG content", str(cm.exception))

    def test_ico_validation(self):
        """Test ICO validation"""
        # Test valid ICO
        valid_ico = b"\x00\x00\x01\x00" + b"\x00" * 16  # Valid ICO header
        ico_file = InMemoryUploadedFile(
            io.BytesIO(valid_ico),
            "meta_icon",
            "test.ico",
            "image/x-icon",
            len(valid_ico),
            None,
        )
        self.assertTrue(validate_image_file(ico_file))

        # Test invalid ICO
        invalid_ico = b"not an ico file"
        ico_file = InMemoryUploadedFile(
            io.BytesIO(invalid_ico),
            "meta_icon",
            "test.ico",
            "image/x-icon",
            len(invalid_ico),
            None,
        )
        with self.assertRaises(FileValidationError) as cm:
            validate_image_file(ico_file)
        self.assertIn("Invalid ICO format", str(cm.exception)) 