from collections.abc import Generator, Iterator
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.db import connection
from django.http.request import HttpRequest
from django.utils.functional import cached_property

from authentik.admin.files.backends.base import ManageableBackend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG
from authentik.lib.utils.time import timedelta_from_string


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

    @cached_property
    def base_path(self) -> str:
        """S3 key prefix: {usage}/{schema}/"""
        return f"{self.usage.value}/{connection.schema_name}"

    @cached_property
    def bucket_name(self) -> str:
        """Get S3 bucket name from configuration."""
        return CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.bucket_name",
            CONFIG.get(f"storage.{self.name}.bucket_name"),
        )

    @cached_property
    def session(self) -> boto3.Session:
        """Create boto3 session with configured credentials."""
        session_profile = CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.session_profile",
            CONFIG.get(f"storage.{self.name}.session_profile", None),
        )
        if session_profile is not None:
            return boto3.Session(profile_name=session_profile)
        else:
            aws_access_key_id = CONFIG.refresh(
                f"storage.{self.usage.value}.{self.name}.access_key",
                CONFIG.refresh(f"storage.{self.name}.access_key", None),
            )
            aws_secret_access_key = CONFIG.refresh(
                f"storage.{self.usage.value}.{self.name}.secret_key",
                CONFIG.refresh(f"storage.{self.name}.secret_key", None),
            )
            aws_session_token = CONFIG.refresh(
                f"storage.{self.usage.value}.{self.name}.security_token",
                CONFIG.refresh(f"storage.{self.name}.security_token", None),
            )
            return boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )

    @cached_property
    def client(self):
        """Create S3 client with configured endpoint and region."""
        endpoint_url = CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.endpoint",
            CONFIG.get(f"storage.{self.name}.endpoint", None),
        )
        region_name = CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.region",
            CONFIG.get(f"storage.{self.name}.region", None),
        )
        # Configure addressing style which needed for R2 and some S3-compatible services
        addressing_style = CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.addressing_style",
            CONFIG.get(f"storage.{self.name}.addressing_style", "auto"),
        )

        return self.session.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
        )

    @cached_property
    def bucket(self):
        return self.client.Bucket(self.bucket_name)

    @property
    def manageable(self) -> bool:
        return True

    def supports_file(self, name: str) -> bool:
        """We support all file usages"""
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

    def file_url(self, name: str, request: HttpRequest | None = None) -> str:
        """Generate presigned URL for file access."""
        use_https = CONFIG.get_bool(
            f"storage.{self.usage.value}.{self.name}.secure_urls",
            CONFIG.get_bool(f"storage.{self.name}.secure_urls", True),
        )

        params = {
            "Bucket": self.bucket_name,
            "Key": f"{self.base_path}/{name}",
        }

        expires_in = timedelta_from_string(
            CONFIG.get(
                f"storage.{self.usage.value}.{self.name}.presigned_expiry",
                CONFIG.get(f"storage.{self.name}.presigned_expiry", "minutes=15"),
            )
        )

        url = self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in.total_seconds(),
            HttpMethod="GET",
        )

        # Support custom domain for S3-compatible storage (so not AWS)
        # Well, can't you do custom domains on AWS as well?
        custom_domain = CONFIG.get(
            f"storage.{self.usage.value}.{self.name}.custom_domain",
            CONFIG.get(f"storage.{self.name}.custom_domain", None),
        )
        if custom_domain:
            parsed = urlsplit(url)
            scheme = "https" if use_https else "http"
            url = f"{scheme}://{custom_domain}{parsed.path}?{parsed.query}"

        return url

    def save_file(self, name: str, content: bytes) -> None:
        """Save file to S3."""
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}/{name}",
            Body=content,
            ACL="private",
        )

    @contextmanager
    def save_file_stream(self, name: str) -> Iterator:
        """Context manager for streaming file writes to S3."""
        # Keep files in memory up to 5 MB
        with SpooledTemporaryFile(max_size=5 * 1024 * 1024, suffix=".S3File") as file:
            yield file
            file.seek(0)
            self.client.upload_fileobj(
                Filobj=file,
                Bucket=self.bucket_name,
                Key=f"{self.base_path}/{name}",
                ExtraArgs={
                    "ACL": "private",
                },
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
