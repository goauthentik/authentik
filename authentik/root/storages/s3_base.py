"""Core S3 storage backend implementation."""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, NoRegionError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from storages.backends.s3 import S3Storage as BaseS3Storage
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.root.storages.base import TenantAwareStorage, DirectoryStructureMixin
from authentik.root.storages.constants import S3_CONFIG_KEYS
from authentik.root.storages.exceptions import (
    S3StorageError,
    S3BucketError,
    S3AccessError,
    S3StorageNotConfiguredError,
    S3UploadError,
    FileValidationError,
)
from authentik.root.storages.s3_operations import S3OperationsMixin
from authentik.root.storages.s3_utils import S3UtilsMixin
from authentik.root.storages.validation import validate_image_file

LOGGER = get_logger()


class S3Storage(TenantAwareStorage, DirectoryStructureMixin, S3OperationsMixin, S3UtilsMixin, BaseS3Storage):
    """Multi-tenant S3 (compatible/Amazon) storage backend."""

    CONFIG_KEYS = S3_CONFIG_KEYS

    def __init__(self, **kwargs):
        """Initialize S3Storage with configuration.

        Args:
            **kwargs: Configuration options passed to parent S3Storage

        Raises:
            S3StorageNotConfiguredError: If storage is not properly configured
            S3BucketError: If bucket doesn't exist or cannot be accessed
            S3AccessError: If credentials are invalid or access is denied
        """
        try:
            # Initialize client/bucket references
            self._client = None
            self._s3_client = None
            self._bucket = None

            # Pre-fetch configuration values
            self._session_profile = kwargs.get("session_profile") or self._get_config_value("session_profile")
            self._access_key = kwargs.get("access_key") or self._get_config_value("access_key")
            self._secret_key = kwargs.get("secret_key") or self._get_config_value("secret_key")
            self._security_token = kwargs.get("security_token") or self._get_config_value("security_token")
            self._bucket_name = kwargs.get("bucket_name") or self._get_config_value("bucket_name")
            self._region_name = kwargs.get("region_name") or self._get_config_value("region_name")
            self._endpoint_url = kwargs.get("endpoint_url") or self._get_config_value("endpoint_url")
            self._custom_domain = kwargs.get("custom_domain") or self._get_config_value("custom_domain")

            # Debug logging
            LOGGER.debug(
                "S3Storage initialization",
                has_session_profile=bool(self._session_profile),
                has_access_key=bool(self._access_key),
                has_secret_key=bool(self._secret_key),
                has_security_token=bool(self._security_token),
                bucket_name=self._bucket_name,
                region_name=self._region_name,
                endpoint_url=self._endpoint_url,
                custom_domain=self._custom_domain,
                tenant=getattr(self, "tenant_prefix", "unknown"),
            )

            # Validate configuration before proceeding
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

            # Initialize parent class with cleaned settings
            try:
                super().__init__(**settings)
                LOGGER.debug("S3Storage parent initialization successful")
            except Exception as e:
                LOGGER.error("S3Storage parent initialization failed", error=str(e))
                raise S3StorageNotConfiguredError(f"Failed to initialize S3 storage: {str(e)}") from e

            self._file_mapping = {}

            # Apply transfer config if specified
            transfer_config = CONFIG.refresh("storage.media.s3.transfer_config", None)
            if transfer_config:
                settings["transfer_config"] = Config(s3=transfer_config)
                super().__init__(**settings)

        except (S3StorageError, S3AccessError, S3BucketError):
            # Re-raise our custom exceptions without wrapping them
            raise
        except Exception as e:
            # Catch any other unexpected errors
            LOGGER.error("Unexpected error during S3 storage initialization", error=str(e))
            raise S3StorageNotConfiguredError(f"Failed to initialize S3 storage: {str(e)}") from e

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
            S3BucketError: If bucket doesn't exist or cannot be accessed
            S3AccessError: If credentials are invalid or access is denied
            S3StorageNotConfiguredError: If storage is not properly configured
        """
        # Check that bucket_name and region_name are set
        if not self._bucket_name:
            LOGGER.error("Missing required S3 configuration: bucket_name")
            raise S3StorageNotConfiguredError("Missing required S3 configuration: bucket_name")

        if not self._region_name:
            LOGGER.info("No region_name specified, defaulting to us-east-1")
            self._region_name = "us-east-1"

        has_profile = bool(self._session_profile)
        has_credentials = bool(self._access_key) and bool(self._secret_key)

        # Check that session profile is not provided with access key and secret key
        if has_profile and has_credentials:
            raise S3StorageNotConfiguredError(
                "AWS session profile should not be provided with access key and secret key"
            )

        if not (has_profile or has_credentials):
            LOGGER.error(
                "Missing required S3 authentication configuration. "
                "Either session_profile or (access_key and secret_key) must be set."
            )
            raise S3StorageNotConfiguredError(
                "Missing required S3 authentication configuration. "
                "Either session_profile or (access_key and secret_key) must be set."
            )

        # Validate bucket exists and is accessible by attempting to list objects
        try:
            _ = self.client  # Ensure client is initialized
            # Try to list objects in the bucket with max_keys=1 to minimize data transfer
            try:
                self._s3_client.list_objects_v2(Bucket=self._bucket_name, MaxKeys=1)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                if error_code == "NoSuchBucket":
                    LOGGER.error("S3 bucket does not exist", bucket=self._bucket_name)
                    raise S3BucketError(f"S3 bucket '{self._bucket_name}' does not exist") from e
                elif error_code == "NoSuchKey":
                    # NoSuchKey is not a critical error - it just means the bucket is empty
                    LOGGER.debug("Bucket is empty", bucket=self._bucket_name)
                elif error_code in ("AccessDenied", "AllAccessDisabled"):
                    LOGGER.error("No permission to access S3 bucket", bucket=self._bucket_name)
                    raise S3AccessError(f"No permission to access S3 bucket '{self._bucket_name}'") from e
                elif error_code == "InvalidAccessKeyId":
                    LOGGER.error("Invalid AWS credentials", bucket=self._bucket_name)
                    raise S3AccessError("Invalid AWS credentials") from e
                elif error_code == "BucketRegionError":
                    LOGGER.error("Bucket region mismatch", bucket=self._bucket_name)
                    raise S3BucketError("Bucket region mismatch") from e
                else:
                    LOGGER.error(
                        "Error accessing S3 bucket",
                        bucket=self._bucket_name,
                        error=str(e),
                        code=error_code,
                    )
                    raise S3BucketError(f"Error accessing S3 bucket: {error_code}") from e

        except (NoCredentialsError, NoRegionError) as e:
            LOGGER.error("AWS credentials/region configuration error", error=str(e))
            raise S3StorageNotConfiguredError(f"AWS configuration error: {str(e)}") from e
        except (S3BucketError, S3AccessError):
            # Re-raise these specific exceptions without wrapping them
            raise
        except Exception as e:
            LOGGER.error("Unexpected error during S3 configuration validation", error=str(e))
            raise S3StorageNotConfiguredError(f"Unexpected error during S3 configuration: {str(e)}") from e

        LOGGER.debug("S3 configuration validated successfully", bucket=self._bucket_name)

    @property
    def client(self):
        """Get or create S3 client.

        Returns:
            boto3.client: S3 client instance

        Raises:
            S3StorageNotConfiguredError: If client cannot be created
            S3AccessError: If credentials are invalid or access is denied
        """
        if self._s3_client is None:
            try:
                kwargs = {
                    "region_name": self._region_name,
                }

                if self._endpoint_url:
                    kwargs["endpoint_url"] = self._endpoint_url

                if self._session_profile:
                    session = boto3.Session(profile_name=self._session_profile)
                    self._s3_client = session.client("s3", **kwargs)
                else:
                    kwargs.update({
                        "aws_access_key_id": self._access_key,
                        "aws_secret_access_key": self._secret_key,
                    })
                    if self._security_token:
                        kwargs["aws_session_token"] = self._security_token
                    self._s3_client = boto3.client("s3", **kwargs)

                # Verify client works by attempting to list objects
                try:
                    self._s3_client.list_objects_v2(Bucket=self._bucket_name, MaxKeys=1)
                    return self._s3_client
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    if error_code == "NoSuchBucket":
                        raise S3BucketError(f"S3 bucket '{self._bucket_name}' does not exist") from e
                    elif error_code in ("AccessDenied", "AllAccessDisabled"):
                        raise S3AccessError(f"No permission to access S3 bucket '{self._bucket_name}'") from e
                    else:
                        raise S3AccessError(f"Error accessing S3: {error_code}") from e

            except (NoCredentialsError, NoRegionError) as e:
                LOGGER.error("AWS credentials/region configuration error", error=str(e))
                raise S3StorageNotConfiguredError(f"AWS credentials/region configuration error: {str(e)}") from e
            except (S3BucketError, S3AccessError):
                # Re-raise these exceptions without wrapping
                raise
            except Exception as e:
                LOGGER.error("Error creating S3 client", error=str(e))
                raise S3StorageNotConfiguredError(f"Error creating S3 client: {str(e)}") from e
        
        return self._s3_client

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
                            "No permission to access S3 bucket",
                            bucket=bucket_name,
                            error_code=error_code,
                            message=error_message,
                            tenant=self.tenant_prefix,
                        )
                        raise ImproperlyConfigured(
                            f"No permission to access S3 bucket '{bucket_name}'"
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
                        raise

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
        
    @bucket.setter
    def bucket(self, value):
        """Setter for bucket property to allow mocking in tests.
        
        Args:
            value: The bucket object or mock to set
        """
        self._bucket = value
        
    @bucket.deleter
    def bucket(self):
        """Deleter for bucket property to allow cleanup in tests."""
        self._bucket = None

    @property
    def base_url(self) -> str:
        """Get base URL for S3 storage with tenant prefix.

        Returns:
            str: Base URL with tenant prefix for S3 storage
        """
        return f"/{self.tenant_prefix}/"

    def _save(self, name, content):
        """Save a file to S3 storage.

        Args:
            name (str): Name of the file to save
            content (File): File-like object to save

        Returns:
            str: Name of the saved file

        Raises:
            FileValidationError: If file validation fails
            S3UploadError: If upload fails
            SuspiciousOperation: If filename is invalid
        """
        try:
            # Validate file path
            name = self._validate_path(name)

            # Validate file content if it's an image
            if hasattr(content, "content_type") and content.content_type.startswith("image/"):
                validate_image_file(content)

            # Upload to S3
            try:
                return super()._save(name, content)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                if error_code in ("AccessDenied", "AllAccessDisabled"):
                    raise S3AccessError(f"No permission to upload to S3 bucket '{self._bucket_name}'") from e
                else:
                    raise S3UploadError(f"Failed to upload file to S3: {error_code}") from e

        except FileValidationError:
            raise
        except SuspiciousOperation:
            raise
        except Exception as e:
            if not isinstance(e, (FileValidationError, S3UploadError, SuspiciousOperation)):
                raise S3UploadError(f"Unexpected error during file upload: {str(e)}") from e
            raise 

    def _open(self, name, mode="rb"):
        """Open a file from S3 storage.

        Args:
            name: Name of the file to open
            mode: Mode to open the file in (only 'rb' is supported)

        Returns:
            File-like object

        Raises:
            FileNotFoundError: If the file doesn't exist
            S3AccessError: If access is denied
            S3StorageError: For other S3 errors
        """
        try:
            normalized_name = self._normalize_name(name)
            s3_key = self._file_mapping.get(name, normalized_name)
            
            try:
                # Call Django's S3Storage _open method
                file_obj = super()._open(s3_key, mode)
                return file_obj
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", "Unknown error")
                if error_code == "NoSuchKey":
                    raise FileNotFoundError(f"File '{name}' not found in S3: {error_message}")
                elif error_code in ("AccessDenied", "AllAccessDisabled"):
                    raise S3AccessError(f"No permission to access file '{name}' in S3: {error_message}")
                else:
                    raise S3StorageError(f"Error opening file '{name}' from S3: {error_code}: {error_message}")
        except Exception as e:
            if isinstance(e, (FileNotFoundError, S3AccessError, S3StorageError)):
                raise
            raise S3StorageError(f"Unexpected error opening file '{name}' from S3: {str(e)}")

    def _validate_path(self, name):
        """Validate file path to prevent path traversal.

        Args:
            name (str): Name of the file to validate

        Returns:
            str: Validated name

        Raises:
            SuspiciousOperation: If the path is invalid
        """
        if not name:
            raise SuspiciousOperation("Empty filename is not allowed")

        # Check for absolute path
        if name.startswith('/') or name.startswith('\\'):
            raise SuspiciousOperation(f"Invalid characters in filename '{name}'")

        # Check for directory traversal
        if '..' in name.split('/') or '..' in name.split('\\'):
            raise SuspiciousOperation(f"Invalid characters in filename '{name}'")

        return name 

    def url(self, name):
        """Get URL for file stored in S3.
        
        Args:
            name (str): Name of the file to get URL for
            
        Returns:
            str: URL to access the file
            
        Raises:
            S3StorageError: If URL generation fails
        """
        try:
            # Call parent class url method with error handling
            normalized_name = self._normalize_name(name)
            
            try:
                return super().url(normalized_name)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", "Unknown error")
                LOGGER.error(
                    "Error generating URL for S3 file",
                    name=name,
                    normalized_name=normalized_name,
                    error_code=error_code,
                    error_message=error_message,
                )
                raise S3StorageError(f"Failed to generate presigned URL: {error_message}")
                
        except Exception as e:
            if isinstance(e, S3StorageError):
                raise
            LOGGER.error("Unexpected error generating URL", name=name, error=str(e))
            raise S3StorageError(f"Failed to generate URL: {str(e)}") 