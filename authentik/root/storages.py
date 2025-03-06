"""authentik storage backends with multi-tenant support for S3 and filesystem"""

import os
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, NoRegionError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.storage import FileSystemStorage
from django.db import connection
from storages.backends.s3 import S3Storage as BaseS3Storage
from storages.utils import safe_join
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


class TenantAwareStorage:
    """Mixin providing tenant-aware path functionality"""

    @property
    def tenant_prefix(self) -> str:
        """Get current tenant schema prefix"""
        return connection.schema_name

    def get_tenant_path(self, name: str) -> str:
        """Get tenant-specific path for storage"""
        return str(Path(self.tenant_prefix) / name)


class FileStorage(TenantAwareStorage, FileSystemStorage):
    """Multi-tenant filesystem storage backend"""

    def __init__(self, *args, **kwargs):
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
        """Return a sanitized filename"""
        name = os.path.basename(name)
        return super().get_valid_name(name)

    @property
    def base_location(self) -> Path:
        """Base storage directory including tenant prefix"""
        return Path(settings.MEDIA_ROOT) / self.tenant_prefix

    @property
    def location(self) -> str:
        """Absolute path to storage directory"""
        return os.path.abspath(self.base_location)

    @property
    def base_url(self) -> str:
        """Base URL for serving stored files with tenant prefix"""
        base_url = settings.MEDIA_URL
        if not base_url.endswith("/"):
            LOGGER.warning(
                "MEDIA_URL should end with '/' for proper URL composition", current_value=base_url
            )
            base_url += "/"
        return f"{base_url}{self.tenant_prefix}/"

    def path(self, name: str) -> str:
        """Return full filesystem path to the file"""
        try:
            name = self.get_valid_name(name)
            full_path = safe_join(self.location, name)
            LOGGER.debug("Resolved file path", name=name, path=full_path)
            return full_path
        except ValueError as e:
            LOGGER.error(
                "Invalid file path requested", name=name, location=self.location, error=str(e)
            )
            raise SuspiciousOperation(f"Invalid path: {name}") from e

    def _save(self, name: str, content) -> str:
        """Save file with sanitized name"""
        name = self.get_valid_name(name)
        return super()._save(name, content)


class S3Storage(TenantAwareStorage, BaseS3Storage):
    """Multi-tenant S3 storage backend"""

    CONFIG_KEYS = {
        "session_profile": "storage.media.s3.session_profile",
        "access_key": "storage.media.s3.access_key",
        "secret_key": "storage.media.s3.secret_key",
        "security_token": "storage.media.s3.security_token",
        "bucket_name": "storage.media.s3.bucket_name",
        "region_name": "storage.media.s3.region_name",
    }

    def __init__(self, **kwargs):
        self._validate_configuration()
        super().__init__(**kwargs)
        self._client = None
        self._bucket = None
        self._file_mapping = {}

    def _validate_configuration(self):
        """Validate configuration and log potential issues"""
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
        """Get refreshed configuration value"""
        return CONFIG.refresh(self.CONFIG_KEYS[key], None)

    @property
    def session_profile(self) -> str | None:
        """AWS session profile name"""
        return self._get_config_value("session_profile")

    @property
    def access_key(self) -> str | None:
        """AWS access key ID"""
        return self._get_config_value("access_key")

    @property
    def secret_key(self) -> str | None:
        """AWS secret access key"""
        return self._get_config_value("secret_key")

    @property
    def security_token(self) -> str | None:
        """AWS temporary security token"""
        return self._get_config_value("security_token")

    @property
    def client(self):
        """Cached boto3 client instance with refreshed credentials"""
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
                    "Unexpected error creating S3 client", error=str(e), tenant=self.tenant_prefix
                )
                raise
        return self._client

    @property
    def bucket(self):
        """Get S3 bucket instance and validate access"""
        if not self._bucket:
            try:
                try:
                    self.client.list_buckets()
                except (ClientError, NoCredentialsError) as e:
                    LOGGER.critical(
                        "Invalid AWS credentials", error=str(e), tenant=self.tenant_prefix
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
                    "Unexpected error accessing S3", error=str(e), tenant=self.tenant_prefix
                )
                raise ImproperlyConfigured(f"S3 configuration error: {str(e)}") from e

        return self._bucket

    def get_valid_name(self, name: str) -> str:
        """Return a sanitized filename"""
        name = os.path.basename(name)
        return super().get_valid_name(name)

    def _normalize_name(self, name: str) -> str:
        """Normalize file path for S3 storage"""
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
        """Generate a randomized filename while preserving extension"""
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
        """Save file to S3 with tenant isolation and random filename"""
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
        """Delete file from S3"""
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
        """Generate URL without signing parameters when using custom domain"""
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
