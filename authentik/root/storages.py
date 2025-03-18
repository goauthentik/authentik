"""Storage backends for authentik with multi-tenant support.

This module provides custom storage backends for handling file storage in a multi-tenant
environment. It supports both filesystem and S3 storage options with proper tenant isolation.
"""

import os
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, NoRegionError
from defusedxml import ElementTree
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile
from django.db import connection
from PIL import Image
from storages.backends.s3 import S3Storage as BaseS3Storage
from storages.utils import safe_join
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()

# Mapping of allowed file extensions to their corresponding MIME types
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


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


class FileValidationError(SuspiciousOperation):
    """Custom exception for file validation errors with status code and user message."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.user_message = message


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
                raise FileValidationError("Invalid SVG file format", status_code=415)
        elif ext == ".ico":
            content = file.read()
            file.seek(0)  # Reset file position
            if not _validate_ico_content(content):
                raise FileValidationError("Invalid ICO file format", status_code=415)
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


class TenantAwareStorage:
    """Mixin providing tenant-aware path functionality for storage backends."""

    @property
    def tenant_prefix(self) -> str:
        """Get current tenant schema prefix.

        Returns:
            str: The current tenant's schema name from the database connection.
        """
        return connection.schema_name

    @tenant_prefix.deleter
    def tenant_prefix(self):
        """Deleter for tenant_prefix property.

        This is required for tests that need to clean up tenant-specific resources.
        """
        # No-op deleter as the tenant_prefix is derived from the connection
        pass

    def get_tenant_path(self, name: str) -> str:
        """Get tenant-specific path for storage.

        Args:
            name (str): Original file path/name.

        Returns:
            str: Path prefixed with tenant identifier for proper isolation.
        """
        return str(Path(self.tenant_prefix) / name)


class FileStorage(TenantAwareStorage, FileSystemStorage):
    """Multi-tenant filesystem storage backend."""

    def __init__(self, *args, **kwargs):
        """Initialize the storage backend with tenant-aware configuration.

        Creates the base storage directory if it doesn't exist and sets up proper
        permissions and logging.

        Args:
            *args: Variable length argument list passed to parent classes
            **kwargs: Arbitrary keyword arguments passed to parent classes

        Raises:
            PermissionError: If storage directory cannot be created due to permissions
            OSError: If storage directory cannot be created due to filesystem errors
        """
        super().__init__(*args, **kwargs)
        self._base_path = Path(self.location)
        try:
            # Ensure the base directory exists with correct permissions
            os.makedirs(self._base_path, exist_ok=True)

            # Also create tenant-specific directory
            tenant_dir = self._base_path / self.tenant_prefix
            os.makedirs(tenant_dir, exist_ok=True)

            LOGGER.debug(
                "Storage directories initialized",
                base_path=str(self._base_path),
                tenant_dir=str(tenant_dir),
            )
        except PermissionError as e:
            LOGGER.error(
                "Permission error creating storage directory",
                path=str(self._base_path),
                error=str(e),
            )
            raise PermissionError(
                f"Cannot create storage directory '{self._base_path}'. Permission denied."
            ) from e
        except OSError as e:
            LOGGER.error(
                "OS error creating storage directory", path=str(self._base_path), error=str(e)
            )
            raise OSError(
                f"Cannot create storage directory '{self._base_path}'. System error: {str(e)}"
            ) from e

    def get_valid_name(self, name: str) -> str:
        """Return a sanitized filename safe for storage.

        Removes path components and applies additional sanitization from parent class.

        Args:
            name (str): Original filename

        Returns:
            str: Sanitized filename safe for storage
        """
        name = os.path.basename(name)
        return super().get_valid_name(name)

    @property
    def base_location(self) -> Path:
        """Get base storage directory including tenant prefix.

        Returns:
            Path: Complete path to tenant-specific storage directory
        """
        return Path(settings.MEDIA_ROOT) / self.tenant_prefix

    @property
    def location(self) -> str:
        """Get absolute path to storage directory.

        Returns:
            str: Absolute filesystem path to tenant storage directory
        """
        return os.path.abspath(self.base_location)

    @property
    def base_url(self) -> str:
        """Get base URL for serving stored files with tenant prefix.

        Ensures proper URL composition by validating and fixing MEDIA_URL format.

        Returns:
            str: Base URL with proper tenant prefix for serving files
        """
        base_url = settings.MEDIA_URL
        if not base_url.endswith("/"):
            LOGGER.warning(
                "MEDIA_URL should end with '/' for proper URL composition", current_value=base_url
            )
            base_url += "/"
        return f"{base_url}{self.tenant_prefix}/"

    def _validate_path(self, name: str) -> str:
        """Validate the path for security issues.

        Ensures that the path does not contain suspicious characters or attempt to
        traverse outside the storage directory.

        Args:
            name (str): Name of the file to validate

        Returns:
            str: Validated path name

        Raises:
            SuspiciousOperation: If the path contains invalid characters or traversal attempts
        """
        if not name:
            raise SuspiciousOperation("Empty filename is not allowed")

        # Check for directory traversal attempts
        if ".." in name.split("/") or ".." in name.split("\\"):
            raise SuspiciousOperation(f"Invalid characters in filename '{name}'")

        # Convert to posix path and normalize
        clean_name = str(Path(name).as_posix())

        # Ensure the path is relative and doesn't start with / or other special patterns
        while clean_name.startswith("/"):
            clean_name = clean_name[1:]

        # Final validation using safe_join
        try:
            # We use safe_join for final validation
            safe_join("", clean_name)
        except ValueError as e:
            raise SuspiciousOperation(f"Invalid characters in filename '{name}'") from e

        return clean_name

    def path(self, name: str) -> str:
        """Return the absolute path to the file.

        Args:
            name (str): The name of the file including tenant prefix

        Returns:
            str: The absolute path to the file on the filesystem

        Raises:
            SuspiciousOperation: If the file path attempts to traverse outside the storage directory
        """
        # Apply tenant prefix if not already included in the name
        if not name.startswith(self.tenant_prefix):
            tenant_path = self.get_tenant_path(name)
        else:
            tenant_path = name

        # Normalize the path to prevent path traversal
        name = self._validate_path(tenant_path)

        # Join the base location with the validated name
        return str(self.base_location / name)

    def _save(self, name: str, content) -> str:
        """Save the file with content validation and tenant prefix application.

        Args:
            name (str): Name of the file
            content: File content to save

        Returns:
            str: Name of the saved file with tenant prefix

        Raises:
            FileValidationError: If file validation fails (for images)
        """
        # First check if this is an image upload that needs validation
        if hasattr(content, "content_type") and content.content_type.startswith("image/"):
            try:
                validate_image_file(content)
            except FileValidationError as e:
                LOGGER.warning("Image validation failed", name=name, error=str(e))
                raise

        # Apply tenant prefix to ensure isolation
        tenant_name = self.get_tenant_path(name)

        # Perform regular file save
        file_path = self.path(tenant_name)

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

        LOGGER.debug("Saving file", name=name, path=file_path)

        # Call parent class _save with the tenant-prefixed path
        saved_name = super()._save(tenant_name, content)

        return saved_name


class S3Storage(TenantAwareStorage, BaseS3Storage):
    """Multi-tenant S3 (compatible/Amazon) storage backend."""

    CONFIG_KEYS = {
        "session_profile": "storage.media.s3.session_profile",
        "access_key": "storage.media.s3.access_key",
        "secret_key": "storage.media.s3.secret_key",
        "security_token": "storage.media.s3.security_token",
        "bucket_name": "storage.media.s3.bucket_name",
        "region_name": "storage.media.s3.region_name",
        "endpoint_url": "storage.media.s3.endpoint",
        "custom_domain": "storage.media.s3.custom_domain",
    }

    def __init__(self, **kwargs):
        """Initialize S3Storage with configuration.

        Args:
            **kwargs: Configuration options passed to parent S3Storage

        Raises:
            ImproperlyConfigured: If AWS credentials or configuration is invalid
        """
        # Pre-fetch configuration values
        self._session_profile = self._get_config_value("session_profile")
        self._access_key = self._get_config_value("access_key")
        self._secret_key = self._get_config_value("secret_key")
        self._security_token = self._get_config_value("security_token")
        self._bucket_name = self._get_config_value("bucket_name")
        self._region_name = self._get_config_value("region_name")
        self._endpoint_url = self._get_config_value("endpoint_url")
        self._custom_domain = self._get_config_value("custom_domain")

        # Debug
        LOGGER.debug(
            "S3Storage initialization",
            has_session_profile=bool(self._session_profile),
            has_access_key=(
                bool(self._access_key) and self._access_key[:4] + "..."
                if self._access_key
                else None
            ),
            has_secret_key=bool(self._secret_key),
            has_security_token=bool(self._security_token),
            bucket_name=self._bucket_name,
            region_name=self._region_name,
            endpoint_url=self._endpoint_url,
            custom_domain=self._custom_domain,
            tenant=getattr(self, "tenant_prefix", "unknown"),
            kwargs_keys=list(kwargs.keys()),
        )

        self._validate_configuration()

        # Update kwargs with our configuration values
        settings = kwargs.copy()
        settings.update(
            {
                "session_profile": self._session_profile,
                "access_key": self._access_key,
                "secret_key": self._secret_key,
                "security_token": self._security_token,
                "bucket_name": self._bucket_name,
                "region_name": self._region_name,
                "endpoint_url": self._endpoint_url,
                "custom_domain": self._custom_domain,
                "querystring_auth": True,
                "querystring_expire": 3600,
            }
        )

        LOGGER.debug(
            "S3Storage parent initialization",
            settings_keys=list(settings.keys()),
            tenant=getattr(self, "tenant_prefix", "unknown"),
        )

        # Initialize parent class with cleaned settings
        try:
            super().__init__(**settings)
            LOGGER.debug(
                "S3Storage parent initialization successful",
                tenant=getattr(self, "tenant_prefix", "unknown"),
            )
        except Exception as e:
            LOGGER.error(
                "S3Storage parent initialization failed",
                error=str(e),
                error_type=type(e).__name__,
                tenant=getattr(self, "tenant_prefix", "unknown"),
            )
            raise

        self._client = None
        self._s3_client = None
        self._bucket = None
        self._file_mapping = {}

    def _get_config_value(self, key: str) -> str | None:
        """Get refreshed configuration value from environment.

        Args:
            key (str): Configuration key from CONFIG_KEYS

        Returns:
            str | None: Configuration value if set, None otherwise
        """
        return CONFIG.refresh(self.CONFIG_KEYS[key], None)

    def _validate_configuration(self):
        """Validate S3 configuration and credentials.

        Checks that all required configuration keys are set and that the
        bucket exists and is accessible.

        Raises:
            ImproperlyConfigured: If S3 configuration is incomplete or invalid
            ClientError: If bucket doesn't exist or cannot be accessed
        """
        # Check that all required configuration keys are set
        for key in self.CONFIG_KEYS.values():
            val = self._get_config_value(key)
            if not val:
                LOGGER.error("Missing required S3 configuration", key=key)
                raise ImproperlyConfigured(f"Missing required S3 configuration: {key}")

        # Validate bucket exists and is accessible
        try:
            self.client.head_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "404":
                LOGGER.error("S3 bucket does not exist", bucket=self._bucket_name)
                raise ImproperlyConfigured(f"S3 bucket '{self._bucket_name}' does not exist") from e
            elif error_code == "403":
                LOGGER.error("No permission to access S3 bucket", bucket=self._bucket_name)
                raise ImproperlyConfigured(
                    f"No permission to access S3 bucket '{self._bucket_name}'"
                ) from e
            else:
                LOGGER.error(
                    "Error accessing S3 bucket",
                    bucket=self._bucket_name,
                    error=str(e),
                    code=error_code,
                )
                raise

        LOGGER.debug("S3 configuration validated successfully", bucket=self._bucket_name)

    @property
    def client(self):
        """Get or create boto3 S3 client with current credentials.

        Creates a new boto3 S3 client if none exists, using current AWS credentials.

        Returns:
            boto3.client: Configured S3 client instance

        Raises:
            ImproperlyConfigured: If AWS credentials are invalid
            ClientError: If AWS client initialization fails
        """
        if not self._client or not self._s3_client:
            try:
                LOGGER.debug(
                    "Creating boto3 session",
                    profile_name=self._session_profile,
                    has_access_key=(
                        bool(self._access_key) and self._access_key[:4] + "..."
                        if self._access_key
                        else None
                    ),
                    has_secret_key=bool(self._secret_key),
                    has_security_token=bool(self._security_token),
                    tenant=self.tenant_prefix,
                )

                session = boto3.Session(
                    profile_name=self._session_profile,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    aws_session_token=self._security_token,
                )

                LOGGER.debug(
                    "Boto3 session created",
                    available_profiles=session.available_profiles,
                    profile_name=session.profile_name,
                    region_name=session.region_name,
                    tenant=self.tenant_prefix,
                )

                client_kwargs = {
                    "region_name": self._region_name,
                }
                if self._endpoint_url:
                    s3_config = Config(s3={"addressing_style": "path"})
                    client_kwargs.update(
                        {
                            "endpoint_url": self._endpoint_url,
                            "config": s3_config,
                        }
                    )
                    LOGGER.debug(
                        "Using custom S3 endpoint with path-style addressing",
                        endpoint=self._endpoint_url,
                        tenant=self.tenant_prefix,
                    )

                LOGGER.debug(
                    "Creating S3 resource and client",
                    client_kwargs=client_kwargs,
                    tenant=self.tenant_prefix,
                )

                self._client = session.resource("s3", **client_kwargs)
                self._s3_client = session.client("s3", **client_kwargs)

                LOGGER.debug(
                    "Created S3 resource and client",
                    session_profile=self._session_profile,
                    region=self._region_name,
                    endpoint=self._endpoint_url,
                    tenant=self.tenant_prefix,
                )
            except (NoCredentialsError, NoRegionError) as e:
                LOGGER.critical(
                    "AWS credentials/region configuration error",
                    error=str(e),
                    error_type=type(e).__name__,
                    tenant=self.tenant_prefix,
                )
                raise ImproperlyConfigured(f"AWS configuration error: {e}") from e

        return self._client

    @property
    def bucket(self):
        """Get or create S3 bucket instance with access validation.

        Creates a new S3 bucket instance if none exists and validates access permissions.

        Returns:
            boto3.s3.Bucket: Validated S3 bucket instance

        Raises:
            ImproperlyConfigured: If bucket doesn't exist or permissions are insufficient
            ClientError: If bucket access fails
        """
        if not self._bucket:
            bucket_name = self._get_config_value("bucket_name")
            try:
                # First check credentials by listing buckets
                try:
                    LOGGER.debug(
                        "Listing S3 buckets to validate credentials",
                        tenant=self.tenant_prefix,
                    )
                    buckets = list(self.client.buckets.all())
                    bucket_names = [b.name for b in buckets]
                    LOGGER.debug(
                        "Successfully listed S3 buckets",
                        bucket_count=len(bucket_names),
                        buckets=bucket_names,
                        target_bucket=bucket_name,
                        bucket_exists=bucket_name in bucket_names,
                        tenant=self.tenant_prefix,
                    )
                except (ClientError, NoCredentialsError) as e:
                    if isinstance(e, ClientError):
                        error_code = e.response.get("Error", {}).get("Code", "Unknown")
                        error_message = e.response.get("Error", {}).get("Message", "Unknown error")
                        LOGGER.critical(
                            "Invalid AWS credentials",
                            error_code=error_code,
                            message=error_message,
                            response=str(e.response),
                            tenant=self.tenant_prefix,
                        )
                    else:
                        LOGGER.critical(
                            "Invalid AWS credentials",
                            error=str(e),
                            error_type=type(e).__name__,
                            tenant=self.tenant_prefix,
                        )
                    raise ImproperlyConfigured("Invalid AWS credentials") from e

                # Then check bucket existence and permissions
                try:
                    LOGGER.debug(
                        "Checking S3 bucket existence and permissions",
                        bucket=bucket_name,
                        tenant=self.tenant_prefix,
                    )
                    bucket = self.client.Bucket(bucket_name)
                    # Try to access the bucket to verify permissions
                    list(bucket.objects.limit(1))
                    LOGGER.debug(
                        "Successfully verified S3 bucket access",
                        bucket=bucket_name,
                        tenant=self.tenant_prefix,
                    )
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    error_message = e.response.get("Error", {}).get("Message", "Unknown error")
                    if error_code == "NoSuchBucket":
                        LOGGER.error(
                            "S3 bucket does not exist",
                            bucket=bucket_name,
                            error_code=error_code,
                            message=error_message,
                            tenant=self.tenant_prefix,
                        )
                        raise ImproperlyConfigured(
                            f"S3 bucket '{bucket_name}' does not exist"
                        ) from e
                    elif error_code in ("AccessDenied", "AllAccessDisabled"):
                        LOGGER.error(
                            "Permission denied accessing S3 bucket",
                            bucket=bucket_name,
                            error_code=error_code,
                            message=error_message,
                            response=str(e.response),
                            tenant=self.tenant_prefix,
                        )
                        raise ImproperlyConfigured(
                            f"Permission denied accessing S3 bucket '{bucket_name}'. "
                            "Please verify your IAM permissions"
                        ) from e
                    else:
                        LOGGER.error(
                            "Error accessing S3 bucket",
                            bucket=bucket_name,
                            error_code=error_code,
                            message=error_message,
                            response=str(e.response),
                            tenant=self.tenant_prefix,
                        )
                        raise ImproperlyConfigured(
                            f"Error accessing S3 bucket '{bucket_name}': {str(e)}"
                        ) from e

                LOGGER.debug(
                    "Creating S3 bucket object",
                    bucket=bucket_name,
                    tenant=self.tenant_prefix,
                )
                self._bucket = bucket
                LOGGER.info(
                    "Successfully connected to S3 bucket",
                    bucket=bucket_name,
                    region=self._region_name,
                    endpoint=self._endpoint_url,
                    tenant=self.tenant_prefix,
                )

            except Exception as e:
                LOGGER.error(
                    "Unexpected error accessing S3",
                    error=str(e),
                    error_type=type(e).__name__,
                    tenant=self.tenant_prefix,
                )
                if isinstance(e, ImproperlyConfigured):
                    raise
                raise ImproperlyConfigured(f"S3 configuration error: {str(e)}") from e

        return self._bucket

    def get_valid_name(self, name: str) -> str:
        """Return a sanitized filename safe for S3 storage.

        Removes path components and applies additional sanitization.

        Args:
            name (str): Original filename

        Returns:
            str: Sanitized filename safe for S3 storage
        """
        # For S3, we want to preserve the directory structure
        dir_name = os.path.dirname(name)
        base_name = os.path.basename(name)
        base_name = super().get_valid_name(base_name)
        if dir_name:
            return os.path.join(dir_name, base_name)
        return base_name

    def _randomize_filename(self, filename: str) -> str:
        """Generate a randomized filename to prevent conflicts and overwriting.

        Creates a unique filename by injecting a UUID while preserving the original
        extension for proper file type handling.

        Args:
            filename (str): Original filename

        Returns:
            str: Randomized filename with UUID
        """
        if not filename:
            raise SuspiciousOperation("Could not derive file name from empty string")

        # Split the filename into base and extension
        base_name, ext = os.path.splitext(os.path.basename(filename))

        # Generate UUID
        unique_id = str(uuid.uuid4())

        # Create new filename with UUID and original extension
        randomized = f"{unique_id}{ext}"

        LOGGER.debug("Randomized filename", original=filename, randomized=randomized)

        return randomized

    def _normalize_name(self, name: str) -> str:
        """Normalize file name for S3 storage.

        Ensures the name is properly prefixed with 'media/tenant/' and doesn't
        contain any suspicious characters that could lead to path traversal.

        Args:
            name (str): Original file name

        Returns:
            str: Normalized S3 key for the file

        Raises:
            SuspiciousFileOperation: If the name contains invalid characters
        """
        # Clean the name by removing leading slashes and normalizing to forward slashes
        clean_name = str(Path(name).as_posix())
        while clean_name.startswith("/"):
            clean_name = clean_name[1:]

        # Check for directory traversal attempts
        if ".." in clean_name.split("/"):
            raise SuspiciousOperation(f"Invalid characters in filename '{name}'")

        # Add media prefix if not already present
        if not clean_name.startswith("media/"):
            clean_name = f"media/{clean_name}"

        # Final validation
        try:
            safe_join("", clean_name)
        except ValueError as e:
            raise SuspiciousOperation(f"Invalid characters in filename '{name}'") from e

        # Log normalization result
        LOGGER.debug("Normalized file name", original=name, normalized=clean_name)

        return clean_name

    def _delete_previous_instance_file(self, content) -> None:
        """Delete the previous file from the model instance if it exists."""
        if not (hasattr(content, "_instance") and hasattr(content._instance, content._field.name)):
            return

        old_file = getattr(content._instance, content._field.name)
        if not old_file:
            return

        try:
            old_name = old_file.name
            LOGGER.debug(
                "Deleting previous file from model instance",
                name=old_name,
                tenant=self.tenant_prefix,
            )
            old_file.delete(save=False)  # Don't save the model yet
        except Exception as e:
            LOGGER.warning(
                "Failed to delete old file from model instance",
                name=old_name,
                error=str(e),
                error_type=type(e).__name__,
                tenant=self.tenant_prefix,
            )

    def _delete_previous_mapped_file(self, name: str) -> None:
        """Delete the previous file with the same name from S3 if it exists in the mapping."""
        if name not in self._file_mapping:
            return

        old_name = self._file_mapping[name]
        try:
            LOGGER.debug(
                "Deleting previous file with same name",
                name=name,
                old_key=old_name,
                tenant=self.tenant_prefix,
            )
            self.bucket.Object(old_name).delete()
            self._file_mapping.pop(name)
        except Exception as e:
            LOGGER.warning(
                "Failed to delete old file during replacement",
                name=name,
                old_key=old_name,
                error=str(e),
                error_type=type(e).__name__,
                tenant=self.tenant_prefix,
            )

    def _upload_to_s3(self, normalized_name: str, content) -> None:
        """Upload the file to S3 and verify the upload."""
        LOGGER.debug(
            "Creating S3 object for upload",
            key=normalized_name,
            tenant=self.tenant_prefix,
        )
        obj = self.bucket.Object(normalized_name)

        LOGGER.debug(
            "Uploading file to S3",
            key=normalized_name,
            tenant=self.tenant_prefix,
        )
        upload_kwargs = {}
        if hasattr(content, "content_type") and content.content_type:
            upload_kwargs["ContentType"] = content.content_type

        obj.upload_fileobj(content, ExtraArgs=upload_kwargs if upload_kwargs else None)
        self._verify_upload(obj, normalized_name)

    def _verify_upload(self, obj, normalized_name: str) -> None:
        """Verify that the upload was successful."""
        LOGGER.debug(
            "Upload to S3 completed, verifying object",
            key=normalized_name,
            tenant=self.tenant_prefix,
        )

        try:
            obj_data = obj.load()
            LOGGER.debug(
                "Successfully verified S3 upload",
                key=normalized_name,
                object_data=str(obj_data),
                tenant=self.tenant_prefix,
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", "Unknown error")
            LOGGER.error(
                "Failed to verify S3 upload",
                key=normalized_name,
                error_code=error_code,
                message=error_message,
                response=str(e.response),
                tenant=self.tenant_prefix,
            )
            self._cleanup_failed_upload(obj, normalized_name)
            raise

    def _cleanup_failed_upload(self, obj, normalized_name: str) -> None:
        """Clean up a failed upload by deleting the object."""
        try:
            LOGGER.debug(
                "Cleaning up failed upload",
                key=normalized_name,
                tenant=self.tenant_prefix,
            )
            obj.delete()
        except Exception as cleanup_error:
            LOGGER.warning(
                "Failed to clean up after failed upload",
                key=normalized_name,
                error=str(cleanup_error),
                tenant=self.tenant_prefix,
            )

    def _log_save_attempt(
        self, name: str, randomized_name: str, normalized_name: str, content
    ) -> None:
        """Log information about the file being saved to S3."""
        LOGGER.info(
            "Saving image to S3",
            original_name=name,
            randomized_name=randomized_name,
            normalized_name=normalized_name,
            content_type=getattr(content, "content_type", None),
            content_length=getattr(content, "size", None),
            tenant=self.tenant_prefix,
        )

    def _log_save_success(self, normalized_name: str, name: str) -> None:
        """Log successful file save to S3."""
        LOGGER.debug(
            "Image saved successfully to S3",
            key=normalized_name,
            original_name=name,
            tenant=self.tenant_prefix,
        )

    def _handle_save_error(self, e: Exception, name: str, normalized_name: str) -> None:
        """Handle and log errors during file save operation."""
        if isinstance(e, ClientError):
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", "Unknown error")
            LOGGER.error(
                "Unexpected error saving image to S3",
                name=name,
                key=normalized_name,
                error_code=error_code,
                message=error_message,
                response=str(e.response),
                tenant=self.tenant_prefix,
            )
        else:
            LOGGER.error(
                "Unexpected error saving image to S3",
                name=name,
                key=normalized_name,
                error=str(e),
                error_type=type(e).__name__,
                tenant=self.tenant_prefix,
            )
        raise e

    def _save(self, name: str, content) -> str:
        """Save file to S3 with validation and error handling.

        Args:
            name (str): Name of the file to save
            content: File content to save (file-like object)

        Returns:
            str: Name of the file that was saved (with tenant prefix)

        Raises:
            FileValidationError: If image validation fails
            ClientError: If S3 upload fails
        """
        # First validate content if it's an image
        if hasattr(content, "content_type") and content.content_type.startswith("image/"):
            try:
                validate_image_file(content)
            except FileValidationError as e:
                LOGGER.warning("Image validation failed", name=name, error=str(e))
                raise

        # Generate a randomized filename to prevent conflicts
        randomized_name = self._randomize_filename(name)

        # Add tenant prefix for isolation
        tenant_path = self.get_tenant_path(randomized_name)

        # Normalize the name for S3 (no leading slash)
        normalized_name = self._normalize_name(tenant_path)

        # Log the save attempt
        self._log_save_attempt(name, randomized_name, normalized_name, content)

        # Get S3 object for this file
        obj = self.bucket.Object(normalized_name)

        try:
            # Upload the file to S3
            self._upload_to_s3(normalized_name, content)

            # Verify the upload was successful
            self._verify_upload(obj, normalized_name)

            # Log successful save
            self._log_save_success(normalized_name, name)

            # Return the name with tenant prefix to ensure proper path reference
            return tenant_path
        except Exception as e:
            # Clean up failed upload attempts
            self._cleanup_failed_upload(obj, normalized_name)

            # Handle errors based on type
            self._handle_save_error(e, name, normalized_name)

            # Re-raise the exception after cleanup and logging
            raise

    def delete(self, name: str) -> None:
        """Delete file from S3 storage.

        Attempts to delete the file using either the mapped normalized name
        or by normalizing the provided name.

        Args:
            name (str): Name of the file to delete

        Note:
            Silently ignores 404 errors when the file doesn't exist
        """
        try:
            # Get normalized name from mapping or normalize original name
            normalized_name = self._file_mapping.get(name, self._normalize_name(name))
            obj = self.bucket.Object(normalized_name)

            # Delete the object
            obj.delete()

            # Remove from mapping if exists
            self._file_mapping.pop(name, None)

            LOGGER.debug(
                "File deleted from S3",
                key=normalized_name,
                tenant=self.tenant_prefix,
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "404":
                LOGGER.error(
                    "Failed to delete file from S3",
                    name=name,
                    error=str(e),
                    tenant=self.tenant_prefix,
                )
                raise
            LOGGER.debug(
                "File not found during delete",
                name=name,
                tenant=self.tenant_prefix,
            )

    def url(self, name: str, **kwargs) -> str:
        """Generate URL for accessing the file.

        Generates a signed URL for the file since buckets are private.
        AWS signing parameters are required and preserved for authenticated access.

        Args:
            name (str): Name of the file
            **kwargs: Additional arguments passed to the parent implementation

        Returns:
            str: Signed URL for accessing the file

        Raises:
            ClientError: If URL generation fails
        """
        try:
            normalized_name = self._normalize_name(name)
            LOGGER.debug(
                "Generating URL for S3 object",
                original_name=name,
                normalized_name=normalized_name,
                custom_domain=self._custom_domain,
                endpoint_url=self._endpoint_url,
                kwargs=kwargs,
                tenant=self.tenant_prefix,
            )

            _ = self.client

            # Generate presigned URL
            url = self._s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._bucket_name,
                    "Key": normalized_name,
                    "ResponseContentDisposition": "inline",
                },
                ExpiresIn=3600,
            )

            # If we have a custom domain, we need to preserve AWS signing parameters
            if self._custom_domain:
                try:
                    # Parse the original URL to get AWS signing parameters
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)

                    # Create new URL with custom domain but preserve AWS signing params
                    custom_url = urlunparse(
                        (
                            parsed.scheme,
                            self._custom_domain,
                            normalized_name,
                            "",
                            urlencode(query_params, doseq=True),  # Keep all AWS signing params
                            "",
                        )
                    )

                    LOGGER.debug(
                        "Generated signed URL for custom domain",
                        key=name,
                        normalized_key=normalized_name,
                        url=custom_url,
                        custom_domain=self._custom_domain,
                        has_aws_algorithm=bool(query_params.get("X-Amz-Algorithm")),
                        has_aws_credential=bool(query_params.get("X-Amz-Credential")),
                        has_aws_signature=bool(query_params.get("X-Amz-Signature")),
                        tenant=self.tenant_prefix,
                    )
                    return custom_url
                except ClientError as e:
                    LOGGER.error(
                        "Failed to generate signed URL",
                        error_code=e.response["Error"]["Code"],
                        message=e.response["Error"]["Message"],
                        key=name,
                        normalized_key=normalized_name,
                        tenant=self.tenant_prefix,
                    )
                    raise
            else:
                LOGGER.debug(
                    "Using standard S3 URL",
                    name=normalized_name,
                    url=url,
                    has_aws_algorithm="X-Amz-Algorithm" in url,
                    has_aws_credential="X-Amz-Credential" in url,
                    has_aws_signature="X-Amz-Signature" in url,
                    tenant=self.tenant_prefix,
                )
                return url

        except ClientError as e:
            LOGGER.error(
                "S3 URL generation failed",
                error_code=e.response["Error"]["Code"],
                message=e.response["Error"]["Message"],
                key=name,
                tenant=self.tenant_prefix,
            )
            raise
        except Exception as e:
            LOGGER.error(
                "Unexpected error generating URL",
                name=name,
                error=str(e),
                tenant=self.tenant_prefix,
            )
            raise
