"""Storage backend implementations for authentik."""

from authentik.root.storages.base import TenantAwareStorage, DirectoryStructureMixin
from authentik.root.storages.constants import (
    STORAGE_DIR_APPLICATION_ICONS,
    STORAGE_DIR_SOURCE_ICONS,
    STORAGE_DIR_FLOW_BACKGROUNDS,
    STORAGE_DIR_PUBLIC,
    STORAGE_DIRS,
    ALLOWED_IMAGE_EXTENSIONS,
    S3_CONFIG_KEYS,
)
from authentik.root.storages.exceptions import (
    FileValidationError,
    S3StorageError,
    S3BucketError,
    S3AccessError,
    S3UploadError,
    S3StorageNotConfiguredError,
)
from authentik.root.storages.filesystem import FileStorage
from authentik.root.storages.s3_base import S3Storage
from authentik.root.storages.validation import validate_image_file, optimize_image
from authentik.root.storages.connection import connection

__all__ = [
    # Base classes and mixins
    "TenantAwareStorage",
    "DirectoryStructureMixin",
    # Storage implementations
    "FileStorage",
    "S3Storage",
    # Constants
    "STORAGE_DIR_APPLICATION_ICONS",
    "STORAGE_DIR_SOURCE_ICONS",
    "STORAGE_DIR_FLOW_BACKGROUNDS",
    "STORAGE_DIR_PUBLIC",
    "STORAGE_DIRS",
    "ALLOWED_IMAGE_EXTENSIONS",
    "S3_CONFIG_KEYS",
    # Exceptions
    "FileValidationError",
    "S3StorageError",
    "S3BucketError",
    "S3AccessError",
    "S3UploadError",
    "S3StorageNotConfiguredError",
    # Validation functions
    "validate_image_file",
    "optimize_image",
    # Connection
    "connection",
] 