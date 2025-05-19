"""Filesystem storage backend implementation."""

import os
import uuid
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from storages.utils import safe_join
from structlog.stdlib import get_logger

from authentik.root.storages.base import TenantAwareStorage, DirectoryStructureMixin
from authentik.root.storages.constants import (
    STORAGE_DIRS,
    STORAGE_DIR_APPLICATION_ICONS,
    STORAGE_DIR_SOURCE_ICONS,
    STORAGE_DIR_FLOW_BACKGROUNDS,
    STORAGE_DIR_PUBLIC,
)
from authentik.root.storages.exceptions import FileValidationError
from authentik.root.storages.validation import validate_image_file, optimize_image
from authentik.root.storages.connection import connection

LOGGER = get_logger()


class FileStorage(TenantAwareStorage, DirectoryStructureMixin, FileSystemStorage):
    """Multi-tenant filesystem storage backend."""

    STORAGE_DIRS = [
        STORAGE_DIR_APPLICATION_ICONS,
        STORAGE_DIR_SOURCE_ICONS,
        STORAGE_DIR_FLOW_BACKGROUNDS,
        STORAGE_DIR_PUBLIC,
    ]

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
        # Initialize _base_path from kwargs or settings
        self._base_path = Path(kwargs.get("location", settings.MEDIA_ROOT))
        try:
            # Ensure the base directory exists with correct permissions
            os.makedirs(self._base_path, exist_ok=True)

            # Also create tenant-specific directory
            tenant_dir = self._base_path / self.tenant_prefix
            os.makedirs(tenant_dir, exist_ok=True)

            # Create standard subdirectories
            self._ensure_directory_structure()

            LOGGER.debug(
                "Storage directories initialized",
                base_path=str(self._base_path),
                tenant_dir=str(tenant_dir),
                pid=os.getpid(),
                schema_name=connection.schema_name,
                domain_url=None,
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

    def _ensure_directory_structure(self):
        """Ensure required directory structure exists in the filesystem.
        
        Creates all required directories for the current tenant with proper permissions.
        """
        try:
            LOGGER.debug("Ensuring filesystem directory structure exists", tenant=self.tenant_prefix)
            
            # Create each required directory
            for directory in self.STORAGE_DIRS:
                dir_path = os.path.join(self._base_path, self.tenant_prefix, directory)
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    # Create a .keep file to ensure the directory is tracked by git
                    keep_file = os.path.join(dir_path, ".keep")
                    if not os.path.exists(keep_file):
                        with open(keep_file, 'w') as f:
                            pass
                    LOGGER.debug("Created directory", directory=directory, path=str(dir_path), tenant=self.tenant_prefix)
                except OSError as e:
                    LOGGER.error(
                        "Failed to create directory",
                        directory=directory,
                        path=str(dir_path),
                        error=str(e),
                        tenant=self.tenant_prefix,
                    )
                    raise PermissionError(f"Cannot create directory '{dir_path}': {str(e)}") from e
                    
            LOGGER.debug("Filesystem directory structure verified", tenant=self.tenant_prefix)
            
        except Exception as e:
            LOGGER.error("Unexpected error creating directory structure", error=str(e), tenant=self.tenant_prefix)
            raise OSError(f"Failed to create directory structure: {str(e)}") from e

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
        return Path(self._base_path) / self.tenant_prefix

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
        if ".." in name or name.startswith("/") or "\\" in name:
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
        if not name.startswith(f"{self.tenant_prefix}/"):
            tenant_path = self.get_tenant_path(name)
        else:
            tenant_path = name

        # Normalize the path to prevent path traversal
        clean_name = self._validate_path(tenant_path)

        # Join the base location with the validated name
        return os.path.join(self.location, clean_name.replace(f"{self.tenant_prefix}/", "", 1))

    def _get_file_subdirectory(self, name: str, content_type: str | None = None) -> str:
        """Determine the appropriate subdirectory for a file based on its name and content type.

        Args:
            name (str): Original filename
            content_type (str | None): Content type of the file if available

        Returns:
            str: Subdirectory path where the file should be stored
        """
        name_lower = name.lower()

        # Application icons
        if any(x in name_lower for x in ["app-icon", "application-icon"]):
            return STORAGE_DIR_APPLICATION_ICONS

        # Source icons
        if any(x in name_lower for x in ["source-icon", "source-logo"]):
            return STORAGE_DIR_SOURCE_ICONS

        # Flow backgrounds
        if any(x in name_lower for x in ["flow-bg", "flow-background"]):
            return STORAGE_DIR_FLOW_BACKGROUNDS

        # Default to public for other files
        return STORAGE_DIR_PUBLIC

    def _save(self, name: str, content) -> str:
        """Save the file with content validation and tenant prefix application.

        Args:
            name (str): Name of the file
            content: File content to save

        Returns:
            str: Name of the saved file with tenant prefix

        Raises:
            FileValidationError: If file validation fails (for images)
            SuspiciousOperation: If the path contains invalid characters or traversal attempts
        """
        # Validate path first
        name = self._validate_path(name)

        # Validate content type
        if hasattr(content, "content_type"):
            if not content.content_type.startswith("image/"):
                raise FileValidationError(f"Invalid content type: {content.content_type}. Only image files are allowed.")
            try:
                validate_image_file(content)
                # Optimize image after validation
                content = optimize_image(content)
            except FileValidationError as e:
                LOGGER.warning("Image validation failed", name=name, error=str(e))
                raise

        # For application icons, always validate
        if name.startswith(STORAGE_DIR_APPLICATION_ICONS):
            try:
                validate_image_file(content)
            except FileValidationError as e:
                LOGGER.warning("Application icon validation failed", name=name, error=str(e))
                raise

        # Preserve the original directory structure
        original_dir = os.path.dirname(name)
        base_name, ext = os.path.splitext(os.path.basename(name))
        unique_id = str(uuid.uuid4())
        randomized_name = f"{unique_id}{ext}"

        # Get appropriate subdirectory
        subdirectory = self._get_file_subdirectory(name, getattr(content, "content_type", None))

        # Create symlink directory structure
        if original_dir:
            symlink_dir = os.path.join(self.path(self.get_tenant_path(original_dir)))
            os.makedirs(symlink_dir, exist_ok=True)

        # Combine with tenant prefix
        tenant_path = f"{self.tenant_prefix}/{subdirectory}/{randomized_name}"

        # Perform regular file save
        file_path = self.path(tenant_path)

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

        LOGGER.debug("Saving file", name=name, path=file_path)

        # Save the file in the storage location
        with open(file_path, 'wb') as f:
            for chunk in content.chunks():
                f.write(chunk)

        # Create a symlink from the original path to the stored file
        if original_dir:
            symlink_path = os.path.join(symlink_dir, os.path.basename(name))
            if os.path.lexists(symlink_path):
                os.unlink(symlink_path)
            os.symlink(os.path.abspath(file_path), symlink_path)

        return tenant_path

    def url(self, name: str) -> str:
        """Get the URL for a file.

        Args:
            name (str): Name of the file

        Returns:
            str: URL for the file
        """
        if not name:
            return ""
        
        # Always start with /media/
        media_prefix = "/media/"
            
        # Get the tenant-specific path if needed
        if not name.startswith(f"{self.tenant_prefix}/"):
            tenant_path = self.get_tenant_path(name)
        else:
            tenant_path = name
            
        # Build the URL with the media URL prefix
        return f"{media_prefix}{tenant_path}"

    def size(self, name: str) -> int:
        """Get the size of a file in bytes.
        
        Args:
            name (str): Name of the file to get the size of
            
        Returns:
            int: Size of the file in bytes
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        if not self.exists(name):
            raise FileNotFoundError(f"File {name} does not exist")
            
        # Open the file for reading to get the correct size
        with self.open(name, 'rb') as f:
            # Go to the end of the file to determine size
            f.seek(0, 2)  # SEEK_END
            size = f.tell()
            return size 

    def _open(self, name, mode="rb"):
        """Open a file from storage.
        
        Args:
            name (str): Name of the file to open
            mode (str): Mode to open the file in (usually 'rb')
            
        Returns:
            File: A File object open in the specified mode
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        full_path = self.path(name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File {full_path} does not exist")
            
        return File(open(full_path, mode)) 

    def listdir(self, path: str) -> tuple[list[str], list[str]]:
        """List contents of a directory.
        
        Args:
            path (str): Directory path relative to tenant base
            
        Returns:
            tuple: A tuple containing (directories, files)
        """
        full_path = self.path(path) if path else os.path.join(self.location)
        
        directories, files = [], []
        with os.scandir(full_path) as entries:
            for entry in entries:
                if entry.is_dir():
                    directories.append(entry.name)
                else:
                    if entry.name != '.keep':  # Exclude .keep files
                        files.append(entry.name)
                        
        return directories, files 