"""Storage backends for authentik with multi-tenant support.

This module provides custom storage backends for handling file storage in a multi-tenant
environment. It supports both filesystem and S3 storage options with proper tenant isolation.
"""

import os
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, NoRegionError
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


def validate_image_file(file: UploadedFile) -> bool:
    """Validate that an uploaded file is a supported and valid image format.

    This function performs multiple validation checks:
    1. Verifies the file extension and MIME type against allowed formats
    2. Performs format-specific validation:
        - SVG: Validates basic XML/SVG structure
        - ICO: Checks file header magic number
        - Other formats: Uses Pillow to verify image integrity

    Args:
        file: The uploaded file to validate. Must be an instance of UploadedFile.

    Returns:
        bool: True if the file is a valid image of an allowed format, False otherwise.

    Raises:
        No exceptions are raised; all errors are caught and logged.
    """
    if not file:
        return False

    _, ext = os.path.splitext(file.name.lower())

    if (
        ext not in ALLOWED_IMAGE_EXTENSIONS
        or file.content_type not in ALLOWED_IMAGE_EXTENSIONS.values()
    ):
        LOGGER.warning(
            "File extension or mimetype not allowed",
            extension=ext,
            mimetype=file.content_type,
            allowed_extensions=list(ALLOWED_IMAGE_EXTENSIONS.keys()),
            allowed_mimetypes=list(ALLOWED_IMAGE_EXTENSIONS.values()),
        )
        return False

    try:
        is_valid = False

        if ext == ".svg":
            # Read first 8KB for SVG validation - sufficient for header and root element
            content = file.read(8192).decode("utf-8").strip().lower()
            file.seek(0)

            # Validate basic SVG structure (XML declaration or SVG root element)
            has_valid_start = content.startswith("<?xml") or content.startswith("<svg")
            is_valid = has_valid_start and "<svg" in content

        elif ext == ".ico":
            # Validate ICO file by checking the magic number in header
            magic = file.read(4)
            file.seek(0)
            is_valid = magic == b"\x00\x00\x01\x00"

        else:
            try:
                # Validate other image formats using Pillow
                with Image.open(file) as img:
                    format_to_ext = {
                        "JPEG": ".jpg",
                        "PNG": ".png",
                        "GIF": ".gif",
                        "WEBP": ".webp",
                    }
                    detected_ext = format_to_ext.get(img.format)

                    if not detected_ext:
                        LOGGER.warning(
                            "Unrecognized image format", format=img.format, extension=ext
                        )
                    else:
                        # Special handling for JPEG extension variants
                        is_jpeg = detected_ext == ".jpg" and ext == ".jpeg"
                        is_valid = detected_ext == ext or is_jpeg
                        if not is_valid:
                            LOGGER.warning(
                                "File extension doesn't match content",
                                detected_format=img.format,
                                extension=ext,
                            )
                        else:
                            # Verify image data integrity
                            img.verify()
                            is_valid = True

                    file.seek(0)

            except Exception as img_error:
                LOGGER.warning("Invalid image file", error=str(img_error))
                is_valid = False

        return is_valid

    except UnicodeDecodeError as e:
        LOGGER.warning("Invalid SVG file: not valid UTF-8", error=str(e))
        return False
    except Exception as e:
        LOGGER.warning("Error validating image file", error=str(e))
        return False


class TenantAwareStorage:
    """Mixin providing tenant-aware path functionality for storage backends."""

    @property
    def tenant_prefix(self) -> str:
        """Get current tenant schema prefix.

        Returns:
            str: The current tenant's schema name from the database connection.
        """
        return connection.schema_name

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
            self._base_path.mkdir(parents=True, exist_ok=True)
            LOGGER.debug("Created storage directory", path=str(self._base_path))
        except PermissionError as e:
            LOGGER.critical(
                "Permission denied creating storage directory",
                path=str(self._base_path),
                error=str(e),
            )
            raise
        except OSError as e:
            LOGGER.error(
                "Filesystem error creating storage directory",
                path=str(self._base_path),
                error=str(e),
            )
            raise

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

    def path(self, name: str) -> str:
        """Return full filesystem path to the file with security validation.

        Performs path validation to prevent directory traversal and other path-based attacks.

        Args:
            name (str): Name of the file

        Returns:
            str: Full filesystem path to the file

        Raises:
            SuspiciousOperation: If the path appears to be malicious
        """
        try:
            name = self.get_valid_name(name)
            name = os.path.normpath(name).lstrip("./")
            if name.startswith("..") or name.startswith("/"):
                raise ValueError("Suspicious path")
            full_path = safe_join(self.location, name)
            LOGGER.debug("Resolved file path", name=name, path=full_path)
            return full_path
        except ValueError as e:
            LOGGER.error(
                "Invalid file path requested", name=name, location=self.location, error=str(e)
            )
            raise SuspiciousOperation(f"Invalid path: {name}") from e

    def _save(self, name: str, content) -> str:
        """Save file.

        Performs image validation and path sanitization before saving the file.

        Args:
            name (str): Name of the file
            content: File content to save

        Returns:
            str: Name of the saved file

        Raises:
            SuspiciousOperation: If file validation fails or path is suspicious
        """
        if not validate_image_file(content):
            raise SuspiciousOperation("Invalid or unsupported image format")

        name = self.get_valid_name(name)
        name = os.path.normpath(name).lstrip("./")
        if name.startswith("..") or name.startswith("/"):
            raise SuspiciousOperation(f"Invalid path: {name}")
        return super()._save(name, content)


class S3Storage(TenantAwareStorage, BaseS3Storage):
    """Multi-tenant S3 (compatible/Amazon) storage backend."""

    CONFIG_KEYS = {
        "session_profile": "storage.media.s3.session_profile",
        "access_key": "storage.media.s3.access_key",
        "secret_key": "storage.media.s3.secret_key",
        "security_token": "storage.media.s3.security_token",
        "bucket_name": "storage.media.s3.bucket_name",
        "region_name": "storage.media.s3.region_name",
    }

    def __init__(self, **kwargs):
        """Initialize the S3 storage backend with proper configuration validation.

        Validates AWS credentials and configuration before initializing the storage backend.
        Sets up caching for S3 client and bucket instances.

        Args:
            **kwargs: Configuration options passed to parent S3Storage

        Raises:
            ImproperlyConfigured: If AWS credentials or configuration is invalid
        """
        self._validate_configuration()
        super().__init__(**kwargs)
        self._client = None
        self._bucket = None
        self._file_mapping = {}

    def _validate_configuration(self):
        """Validate AWS credentials and configuration settings.

        1. Checks for conflicting authentication methods
        2. Ensures required credentials are provided
        3. Validates bucket name configuration

        Raises:
            ImproperlyConfigured: If configuration is invalid or incomplete
        """
        if self.session_profile and (self.access_key or self.secret_key):
            LOGGER.error(
                "Conflicting S3 storage configuration",
                session_profile=self.session_profile,
                has_access_key=bool(self.access_key),
                has_secret_key=bool(self.secret_key),
            )
            raise ImproperlyConfigured(
                "AUTHENTIK_STORAGE__MEDIA__S3__SESSION_PROFILE should not be provided with "
                "AUTHENTIK_STORAGE__MEDIA__S3__ACCESS_KEY and "
                "AUTHENTIK_STORAGE__MEDIA__S3__SECRET_KEY"
            )

        if not self.session_profile and not (self.access_key and self.secret_key):
            LOGGER.error(
                "Incomplete S3 configuration",
                has_session_profile=bool(self.session_profile),
                has_access_key=bool(self.access_key),
                has_secret_key=bool(self.secret_key),
            )
            raise ImproperlyConfigured(
                "Either AWS session profile or access key/secret pair must be configured"
            )

        bucket_name = self._get_config_value("bucket_name")
        if not bucket_name:
            LOGGER.error("S3 bucket name not configured")
            raise ImproperlyConfigured(
                "AUTHENTIK_STORAGE__MEDIA__S3__BUCKET_NAME must be configured"
            )

        region_name = self._get_config_value("region_name")
        if not region_name:
            LOGGER.warning(
                "S3 region not configured, using default region", default_region="us-east-1"
            )

    def _get_config_value(self, key: str) -> str | None:
        """Get refreshed configuration value from environment.

        Args:
            key (str): Configuration key from CONFIG_KEYS

        Returns:
            str | None: Configuration value if set, None otherwise
        """
        return CONFIG.refresh(self.CONFIG_KEYS[key], None)

    @property
    def session_profile(self) -> str | None:
        """Get AWS session profile name.

        Returns:
            str | None: Configured AWS session profile name
        """
        return self._get_config_value("session_profile")

    @property
    def access_key(self) -> str | None:
        """Get AWS access key ID.

        Returns:
            str | None: Configured AWS access key ID
        """
        return self._get_config_value("access_key")

    @property
    def secret_key(self) -> str | None:
        """Get AWS secret access key.

        Returns:
            str | None: Configured AWS secret access key
        """
        return self._get_config_value("secret_key")

    @property
    def security_token(self) -> str | None:
        """Get AWS temporary security token.

        Returns:
            str | None: Configured AWS security token
        """
        return self._get_config_value("security_token")

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
        if not self._client:
            try:
                session = boto3.Session(
                    profile_name=self.session_profile,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    aws_session_token=self.security_token,
                )
                self._client = session.client("s3")
                LOGGER.debug(
                    "Created S3 client",
                    session_profile=self.session_profile,
                    region=self.region_name,
                )
            except (NoCredentialsError, NoRegionError) as e:
                LOGGER.critical(
                    "AWS credentials/region configuration error",
                    error=str(e),
                    tenant=self.tenant_prefix,
                )
                raise ImproperlyConfigured(f"AWS configuration error: {e}") from e
            except ClientError as e:
                LOGGER.error(
                    "AWS client initialization failed",
                    error_code=e.response["Error"]["Code"],
                    message=e.response["Error"]["Message"],
                    tenant=self.tenant_prefix,
                )
                raise
            except Exception as e:
                LOGGER.error(
                    "Unexpected error creating S3 client",
                    error=str(e),
                    tenant=self.tenant_prefix,
                )
                raise
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
            try:
                try:
                    self.client.list_buckets()
                except (ClientError, NoCredentialsError) as e:
                    LOGGER.critical(
                        "Invalid AWS credentials",
                        error=str(e),
                        tenant=self.tenant_prefix,
                    )
                    raise ImproperlyConfigured("Invalid AWS credentials") from e

                bucket_name = self._get_config_value("bucket_name")

                try:
                    self.client.head_bucket(Bucket=bucket_name)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    if error_code == "404":
                        LOGGER.error(
                            "S3 bucket does not exist",
                            bucket=bucket_name,
                            tenant=self.tenant_prefix,
                        )
                        raise ImproperlyConfigured(
                            f"S3 bucket '{bucket_name}' does not exist"
                        ) from e
                    elif error_code in ("403", "401"):
                        LOGGER.error(
                            "Permission denied accessing S3 bucket",
                            bucket=bucket_name,
                            error=str(e),
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
                            error=str(e),
                            tenant=self.tenant_prefix,
                        )
                        raise ImproperlyConfigured(
                            f"Error accessing S3 bucket '{bucket_name}': {str(e)}"
                        ) from e

                self._bucket = self.client.Bucket(bucket_name)
                LOGGER.info(
                    "Successfully connected to S3 bucket",
                    bucket=bucket_name,
                    region=self.region_name,
                    tenant=self.tenant_prefix,
                )

            except Exception as e:
                LOGGER.error(
                    "Unexpected error accessing S3",
                    error=str(e),
                    tenant=self.tenant_prefix,
                )
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
        name = os.path.basename(name)
        return super().get_valid_name(name)

    def _normalize_name(self, name: str) -> str:
        """Normalize file path for S3 storage with security validation.

        Normalizes the file path and performs security checks to prevent
        path traversal attacks.

        Args:
            name (str): Original file path/name

        Returns:
            str: Normalized and tenant-prefixed path

        Raises:
            SuspiciousOperation: If the path appears to be malicious
        """
        if ".." in name or name.startswith("/"):
            raise SuspiciousOperation(f"Suspicious path: {name}")
        normalized = self.get_tenant_path(name)
        LOGGER.debug(
            "Normalized S3 key",
            original=name,
            normalized=normalized,
        )
        return normalized

    def _randomize_filename(self, filename: str) -> str:
        """Generate a randomized filename while preserving extension.

        Creates a unique filename using tenant hash and UUID while
        maintaining the original file extension.

        Args:
            filename (str): Original filename

        Returns:
            str: Randomized filename with original extension
        """
        name, ext = os.path.splitext(filename)
        tenant_hash = str(uuid.uuid5(uuid.NAMESPACE_DNS, self.tenant_prefix))[:8]
        random_uuid = str(uuid.uuid4())
        randomized = f"{tenant_hash}_{random_uuid}{ext.lower()}"
        LOGGER.debug(
            "Randomized filename",
            original=filename,
            randomized=randomized,
            tenant=self.tenant_prefix,
        )
        return randomized

    def _save(self, name: str, content) -> str:
        """Save file to S3 with security validation and tenant isolation.

        Performs image validation, generates a random filename, and uploads
        the file to the appropriate tenant-specific S3 location.

        Args:
            name (str): Original filename
            content: File content to save

        Returns:
            str: Normalized S3 key of the saved file

        Raises:
            SuspiciousOperation: If file validation fails
            ClientError: If S3 upload fails
        """
        if not validate_image_file(content):
            raise SuspiciousOperation("Invalid or unsupported image format")

        randomized_name = self._randomize_filename(name)
        normalized_name = self._normalize_name(randomized_name)

        LOGGER.info(
            "Saving file to S3",
            original_name=name,
            randomized_name=randomized_name,
            normalized_name=normalized_name,
            tenant=self.tenant_prefix,
        )

        try:
            # Upload file to S3
            self.bucket.Object(normalized_name).upload_fileobj(content)

            # Verify upload
            try:
                self.bucket.Object(normalized_name).load()
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", "Unknown error")
                LOGGER.error(
                    "Failed to verify S3 upload",
                    key=normalized_name,
                    error_code=error_code,
                    message=error_message,
                    tenant=self.tenant_prefix,
                )
                # Clean up failed upload
                try:
                    self.bucket.Object(normalized_name).delete()
                except Exception as cleanup_error:
                    LOGGER.error(
                        "Failed to clean up failed upload",
                        key=normalized_name,
                        error=str(cleanup_error),
                        tenant=self.tenant_prefix,
                    )
                raise

            # Store mapping of original name to normalized name
            self._file_mapping[name] = normalized_name

            LOGGER.debug(
                "File saved successfully to S3",
                key=normalized_name,
                tenant=self.tenant_prefix,
            )
            return normalized_name

        except Exception as e:
            LOGGER.error(
                "Unexpected error saving file to S3",
                name=name,
                error=str(e),
                tenant=self.tenant_prefix,
            )
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
            self.bucket.Object(normalized_name).delete()
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
        """Generate URL for accessing the file, with optional custom domain support.

        Generates a URL for the file, optionally cleaning AWS signing parameters
        when using a custom domain.

        Args:
            name (str): Name of the file
            **kwargs: Additional arguments passed to the parent implementation

        Returns:
            str: URL for accessing the file

        Raises:
            ClientError: If URL generation fails
        """
        try:
            url = super().url(name, **kwargs)

            if not self.custom_domain:
                return url

            parsed = urlsplit(url)
            query_params = parse_qsl(parsed.query, keep_blank_values=True)

            signing_params = {
                "x-amz-algorithm",
                "x-amz-credential",
                "x-amz-date",
                "x-amz-expires",
                "x-amz-signedheaders",
                "x-amz-signature",
                "x-amz-security-token",
                "awsaccesskeyid",
                "expires",
                "signature",
            }

            clean_params = [(k, v) for k, v in query_params if k.lower() not in signing_params]

            return parsed._replace(query=urlencode(clean_params, doseq=True)).geturl()
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
