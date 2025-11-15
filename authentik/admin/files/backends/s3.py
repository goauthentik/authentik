"""S3-compatible object storage backend"""

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from io import BytesIO
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.db import connection
from django.utils.functional import cached_property

from authentik.admin.files.backend import Backend, Usage
from authentik.admin.files.constants import (
    S3_DEFAULT_ACL,
    S3_PRESIGNED_URL_EXPIRY_SECONDS,
)


class S3Backend(Backend):
    """S3-compatible object storage backend.

    Stores files in s3-compatible storage:
    - Key prefix: {usage}/{schema}/{filename}
    - Supports full file management (upload, delete, list)
    - Generates presigned URLs for file access
    - Used when storage.backend=s3
    """

    allowed_usages = list(Usage)  # All usages
    manageable = True

    @property
    def base_path(self) -> str:
        """S3 key prefix: {usage}/{schema}/"""
        return f"{self.usage.value}/{connection.schema_name}/"

    @cached_property
    def bucket_name(self) -> str:
        """Get S3 bucket name from configuration."""
        return self.get_config("s3.bucket_name")

    @cached_property
    def session(self) -> boto3.Session:
        """Create boto3 session with configured credentials."""
        session_profile = self.get_config("s3.session_profile", None)
        if session_profile is not None:
            return boto3.Session(profile_name=session_profile)
        else:
            return boto3.Session(
                aws_access_key_id=self.get_config("s3.access_key", None),
                aws_secret_access_key=self.get_config("s3.secret_key", None),
                aws_session_token=self.get_config("s3.security_token", None),
            )

    @cached_property
    def client(self):
        """Create S3 client with configured endpoint and region."""
        endpoint_url = self.get_config("s3.endpoint", None)
        region_name = self.get_config("s3.region", None)

        # Configure addressing style which needed for R2 and some S3-compatible services
        addressing_style = self.get_config("s3.addressing_style", "auto")

        return self.session.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
        )

    def supports_file_path(self, file_path: str) -> bool:
        """Check if this backend type is configured."""
        return self._backend_type == "s3"

    def list_files(self) -> Generator[str]:
        """List all files returning relative paths from base_path."""
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.base_path)

        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                # Remove base path prefix to get relative path
                rel_path = key.removeprefix(self.base_path)
                if rel_path:  # Skip if it's just the directory itself
                    yield rel_path

    def save_file(self, name: str, content: bytes) -> None:
        """Save file to S3."""
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}{name}",
            Body=content,
            ACL=S3_DEFAULT_ACL,
        )

    @contextmanager
    def save_file_stream(self, name: str) -> Iterator:
        """Context manager for streaming file writes to S3."""
        buffer = BytesIO()
        yield buffer
        # Upload when context closes
        buffer.seek(0)
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}{name}",
            Body=buffer.getvalue(),
            ACL=S3_DEFAULT_ACL,
        )

    def delete_file(self, name: str) -> None:
        """Delete file from S3."""
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}{name}",
        )

    def file_url(self, name: str) -> str:
        """Generate presigned URL for file access."""
        use_https = self.get_config("s3.secure_urls", True)
        if isinstance(use_https, str):
            use_https = use_https.lower() in ("true")

        params = {
            "Bucket": self.bucket_name,
            "Key": f"{self.base_path}{name}",
        }

        expires_in = self.get_config("s3.presigned_expiry", S3_PRESIGNED_URL_EXPIRY_SECONDS)
        if isinstance(expires_in, str):
            expires_in = int(expires_in)

        url = self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
            HttpMethod="GET",
        )

        # Support custom domain for S3-compatible storage (so not AWS)
        # Well, can't you do custom domains on AWS as well?
        custom_domain = self.get_config("s3.custom_domain", None)
        if custom_domain:
            parsed = urlsplit(url)
            scheme = "https" if use_https else "http"
            url = f"{scheme}://{custom_domain}{parsed.path}?{parsed.query}"

        return url

    def file_size(self, name: str) -> int:
        """Get file size in bytes."""
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=f"{self.base_path}{name}",
            )
            return response.get("ContentLength", 0)
        except ClientError:
            return 0

    def file_exists(self, name: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=f"{self.base_path}{name}",
            )
            return True
        except ClientError:
            return False
