"""Image validation functions for storage backends."""

import io
import os
from defusedxml import ElementTree
from django.core.files.uploadedfile import UploadedFile
from PIL import Image
from structlog.stdlib import get_logger

from authentik.root.storages.constants import ALLOWED_IMAGE_EXTENSIONS
from authentik.root.storages.exceptions import FileValidationError

LOGGER = get_logger()


def _validate_svg_content(content: str) -> bool:
    """Validate SVG content structure.

    Args:
        content: SVG content as string

    Returns:
        bool: True if content is valid SVG, False otherwise
    """
    try:
        # Basic check for SVG element presence
        has_svg_element = "<svg" in content and "</svg>" in content
        if not has_svg_element:
            LOGGER.warning("Missing SVG element or closing tag")
            return False

        # Try to parse as XML to validate structure
        tree = ElementTree.fromstring(content.encode())

        # Validate that the root element or a child is an SVG element
        if tree.tag.lower().endswith("svg"):
            return True

        for child in tree:
            if child.tag.lower().endswith("svg"):
                return True

        LOGGER.warning("SVG element not found in XML structure")
        return False
    except ElementTree.ParseError as e:
        LOGGER.warning("Invalid SVG XML structure", error=str(e))
        return False
    except ValueError as e:
        LOGGER.warning("Invalid SVG content", error=str(e))
        return False
    except Exception as e:
        LOGGER.warning("Unexpected error validating SVG", error=str(e))
        return False


def _validate_ico_content(content: bytes) -> bool:
    """Validate ICO file content.

    Args:
        content: ICO file content as bytes

    Returns:
        bool: True if content is valid ICO, False otherwise
    """
    # ICO files should start with the magic number 0x00 0x00 0x01 0x00
    # but we don't need to check the exact content - just the header
    ICO_HEADER_SIZE = 4
    return len(content) >= ICO_HEADER_SIZE and content.startswith(b"\x00\x00\x01\x00")


def _validate_pillow_image(file: UploadedFile, ext: str, name: str = "") -> bool:
    """Validate image using Pillow.

    Args:
        file: Uploaded file
        ext: File extension
        name: Name of the file for logging purposes

    Returns:
        bool: True if file is valid image, False otherwise
    """
    try:
        with Image.open(file) as img:
            format_to_ext = {
                "JPEG": ".jpg",
                "PNG": ".png",
                "GIF": ".gif",
                "WEBP": ".webp",
            }
            detected_ext = format_to_ext.get(img.format)

            if not detected_ext:
                LOGGER.warning("Unrecognized image format", format=img.format, extension=ext)
                return False

            # Special handling for JPEG extension variants
            is_jpeg = detected_ext == ".jpg" and ext in (".jpg", ".jpeg")
            if not (detected_ext == ext or is_jpeg):
                LOGGER.warning(
                    "File extension doesn't match content",
                    detected_format=img.format,
                    extension=ext,
                )
                return False

            # Verify image data integrity
            img.verify()
            return True

    except Exception as e:
        LOGGER.warning("Image validation failed", error=str(e), name=name)
        raise FileValidationError(f"Failed to validate image: {str(e)}", status_code=415) from e
    finally:
        file.seek(0)


def validate_image_file(file: UploadedFile) -> bool:
    """Validate that the uploaded file is a valid image in an allowed format.

    Args:
        file: The uploaded file to validate

    Returns:
        bool: True if file is valid

    Raises:
        FileValidationError: If file validation fails with specific error message and status code
    """
    if not file:
        raise FileValidationError("No file was provided", status_code=400)

    if not hasattr(file, "content_type") or not hasattr(file, "name"):
        raise FileValidationError("File type could not be determined", status_code=400)

    name = file.name.lower() if file.name else ""
    ext = os.path.splitext(name)[1] if name else ""

    # Check if extension is allowed
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed_exts = ", ".join(ALLOWED_IMAGE_EXTENSIONS.keys())
        raise FileValidationError(
            f"File type '{ext}' is not allowed. Allowed types are: {allowed_exts}",
            status_code=415,  # Unsupported Media Type
        )

    # Check content type
    expected_type = ALLOWED_IMAGE_EXTENSIONS.get(ext)
    if file.content_type != expected_type:
        raise FileValidationError(
            f"Invalid content type '{file.content_type}' for {ext} file. Expected: {expected_type}",
            status_code=415,
        )

    # Validate file content based on type
    try:
        if ext == ".svg":
            content = file.read().decode("utf-8")
            file.seek(0)  # Reset file position
            if not _validate_svg_content(content):
                raise FileValidationError("Invalid SVG content", status_code=415)
        elif ext == ".ico":
            content = file.read()
            file.seek(0)  # Reset file position
            if not _validate_ico_content(content):
                raise FileValidationError("Invalid ICO format", status_code=415)
        else:
            # For other image types, use Pillow validation
            try:
                with Image.open(file) as img:
                    # Verify image data integrity
                    img.verify()
                    # Reset file position after verify
                    file.seek(0)
            except Exception as e:
                raise FileValidationError(f"Invalid image format: {str(e)}", status_code=415) from e

        return True
    except FileValidationError:
        # Re-raise FileValidationError exceptions
        raise
    except Exception as e:
        LOGGER.warning("Unexpected error in image validation", error=str(e), name=name)
        raise FileValidationError(f"Failed to validate image: {str(e)}", status_code=415) from e


def optimize_image(content):
    """Optimize image by resizing if needed and applying compression.

    Used for application icons and other image uploads to reduce file size
    and improve loading performance.

    Args:
        content: File content to optimize (must be an image)

    Returns:
        Optimized content or original content if optimization failed
    """
    if not hasattr(content, "content_type") or not content.content_type.startswith("image/"):
        return content

    # Skip for SVG and ICO files which don't support Pillow optimization
    name = content.name.lower() if hasattr(content, "name") else ""
    ext = os.path.splitext(name)[1] if name else ""
    if ext in (".svg", ".ico"):
        return content

    original_pos = content.tell() if hasattr(content, "tell") else 0

    try:
        # Try to open the image
        img = Image.open(content)

        # Reset file position after reading
        if hasattr(content, "seek"):
            content.seek(0)

        # Check if we need to optimize this image
        if img.format not in ("JPEG", "PNG", "GIF", "WEBP"):
            return content

        # Create in-memory buffer for the optimized image
        buffer = io.BytesIO()

        # Maximum dimension for images in pixels
        MAX_IMAGE_DIMENSION = 512

        # Resize large images to a reasonable size
        if max(img.size) > MAX_IMAGE_DIMENSION:
            LOGGER.debug(
                "Resizing large image", original_size=img.size, format=img.format, name=name
            )
            ratio = float(MAX_IMAGE_DIMENSION) / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Save with optimization based on format
        if img.format == "JPEG":
            img.save(buffer, format="JPEG", quality=85, optimize=True)
        elif img.format == "PNG":
            img.save(buffer, format="PNG", optimize=True)
        elif img.format == "GIF":
            img.save(buffer, format="GIF", optimize=True)
        elif img.format == "WEBP":
            img.save(buffer, format="WEBP", quality=85, method=4)
        else:
            # Fallback for unsupported optimization
            return content

        # Reset buffer position
        buffer.seek(0)

        # Create a new ContentFile with the optimized image
        from django.core.files.base import ContentFile

        optimized = ContentFile(buffer.getvalue())

        # Copy needed attributes from original content
        optimized.name = content.name if hasattr(content, "name") else "optimized.img"
        optimized.content_type = content.content_type if hasattr(content, "content_type") else None

        # Log the optimization results
        if hasattr(content, "size"):
            original_size = content.size
            new_size = len(buffer.getvalue())
            reduction = (1 - (new_size / original_size)) * 100 if original_size > 0 else 0
            LOGGER.info(
                "Image optimized",
                original_size=original_size,
                new_size=new_size,
                reduction_percent=f"{reduction:.1f}%",
                format=img.format,
                name=name,
            )

        return optimized
    except Exception as e:
        LOGGER.warning("Image optimization failed, using original image", error=str(e), name=name)
        # Reset file position on optimization failure
        if hasattr(content, "seek"):
            content.seek(original_pos)
        return content 