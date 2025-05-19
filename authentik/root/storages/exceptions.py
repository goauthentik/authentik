"""Custom exceptions for storage backends."""

from django.core.exceptions import SuspiciousOperation


class FileValidationError(SuspiciousOperation):
    """Custom exception for file validation errors with status code and user message."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.user_message = message


class S3StorageError(Exception):
    """Base exception class for S3 storage errors."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class S3BucketError(S3StorageError):
    """Exception raised for bucket-related errors."""
    pass


class S3AccessError(S3StorageError):
    """Exception raised for access-related errors."""
    pass


class S3UploadError(S3StorageError):
    """Exception raised for upload-related errors."""
    pass


class S3StorageNotConfiguredError(S3StorageError):
    """Exception raised when S3 storage is not properly configured."""
    pass 