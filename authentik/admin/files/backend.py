import mimetypes
import os
from abc import ABC, abstractmethod
from collections.abc import Generator
from enum import Enum
from pathlib import Path
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from django.db import connection
from django.utils.functional import cached_property
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


def get_storage_config(usage: "Usage", key: str, default=None):
    """Get storage configuration with usage-specific override support.

    Lookup order:
    1. storage.<usage>.<key> (e.g., storage.media.backend)
    2. storage.<key> (e.g., storage.backend)
    3. default value
    """
    usage_key = f"storage.{usage.value}.{key}"
    fallback_key = f"storage.{key}"

    LOGGER.debug("get_storage_config called", usage=usage.value, key=key, usage_key=usage_key, fallback_key=fallback_key, default=default)

    usage_specific = CONFIG.get(usage_key, None)
    LOGGER.debug("get_storage_config usage_specific lookup result",
                 key=usage_key,
                 value=usage_specific,
                 value_type=type(usage_specific).__name__,
                 value_str=str(usage_specific),
                 is_none=usage_specific is None)

    if usage_specific is not None:
        LOGGER.debug("get_storage_config returning usage_specific", key=usage_key, value=usage_specific)
        return usage_specific

    fallback_value = CONFIG.get(fallback_key, default)
    LOGGER.debug("get_storage_config fallback lookup result",
                 key=fallback_key,
                 value=fallback_value,
                 value_type=type(fallback_value).__name__,
                 value_str=str(fallback_value),
                 default=default)
    LOGGER.debug("get_storage_config returning fallback", key=fallback_key, value=fallback_value)
    return fallback_value


def get_mime_from_filename(filename: str) -> str:
    """Get mime type from filename"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


class Usage(str, Enum):
    """Usage types for file storage"""

    MEDIA = "media"
    REPORTS = "reports"


class Backend(ABC):
    """Base class for file storage backends

    Class attributes:
    - allowed_usages: List of Usage types this backend can handle
    - manageable: Whether files can be uploaded/deleted through the API
    """
    allowed_usages: list[Usage] = []
    manageable: bool = True

    @classmethod
    def get_allowed_api_usages(cls) -> list[Usage]:
        """Get usages that can be accessed via the files API"""
        return [u for u in cls.allowed_usages if cls.manageable]

    def __init__(self, usage: Usage):
        LOGGER.debug("Backend.__init__ called",
                    backend_class=self.__class__.__name__,
                    usage=usage.value,
                    manageable=self.manageable,
                    allowed_usages=[u.value for u in self.allowed_usages])
        self.usage = usage
        # Only get backend config for manageable backends
        if self.manageable:
            LOGGER.debug("Backend.__init__ getting backend type for manageable backend", backend_class=self.__class__.__name__)
            self._backend_type = get_storage_config(usage, "backend", "file")
            LOGGER.info(f"Initialized {self.__class__.__name__} backend", usage=usage.value, backend_type=self._backend_type)
        else:
            self._backend_type = None
            LOGGER.debug("Backend.__init__ non-manageable backend, skipping backend_type", backend_class=self.__class__.__name__)

    def get_config(self, key: str, default=None):
        """Get configuration value with usage-specific override support"""
        LOGGER.debug("Backend.get_config called",
                    backend_class=self.__class__.__name__,
                    usage=self.usage.value,
                    key=key,
                    default=default)
        result = get_storage_config(self.usage, key, default)
        LOGGER.debug("Backend.get_config result",
                    backend_class=self.__class__.__name__,
                    key=key,
                    result=result,
                    result_type=type(result).__name__)
        return result

    @abstractmethod
    def can_manage_file(self, name: str) -> bool:
        pass

    @abstractmethod
    def list_files(self) -> Generator[str]:
        pass

    @abstractmethod
    def save_file(self, name: str, content: bytes) -> None:
        pass

    @abstractmethod
    def save_file_stream(self, name: str):
        """Context manager for streaming file writes

        Usage:
            with backend.save_file_stream("output.csv") as f:
                f.write("data...")
        """
        pass

    @abstractmethod
    def delete_file(self, name: str) -> None:
        pass

    @abstractmethod
    def file_url(self, name: str) -> str:
        pass

    @abstractmethod
    def file_size(self, name: str) -> int:
        pass


class StaticBackend(Backend):
    """Read-only backend for static files from web/dist/assets

    Used for serving built-in static assets like icons and images.
    Files cannot be uploaded or deleted through this backend.
    Only accessible through resolve_file_url when a static path is detected.
    """
    allowed_usages = [Usage.MEDIA]
    manageable = False

    def can_manage_file(self, name: str) -> bool:
        return name.startswith("/static") or name.startswith("web/dist/assets")

    def list_files(self) -> Generator[str]:
        # List built-in source icons
        sources_dir = Path("web/authentik/sources")
        if sources_dir.exists():
            for file_path in sources_dir.iterdir():
                if file_path.is_file() and (file_path.suffix in [".svg", ".png"]):
                    yield f"/static/authentik/sources/{file_path.name}"

        # List other static assets
        for dir in ("assets/icons", "assets/images"):
            dist_dir = Path(f"web/dist/{dir}")
            if dist_dir.exists():
                for file_path in dist_dir.rglob("*"):
                    if file_path.is_file() and (file_path.suffix in [".svg", ".png"]):
                        yield f"/static/{dir}/{file_path.name}"

    def file_url(self, name: str) -> str:
        prefix = CONFIG.get("web.path", "/")[:-1]
        if name.startswith("/static"):
            return prefix + name
        if name.startswith("web/dist/assets"):
            return f"{prefix}/static/dist/{name.removeprefix('web/dist/')}"
        raise RuntimeError

    def file_size(self, name: str) -> int:
        return 0  # Static files size not tracked

    def save_file(self, name: str, content: bytes) -> None:
        raise NotImplementedError("Cannot save files to static backend")

    def save_file_stream(self, name: str):
        raise NotImplementedError("Cannot save files to static backend")

    def delete_file(self, name: str) -> None:
        raise NotImplementedError("Cannot delete files from static backend")


class PassthroughBackend(Backend):
    """Passthrough backend for external URLs and special schemes

    Handles external resources that aren't stored in authentik:
    - Font Awesome icons (fa://...)
    - HTTP/HTTPS URLs (http://..., https://...)

    Files "managed" by this backend are just passed through as-is.
    No upload, delete, or listing operations are supported.
    Only accessible through resolve_file_url when an external URL is detected.
    """
    allowed_usages = [Usage.MEDIA]
    manageable = False

    def can_manage_file(self, name: str) -> bool:
        return name.startswith("fa://") or name.startswith("http:") or name.startswith("https:") # hmmm.

    def list_files(self) -> Generator[str]:
        yield from []

    def file_url(self, name: str) -> str:
        return name

    def file_size(self, name: str) -> int:
        return 0  # External files size not tracked

    def save_file(self, name: str, content: bytes) -> None:
        raise NotImplementedError("Cannot save files to passthrough backend")

    def save_file_stream(self, name: str):
        raise NotImplementedError("Cannot save files to passthrough backend")

    def delete_file(self, name: str) -> None:
        raise NotImplementedError("Cannot delete files from passthrough backend")


class FileBackend(Backend):
    """Local filesystem backend for file storage

    Stores files in a local directory structure:
    - Path: {base_dir}/{usage}/{schema}/{filename}
    - Supports full file management (upload, delete, list)
    - Used when storage.backend=file (default)
    """
    allowed_usages = list(Usage)  # All usages
    manageable = True

    @property
    def base_path(self) -> Path:
        """Path structure: {base_dir}/{usage}/{schema}"""
        LOGGER.debug("FileBackend.base_path property accessed",
                    usage=self.usage.value,
                    schema=connection.schema_name,
                    backend_type=self._backend_type)

        file_path = self.get_config("file.path", "/data")
        base_dir = Path(file_path)
        LOGGER.debug("FileBackend.base_path base_dir created", base_dir=str(base_dir))

        result = base_dir / self.usage.value / connection.schema_name
        LOGGER.info("File storage base path resolved",
                   usage=self.usage.value,
                   schema=connection.schema_name,
                   path=str(result))
        LOGGER.debug("FileBackend.base_path returning", path=str(result), exists=result.exists())
        return result

    def can_manage_file(self, name: str) -> bool:
        return self._backend_type == "file"

    def list_files(self) -> Generator[str]:
        """List all files returning relative paths from base_path"""
        LOGGER.debug("FileBackend.list_files called",
                    usage=self.usage.value,
                    schema=connection.schema_name)

        LOGGER.debug("FileBackend.list_files accessing base_path property")
        base_path = self.base_path
        LOGGER.debug("FileBackend.list_files base_path retrieved",
                    path=str(base_path),
                    exists=base_path.exists(),
                    is_dir=base_path.is_dir() if base_path.exists() else False)

        if not base_path.exists():
            LOGGER.warning("File storage path does not exist",
                          usage=self.usage.value,
                          schema=connection.schema_name,
                          path=str(base_path))
            LOGGER.debug("FileBackend.list_files returning empty generator")
            return

        LOGGER.debug("FileBackend.list_files walking directory", path=str(base_path))
        file_count = 0
        for root, _, files in os.walk(base_path):
            LOGGER.debug("FileBackend.list_files walking",
                        root=root,
                        file_count=len(files))
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base_path)
                file_count += 1
                LOGGER.debug("FileBackend.list_files yielding file",
                            file=str(rel_path),
                            full_path=str(full_path))
                yield str(rel_path)

        LOGGER.info("Listed files from storage",
                   usage=self.usage.value,
                   schema=connection.schema_name,
                   count=file_count)

    def save_file(self, name: str, content: bytes) -> None:
        path = self.base_path / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)

    def save_file_stream(self, name: str):
        """Context manager for streaming file writes to local filesystem"""
        from contextlib import contextmanager

        @contextmanager
        def _stream():
            path = self.base_path / Path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                yield f

        return _stream()

    def delete_file(self, name: str) -> None:
        path = self.base_path / Path(name)
        path.unlink(missing_ok=True)

    def file_url(self, name: str) -> str:
        prefix = CONFIG.get("web.path", "/")[:-1]
        return f"{prefix}/static/{self.usage.value}/{connection.schema_name}/{name}"

    def file_size(self, name: str) -> int:
        path = self.base_path / Path(name)
        try:
            return path.stat().st_size if path.exists() else 0
        except Exception:
            return 0

    def file_exists(self, name: str) -> bool:
        """Check if a file exists"""
        path = self.base_path / Path(name)
        return path.exists()


class S3Backend(Backend):
    """S3-compatible object storage backend

    Stores files in S3 or S3-compatible storage:
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
        return self.get_config("s3.bucket_name")

    @cached_property
    def session(self) -> boto3.Session:
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
        endpoint_url = self.get_config("s3.endpoint", None)
        region_name = self.get_config("s3.region", None)

        return self.session.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=Config(signature_version="s3v4"),
        )

    def can_manage_file(self, name: str) -> bool:
        return self._backend_type == "s3"

    def list_files(self) -> Generator[str]:
        """List all files returning relative paths from base_path"""
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
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}{name}",
            Body=content,
            ACL="private",
        )

    def save_file_stream(self, name: str):
        """Context manager for streaming file writes to S3"""
        from contextlib import contextmanager
        from io import BytesIO

        @contextmanager
        def _stream():
            buffer = BytesIO()
            yield buffer
            # Upload when context closes
            buffer.seek(0)
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=f"{self.base_path}{name}",
                Body=buffer.getvalue(),
                ACL="private",
            )

        return _stream()

    def delete_file(self, name: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}{name}",
        )

    def file_url(self, name: str) -> str:
        use_https = self.get_config("s3.secure_urls", True)
        if isinstance(use_https, str):
            use_https = use_https.lower() in ("true", "1", "yes")
        http_method = "GET"

        params = {
            "Bucket": self.bucket_name,
            "Key": f"{self.base_path}{name}",
        }
        expires_in = self.get_config("s3.presigned_expiry", 3600)
        if isinstance(expires_in, str):
            expires_in = int(expires_in)

        url = self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
            HttpMethod=http_method,
        )

        custom_domain = self.get_config("s3.custom_domain", None)
        if custom_domain:
            parsed = urlsplit(url)
            scheme = "https" if use_https else "http"
            url = f"{scheme}://{custom_domain}{parsed.path}?{parsed.query}"

        return url

    def file_size(self, name: str) -> int:
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=f"{self.base_path}{name}",
            )
            return response.get("ContentLength", 0)
        except Exception:
            return 0

    def file_exists(self, name: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=f"{self.base_path}{name}",
            )
            return True
        except Exception:
            return False


def get_allowed_api_usages() -> list[Usage]:
    """Get list of usages that are accessible via the files API"""
    return [Usage.MEDIA]


def get_storage_backend(usage: Usage) -> Backend:
    """Get the appropriate storage backend for the given usage type

    Returns the configured backend (FileBackend or S3Backend) based on
    the storage.backend configuration.
    """
    LOGGER.debug("get_storage_backend called", usage=usage.value)
    backend_type = get_storage_config(usage, "backend", "file")
    LOGGER.debug("get_storage_backend backend_type determined",
                backend_type=backend_type,
                usage=usage.value)

    if backend_type == "s3":
        LOGGER.info("Using S3 storage backend", usage=usage.value)
        return S3Backend(usage)

    LOGGER.info("Using file storage backend", usage=usage.value)
    return FileBackend(usage)


def resolve_file_url(file_path: str, usage: Usage) -> str:
    """Resolve a file path to its URL using the appropriate backend

    Args:
        file_path: The file path to resolve
        usage: The usage type (MEDIA, REPORTS, etc.) to determine which backend to use

    Handles:
    - Static files (/static/...)
    - Passthrough URLs (fa://, http://, https://...)
    - Storage files (uploaded files from the specified usage backend)

    This is a convenience function that automatically determines the correct backend
    based on the file path and returns the appropriate URL.
    """
    if not file_path:
        return file_path

    # Passthrough backend for external URLs and Font Awesome
    if file_path.startswith("fa://") or file_path.startswith("http"):
        backend = PassthroughBackend(usage)
        return backend.file_url(file_path)

    # Static backend for built-in static files
    if file_path.startswith("/static") or file_path.startswith("web/dist/assets"):
        backend = StaticBackend(usage)
        return backend.file_url(file_path)

    # Storage backend for uploaded files - need to strip schema prefix if present
    schema_prefix = f"{connection.schema_name}/"
    if file_path.startswith(schema_prefix):
        file_path = file_path.removeprefix(schema_prefix)

    backend = get_storage_backend(usage)
    return backend.file_url(file_path)
