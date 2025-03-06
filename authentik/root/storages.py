"""authentik storage backends with multi-tenant support for S3 and filesystem"""

import os
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, NoRegionError
from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.db import connection
from storages.backends.s3 import S3Storage as BaseS3Storage
from storages.utils import clean_name, safe_join
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
                error=str(e)
            )
            raise
        except OSError as e:
            LOGGER.error(
                "Filesystem error creating storage directory",
                path=str(self._base_path),
                error=str(e)
            )
            raise

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
        if not base_url.endswith('/'):
            LOGGER.warning(
                "MEDIA_URL should end with '/' for proper URL composition",
                current_value=base_url
            )
            base_url += '/'
        return f"{base_url}{self.tenant_prefix}/"

    def path(self, name: str) -> str:
        """Return full filesystem path to the file"""
        try:
            full_path = safe_join(self.location, name)
            LOGGER.debug("Resolved file path", name=name, path=full_path)
            return full_path
        except ValueError as e:
            LOGGER.error(
                "Invalid file path requested",
                name=name,
                location=self.location,
                error=str(e)
            )
            raise SuspiciousOperation(f"Invalid path: {name}") from e


class S3Storage(TenantAwareStorage, BaseS3Storage):
    """Multi-tenant S3 storage backend"""
    
    CONFIG_KEYS = {
        'session_profile': 'storage.media.s3.session_profile',
        'access_key': 'storage.media.s3.access_key',
        'secret_key': 'storage.media.s3.secret_key',
        'security_token': 'storage.media.s3.security_token',
    }

    def __init__(self, **kwargs):
        self._validate_configuration()
        super().__init__(**kwargs)
        self._client = None  # Cached client instance

    def _validate_configuration(self):
        """Validate configuration and log potential issues"""
        if self.session_profile and (self.access_key or self.secret_key):
            LOGGER.error(
                "Conflicting S3 storage configuration",
                session_profile=self.session_profile,
                has_access_key=bool(self.access_key),
                has_secret_key=bool(self.secret_key)
            )
            raise ImproperlyConfigured(
                "AUTHENTIK_STORAGE__MEDIA__S3__SESSION_PROFILE should not be provided with "
                "AUTHENTIK_STORAGE__MEDIA__S3__ACCESS_KEY and AUTHENTIK_STORAGE__MEDIA__S3__SECRET_KEY"
            )
        
        if not self.session_profile and not (self.access_key and self.secret_key):
            LOGGER.error(
                "Incomplete S3 configuration",
                has_session_profile=bool(self.session_profile),
                has_access_key=bool(self.access_key),
                has_secret_key=bool(self.secret_key)
            )
            raise ImproperlyConfigured(
                "Either AWS session profile or access key/secret pair must be configured"
            )

    def _get_config_value(self, key: str) -> Optional[str]:
        """Get refreshed configuration value"""
        return CONFIG.refresh(self.CONFIG_KEYS[key], None)

    @property
    def session_profile(self) -> Optional[str]:
        """AWS session profile name"""
        return self._get_config_value('session_profile')

    @property
    def access_key(self) -> Optional[str]:
        """AWS access key ID"""
        return self._get_config_value('access_key')

    @property
    def secret_key(self) -> Optional[str]:
        """AWS secret access key"""
        return self._get_config_value('secret_key')

    @property
    def security_token(self) -> Optional[str]:
        """AWS temporary security token"""
        return self._get_config_value('security_token')

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
                self._client = session.client('s3')
                LOGGER.debug("Created S3 client", 
                           session_profile=self.session_profile,
                           region=self.region_name)
            except (NoCredentialsError, NoRegionError) as e:
                LOGGER.critical(
                    "AWS credentials/region configuration error",
                    error=str(e),
                    tenant=self.tenant_prefix
                )
                raise ImproperlyConfigured(f"AWS configuration error: {e}") from e
            except ClientError as e:
                LOGGER.error(
                    "AWS client initialization failed",
                    error_code=e.response['Error']['Code'],
                    message=e.response['Error']['Message'],
                    tenant=self.tenant_prefix
                )
                raise
            except Exception as e:
                LOGGER.error(
                    "Unexpected error creating S3 client",
                    error=str(e),
                    tenant=self.tenant_prefix
                )
                raise
        return self._client

    def _normalize_name(self, name: str) -> str:
        """Create tenant-aware S3 key"""
        try:
            normalized = safe_join(self.location, self.get_tenant_path(name))
            LOGGER.debug("Normalized S3 key", original=name, normalized=normalized)
            return normalized
        except ValueError as e:
            LOGGER.error(
                "Invalid S3 key path detected",
                name=name,
                tenant=self.tenant_prefix,
                error=str(e)
            )
            raise SuspiciousOperation(f"Invalid path: {name}") from e

    def _randomize_filename(self, filename: str) -> str:
        """Prevent filename collisions using UUID"""
        stem = uuid.uuid4().hex
        suffix = Path(filename).suffix
        randomized = f"{stem}{suffix}"
        LOGGER.debug("Randomized filename", original=filename, randomized=randomized)
        return randomized

    def _save(self, name: str, content) -> str:
        """Save file with randomized name and tenant prefix"""
        try:
            randomized_name = self._randomize_filename(name)
            LOGGER.info(
                "Saving file to S3",
                original_name=name,
                randomized_name=randomized_name,
                tenant=self.tenant_prefix
            )
            return super()._save(randomized_name, content)
        except ClientError as e:
            LOGGER.error(
                "S3 upload failed",
                error_code=e.response['Error']['Code'],
                message=e.response['Error']['Message'],
                key=randomized_name,
                tenant=self.tenant_prefix
            )
            raise
        except Exception as e:
            LOGGER.error(
                "Unexpected error saving file to S3",
                name=name,
                error=str(e),
                tenant=self.tenant_prefix
            )
            raise

    def url(self, name: str, **kwargs) -> str:
        """Generate URL without signing parameters when using custom domain"""
        try:
            url = super().url(name, **kwargs)
            
            if not self.custom_domain:
                return url

            parsed = urlsplit(url)
            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            
            signing_params = {
                'x-amz-algorithm', 'x-amz-credential', 'x-amz-date',
                'x-amz-expires', 'x-amz-signedheaders', 'x-amz-signature',
                'x-amz-security-token', 'awsaccesskeyid', 'expires', 'signature'
            }
            
            clean_params = [
                (k, v) for k, v in query_params
                if k.lower() not in signing_params
            ]
            
            return parsed._replace(
                query=urlencode(clean_params, doseq=True)
            ).geturl()
        except ClientError as e:
            LOGGER.error(
                "S3 URL generation failed",
                error_code=e.response['Error']['Code'],
                message=e.response['Error']['Message'],
                key=name,
                tenant=self.tenant_prefix
            )
            raise
        except Exception as e:
            LOGGER.error(
                "Unexpected error generating URL",
                name=name,
                error=str(e),
                tenant=self.tenant_prefix
            )
            raise

    def get_valid_name(self, name: str) -> str:
        """Return valid S3 key name maintaining file extension"""
        try:
            clean_name = Path(name).name
            valid_name = super().get_valid_name(clean_name)
            LOGGER.debug("Cleaned file name", original=name, cleaned=valid_name)
            return valid_name
        except Exception as e:
            LOGGER.error(
                "Filename validation failed",
                original_name=name,
                error=str(e),
                tenant=self.tenant_prefix
            )
            raise
