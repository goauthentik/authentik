"""Utility functions and helper methods for S3 storage."""

from pathlib import Path
from urllib.parse import urlencode, urlunparse

from botocore.exceptions import ClientError
from django.core.exceptions import SuspiciousOperation
from storages.utils import safe_join
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.root.storages.constants import (
    STORAGE_DIR_APPLICATION_ICONS,
    STORAGE_DIR_SOURCE_ICONS,
    STORAGE_DIR_FLOW_BACKGROUNDS,
    STORAGE_DIR_PUBLIC,
    STORAGE_DIRS,
    ALLOWED_IMAGE_EXTENSIONS,
)
from authentik.root.storages.exceptions import S3StorageError, S3BucketError, S3AccessError

LOGGER = get_logger()


class S3UtilsMixin:
    """Mixin providing utility functions for S3 storage."""

    def _ensure_directory_structure(self):
        """Ensure required directory structure exists in the S3 bucket.
        
        Creates empty marker files in each required directory to ensure the structure exists.
        This is needed because S3 doesn't have real directories, and we need to ensure
        the paths exist for future operations.
        """
        try:
            LOGGER.debug("Ensuring S3 directory structure exists", tenant=self.tenant_prefix)
            
            # Create a marker file for each required directory
            for directory in STORAGE_DIRS:
                # Create a path with tenant prefix
                marker_path = f"{self.tenant_prefix}/{directory}/.keep"
                
                try:
                    # Check if marker already exists
                    try:
                        self._s3_client.head_object(Bucket=self._bucket_name, Key=marker_path)
                        LOGGER.debug("Directory marker exists", directory=directory, tenant=self.tenant_prefix)
                        continue
                    except ClientError as e:
                        if e.response["Error"]["Code"] != "404":
                            raise
                    
                    # Create empty marker file
                    self._s3_client.put_object(
                        Bucket=self._bucket_name,
                        Key=marker_path,
                        Body=b"",
                        ContentType="text/plain",
                    )
                    LOGGER.debug("Created directory marker", directory=directory, tenant=self.tenant_prefix)
                    
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    LOGGER.error(
                        "Failed to create directory marker",
                        directory=directory,
                        error_code=error_code,
                        error=str(e),
                        tenant=self.tenant_prefix,
                    )
                    if error_code in ("AccessDenied", "AllAccessDisabled"):
                        raise S3AccessError(f"No permission to create directory structure in bucket '{self._bucket_name}'") from e
                    else:
                        raise S3BucketError(f"Failed to create directory structure: {error_code}") from e
                    
            LOGGER.debug("S3 directory structure verified", tenant=self.tenant_prefix)
            
        except S3StorageError:
            raise
        except Exception as e:
            LOGGER.error("Unexpected error creating directory structure", error=str(e), tenant=self.tenant_prefix)
            raise S3BucketError(f"Failed to create directory structure: {str(e)}") from e

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

    def _get_file_subdirectory(self, filename: str) -> str:
        """Get the appropriate subdirectory for a file based on its name.

        Args:
            filename (str): Name of the file

        Returns:
            str: Subdirectory path where the file should be stored
        """
        filename = filename.lower()
        if "app-icon" in filename or "application-icon" in filename:
            return STORAGE_DIR_APPLICATION_ICONS
        if "source-icon" in filename or "source-logo" in filename:
            return STORAGE_DIR_SOURCE_ICONS
        if "flow-bg" in filename or "flow-background" in filename:
            return STORAGE_DIR_FLOW_BACKGROUNDS
        return STORAGE_DIR_PUBLIC

    def _get_tenant_path(self, name: str) -> str:
        """Get tenant-specific path for storage.

        Args:
            name (str): Original file path/name.

        Returns:
            str: Path prefixed with tenant identifier for proper isolation.
        """
        return f"{self.tenant_prefix}/{name}"

    def _get_bucket_path(self, name: str) -> str:
        """Get the full bucket path for a file.

        Args:
            name (str): Name of the file

        Returns:
            str: Full path in the bucket including tenant prefix
        """
        if not name.startswith(f"{self.tenant_prefix}/"):
            return self._get_tenant_path(name)
        return name

    def _get_object_key(self, name: str) -> str:
        """Get the S3 object key for a file.

        Args:
            name (str): Name of the file

        Returns:
            str: S3 object key
        """
        return self._normalize_name(self._get_bucket_path(name))

    def _get_content_type(self, name: str) -> str | None:
        """Get the content type for a file based on its extension.

        Args:
            name (str): Name of the file

        Returns:
            str | None: Content type if known, None otherwise
        """
        ext = Path(name).suffix.lower()
        return ALLOWED_IMAGE_EXTENSIONS.get(ext)

    def _get_upload_args(self, content) -> dict:
        """Get upload arguments for S3 upload.

        Args:
            content: File content to upload

        Returns:
            dict: Upload arguments for S3
        """
        upload_args = {}
        if hasattr(content, "content_type") and content.content_type:
            upload_args["ContentType"] = content.content_type
        return upload_args

    def _get_download_args(self, name: str) -> dict:
        """Get download arguments for S3 download.

        Args:
            name (str): Name of the file

        Returns:
            dict: Download arguments for S3
        """
        return {
            "ResponseContentDisposition": "inline",
            "ResponseContentType": self._get_content_type(name),
        }

    def _get_presigned_url_args(self, name: str) -> dict:
        """Get arguments for generating a presigned URL.

        Args:
            name (str): Name of the file

        Returns:
            dict: Arguments for presigned URL generation
        """
        return {
            "Bucket": self._bucket_name,
            "Key": self._get_object_key(name),
            **self._get_download_args(name),
        }

    def _get_custom_domain_url(self, name: str, query_params: dict) -> str:
        """Get URL with custom domain.

        Args:
            name (str): Name of the file
            query_params (dict): Query parameters for the URL

        Returns:
            str: URL with custom domain
        """
        normalized_name = self._get_object_key(name)
        return urlunparse(
            (
                "https" if CONFIG.get_bool("storage.media.s3.secure_urls", True) else "http",
                self._custom_domain,
                "/" + normalized_name,
                "",
                urlencode(query_params, doseq=True),
                "",
            )
        ) 