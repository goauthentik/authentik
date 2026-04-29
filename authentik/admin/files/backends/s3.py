from collections.abc import Generator, Iterator
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from typing import Any
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1, EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db.models import Q
from django.http.request import HttpRequest

from authentik.admin.files.backends.base import ManageableBackend, get_content_type
from authentik.admin.files.backends.s3_urls import S3UrlOptions, s3_file_url
from authentik.admin.files.usage import FileUsage
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.config import CONFIG
from authentik.lib.utils.time import timedelta_from_string

_CLOUDFRONT_RSA_KEY_SIZE = 2048


def _validate_cloudfront_private_key(private_key) -> None:
    """Validate a private key against CloudFront signed URL key requirements."""
    if isinstance(private_key, RSAPrivateKey):
        if private_key.key_size != _CLOUDFRONT_RSA_KEY_SIZE:
            raise ImproperlyConfigured(
                "CloudFront URL signing keypair must contain a 2048-bit RSA private key, "
                "or an ECDSA P-256 private key."
            )
        return
    if isinstance(private_key, EllipticCurvePrivateKey):
        if not isinstance(private_key.curve, SECP256R1):
            raise ImproperlyConfigured(
                "CloudFront URL signing keypair must contain an ECDSA P-256 private key, "
                "or a 2048-bit RSA private key."
            )
        return
    raise ImproperlyConfigured(
        "CloudFront URL signing keypair must contain an RSA or ECDSA private key."
    )


def _cloudfront_private_key_from_keypair(selector: str) -> str:
    """Return the PEM private key for a CloudFront signing Certificate-Key Pair."""
    query = Q(name=selector)
    try:
        query |= Q(kp_uuid=UUID(str(selector)))
    except ValueError:
        pass

    keypair = CertificateKeyPair.objects.filter(query).first()
    if keypair is None:
        raise ImproperlyConfigured(
            "CloudFront URL signing keypair was not found. Configure "
            "storage.s3.cloudfront_keypair with a Certificate-Key Pair name or UUID."
        )
    if not keypair.key_data:
        raise ImproperlyConfigured("CloudFront URL signing keypair must include a private key.")
    private_key = keypair.private_key
    _validate_cloudfront_private_key(private_key)
    return keypair.key_data


class S3Backend(ManageableBackend):
    """S3-compatible object storage backend.

    Stores files in s3-compatible storage:
    - Key prefix: {usage}/{schema}/{filename}
    - Supports full file management (upload, delete, list)
    - Generates presigned URLs for file access
    - Used when storage.backend=s3
    """

    allowed_usages = list(FileUsage)  # All usages
    name = "s3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = {}
        self._session = None

    def _get_config(self, key: str, default: Any = None) -> tuple[Any, bool]:
        unset = object()
        current = self._config.get(key, unset)
        refreshed = CONFIG.refresh(
            f"storage.{self.usage.value}.{self.name}.{key}",
            CONFIG.refresh(f"storage.{self.name}.{key}", default),
        )
        if current is unset:
            current = refreshed
        self._config[key] = refreshed
        return (refreshed, current != refreshed)

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        return CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.{key}",
            CONFIG.get(f"storage.{self.name}.{key}", default),
        )

    def _get_config_bool(self, key: str, default: bool = False) -> bool:
        return CONFIG.get_bool(
            f"storage.{self.usage.value}.{self.name}.{key}",
            CONFIG.get_bool(f"storage.{self.name}.{key}", default),
        )

    @property
    def base_path(self) -> str:
        """S3 key prefix: {usage}/{schema}/"""
        return f"{self.usage.value}/{connection.schema_name}"

    @property
    def bucket_name(self) -> str:
        return self._get_config_value("bucket_name")

    @property
    def object_acl(self) -> str | None:
        """ACL applied to uploaded objects, or None to omit ACL entirely."""
        object_acl = self._get_config_value("object_acl", "private")
        if object_acl in (None, ""):
            return None
        return object_acl

    @property
    def cloudfront_private_key(self) -> str | None:
        """Private key loaded from an authentik Certificate-Key Pair."""
        keypair = self._get_config_value("cloudfront_keypair", None)
        if keypair in (None, ""):
            return None
        return _cloudfront_private_key_from_keypair(str(keypair))

    @property
    def session(self) -> boto3.Session:
        """Create boto3 session with configured credentials."""
        session_profile, session_profile_r = self._get_config("session_profile", None)
        if session_profile is not None:
            if session_profile_r or self._session is None:
                self._session = boto3.Session(profile_name=session_profile)
                return self._session
            else:
                return self._session
        else:
            access_key, access_key_r = self._get_config("access_key", None)
            secret_key, secret_key_r = self._get_config("secret_key", None)
            session_token, session_token_r = self._get_config("session_token", None)
            if access_key_r or secret_key_r or session_token_r or self._session is None:
                self._session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=session_token,
                )
                return self._session
            else:
                return self._session

    @property
    def client(self):
        """Create S3 client with configured endpoint and region."""
        endpoint_url = self._get_config_value("endpoint", None)
        use_ssl = self._get_config_value("use_ssl", True)
        region_name = self._get_config_value("region", None)
        addressing_style = self._get_config_value("addressing_style", "auto")
        signature_version = self._get_config_value("signature_version", "s3v4")
        # Keep signature_version pass-through and let boto3/botocore handle it.
        # In boto3's S3 configuration docs, `s3v4` (default) and deprecated `s3`
        # are the documented values:
        # https://github.com/boto/boto3/blob/791a3e8f36d83664a47b4281a0586b3546cef3ec/docs/source/guide/configuration.rst?plain=1#L398-L407
        # Botocore also supports additional signer names, so we intentionally do
        # not enforce a restricted allowlist here.

        return self.session.client(
            "s3",
            endpoint_url=endpoint_url,
            use_ssl=use_ssl,
            region_name=region_name,
            config=Config(
                signature_version=signature_version, s3={"addressing_style": addressing_style}
            ),
        )

    @property
    def manageable(self) -> bool:
        return True

    def supports_file(self, name: str) -> bool:
        """We support all files"""
        return True

    def list_files(self) -> Generator[str]:
        """List all files returning relative paths from base_path."""
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=f"{self.base_path}/")

        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                # Remove base path prefix to get relative path
                rel_path = key.removeprefix(f"{self.base_path}/")
                if rel_path:  # Skip if it's just the directory itself
                    yield rel_path

    def file_url(
        self,
        name: str,
        request: HttpRequest | None = None,
        use_cache: bool = True,
    ) -> str:
        """Generate a signed or unsigned URL for file access."""
        use_https = self._get_config_bool("secure_urls", True)
        querystring_auth = self._get_config_bool("querystring_auth", True)

        expires_in = int(
            timedelta_from_string(
                self._get_config_value("url_expiry", "minutes=15")
            ).total_seconds()
        )

        def _file_url(name: str, request: HttpRequest | None) -> str:
            return s3_file_url(
                client=self.client,
                bucket_name=self.bucket_name,
                key=f"{self.base_path}/{name}",
                options=S3UrlOptions(
                    expires_in=expires_in,
                    custom_domain=self._get_config_value("custom_domain", None),
                    use_https=use_https,
                    querystring_auth=querystring_auth,
                    cloudfront_key_id=self._get_config_value("cloudfront_key_id", None),
                    cloudfront_private_key=self.cloudfront_private_key,
                ),
            )

        if use_cache:
            return self._cache_get_or_set(name, request, _file_url, expires_in)
        else:
            return _file_url(name, request)

    def save_file(self, name: str, content: bytes) -> None:
        """Save file to S3."""
        extra_args = {}
        if self.object_acl is not None:
            extra_args["ACL"] = self.object_acl
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}/{name}",
            Body=content,
            ContentType=get_content_type(name),
            **extra_args,
        )

    @contextmanager
    def save_file_stream(self, name: str) -> Iterator:
        """Context manager for streaming file writes to S3."""
        # Keep files in memory up to 5 MB
        with SpooledTemporaryFile(max_size=5 * 1024 * 1024, suffix=".S3File") as file:
            yield file
            file.seek(0)
            extra_args = {"ContentType": get_content_type(name)}
            if self.object_acl is not None:
                extra_args["ACL"] = self.object_acl
            self.client.upload_fileobj(
                Fileobj=file,
                Bucket=self.bucket_name,
                Key=f"{self.base_path}/{name}",
                ExtraArgs=extra_args,
            )

    def delete_file(self, name: str) -> None:
        """Delete file from S3."""
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}/{name}",
        )

    def file_exists(self, name: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=f"{self.base_path}/{name}",
            )
            return True
        except ClientError:
            return False
