import re
import uuid
from enum import Enum
from pathlib import Path, PurePosixPath

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.admin.files.backend import (
    Backend,
    FileBackend,
    PassthroughBackend,
    S3Backend,
    StaticBackend,
    Usage,
    get_allowed_api_usages,
    get_mime_from_filename,
    get_storage_config,
)

LOGGER = get_logger()


def sanitize_file_path(file_path: str) -> str:
    """Sanitize file path to prevent directory traversal attacks and ensure safe filenames.
    """
    if not file_path:
        raise ValidationError(_("File path cannot be empty"))

    # Strip whitespace
    file_path = file_path.strip()

    # Allow alphanumeric, dots, hyphens, underscores, and forward slashes (for paths)
    if not re.match(r"^[a-zA-Z0-9._/-]+$", file_path):
        raise ValidationError(
            _("Filename can only contain letters, numbers, dots, hyphens, and underscores")
        )

    # Convert to posix path for consistent handling
    path = PurePosixPath(file_path)

    # Check for absolute paths
    if path.is_absolute():
        raise ValidationError(_("Absolute paths are not allowed"))

    # Normalize the path and check for directory traversal
    normalized = str(path)

    # Check for parent directory references or current directory at start
    if ".." in path.parts:
        raise ValidationError(_("Parent directory references (..) are not allowed"))

    # Disallow paths starting with dot (hidden files at root level)
    if normalized.startswith("."):
        raise ValidationError(_("Paths cannot start with '.'"))

    # Check path length limits
    if len(normalized) > 1024:
        raise ValidationError(_("File path too long (max 1024 characters)"))

    for part in path.parts:
        if len(part) > 255:
            raise ValidationError(_("Path component too long (max 255 characters)"))

    # Remove any duplicate slashes
    normalized = re.sub(r"/+", "/", normalized)

    # Final safety check: ensure the normalized path doesn't escape
    if normalized.startswith("/") or normalized.startswith(".."):
        raise ValidationError("Invalid file path")

    return normalized


class FileSerializer(PassiveSerializer):
    name = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    mime_type = serializers.CharField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    usage = serializers.ChoiceField(
        choices=[(u.value, u.value) for u in Usage],
        read_only=True,
    )


class FileUploadRequestSerializer(PassiveSerializer):
    file = serializers.FileField(required=True)
    path = serializers.CharField(required=False, allow_blank=True)
    usage = serializers.ChoiceField(
        choices=[(u.value, u.value) for u in get_allowed_api_usages()],
        default=Usage.MEDIA.value,
        required=False,
    )


class UsageSerializer(PassiveSerializer):
    value = serializers.CharField()
    label = serializers.CharField()


class FileViewSet(ViewSet):
    serializer_class = FileSerializer
    parser_classes = [MultiPartParser]
    # Dummy queryset for permission checks
    queryset = User.objects.none()

    def _build_file_response(
        self, file_path: str, backend: Backend, usage: Usage
    ) -> dict:
        """Build standardized file response with schema prefix for display

        Args:
            file_path: Relative file path (e.g., "my-icon.png")
            backend: Storage backend instance
            usage: Usage type

        Returns:
            Dictionary with file information including schema-prefixed name
        """
        from django.db import connection

        # Only include schema prefix for manageable backends (MEDIA, REPORTS)
        # Non-manageable files (static, passthrough) are shared across tenants
        if backend.manageable:
            display_name = f"{connection.schema_name}/{file_path}"
        else:
            display_name = file_path

        return {
            "name": display_name,
            "url": backend.file_url(file_path),
            "mime_type": get_mime_from_filename(file_path),
            "size": backend.file_size(file_path),
            "usage": usage.value,
        }

    def _strip_schema_prefix(self, file_path: str) -> str:
        """Strip schema prefix from file path if present

        Args:
            file_path: File path possibly with schema prefix (e.g., "public/my-icon.png")

        Returns:
            File path without schema prefix (e.g., "my-icon.png")
        """
        from django.db import connection

        schema_prefix = f"{connection.schema_name}/"
        return file_path.removeprefix(schema_prefix)

    def _build_paginated_response(self, results: list) -> dict:
        """Build standardized paginated response

        Args:
            results: List of file response dictionaries

        Returns:
            Response dictionary with pagination metadata and results
        """
        count = len(results)
        return {
            "pagination": {
                "next": 0,
                "previous": 0,
                "count": count,
                "current": 1,
                "total_pages": 1 if count > 0 else 0,
                "start_index": 1 if count > 0 else 0,
                "end_index": count,
            },
            "results": results,
        }

    def _get_backend(self, usage: Usage) -> Backend:
        """Get the appropriate backend instance based on configuration

        Supports usage-specific overrides:
        - storage.media.backend or storage.reports.backend
        - Falls back to storage.backend
        """
        LOGGER.debug("FileViewSet._get_backend called", usage=usage.value)
        backend_type = get_storage_config(usage, "backend", "file")
        LOGGER.debug("FileViewSet._get_backend backend_type determined",
                    backend_type=backend_type,
                    usage=usage.value)

        if backend_type == "file":
            LOGGER.debug("FileViewSet._get_backend creating FileBackend")
            return FileBackend(usage)
        elif backend_type == "s3":
            LOGGER.debug("FileViewSet._get_backend creating S3Backend")
            return S3Backend(usage)
        else:
            LOGGER.error("Unknown storage backend configured",
                        backend_type=backend_type,
                        usage=usage.value)
            raise ValidationError(f"Unknown storage backend: {backend_type}")

    @extend_schema(responses={200: UsageSerializer(many=True)})
    @action(detail=False, methods=["GET"])
    def usages(self, request: Request) -> Response:
        """Get available usage types"""
        allowed = get_allowed_api_usages()
        usages = [{"value": u.value, "label": u.value.title()} for u in allowed]
        return Response(usages)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="usage",
                type=str,
                enum=[u.value for u in get_allowed_api_usages()],
                default=Usage.MEDIA.value,
                description="Usage type",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                required=False,
                description="Search for files by name (case-insensitive substring match)",
            ),
            OpenApiParameter(
                name="includeStatic",
                type=bool,
                required=False,
                description="Include static files in the results",
            ),
        ],
        responses={200: FileSerializer(many=True)},
    )
    def list(self, request: Request) -> Response:
        """List files from storage backend"""
        usage_param = request.query_params.get("usage", Usage.MEDIA.value)
        search_query = request.query_params.get("search", "").strip().lower()
        include_static = request.query_params.get("includeStatic", "").lower() in ("true", "1", "yes")

        LOGGER.debug("FileViewSet.list called",
                    usage_param=usage_param,
                    search_query=search_query,
                    include_static=include_static,
                    user=request.user.username if hasattr(request.user, 'username') else 'anonymous')

        try:
            usage = Usage(usage_param)
            LOGGER.debug("FileViewSet.list usage parsed", usage=usage.value)
        except ValueError as e:
            LOGGER.warning("Invalid usage parameter provided",
                          usage_param=usage_param,
                          error=str(e))
            raise ValidationError(f"Invalid usage: {usage_param}")

        allowed_usages = get_allowed_api_usages()
        LOGGER.debug("FileViewSet.list allowed_usages check",
                    allowed_usages=[u.value for u in allowed_usages],
                    requested_usage=usage.value)

        if usage not in allowed_usages:
            LOGGER.warning("Usage not accessible via API",
                          usage=usage.value,
                          allowed_usages=[u.value for u in allowed_usages])
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        LOGGER.debug("FileViewSet.list getting primary backend", usage=usage.value)
        backends = [self._get_backend(usage)]
        LOGGER.debug("FileViewSet.list backends initialized",
                    backend_count=len(backends),
                    primary_backend=backends[0].__class__.__name__,
                    include_static=include_static)

        if include_static:
            LOGGER.debug("FileViewSet.list adding StaticBackend")
            backends.append(StaticBackend(usage))

        # Backend is source of truth - list all files from storage
        files = []
        LOGGER.debug("FileViewSet.list iterating backends", backend_count=len(backends))
        for idx, backend in enumerate(backends):
            LOGGER.debug("FileViewSet.list processing backend",
                        backend_index=idx,
                        backend=backend.__class__.__name__,
                        usage=backend.usage.value)

            file_count_from_backend = 0
            for file_path in backend.list_files():
                # Apply search filter if provided
                if search_query and search_query not in file_path.lower():
                    LOGGER.debug("FileViewSet.list skipping file (search filter)",
                                file=file_path,
                                search_query=search_query)
                    continue

                file_count_from_backend += 1
                LOGGER.debug("FileViewSet.list adding file",
                            file=file_path,
                            backend=backend.__class__.__name__)
                files.append(self._build_file_response(file_path, backend, backend.usage))

            LOGGER.debug("FileViewSet.list backend iteration complete",
                        backend=backend.__class__.__name__,
                        files_from_backend=file_count_from_backend)

        LOGGER.info("Listing files complete",
                   usage=usage.value,
                   total_files=len(files),
                   search_applied=bool(search_query),
                   include_static=include_static)
        return Response(self._build_paginated_response(files))

    @extend_schema(
        request=FileUploadRequestSerializer,
        responses={200: FileSerializer},
    )
    @action(detail=False, methods=["POST"])
    def upload(self, request: Request) -> Response:
        """Upload file to storage backend"""
        LOGGER.debug("FileViewSet.upload called",
                    user=request.user.username if hasattr(request.user, 'username') else 'anonymous')

        serializer = FileUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]
        custom_path = serializer.validated_data.get("path", "").strip()
        usage_value = serializer.validated_data.get("usage", Usage.MEDIA.value)

        LOGGER.debug("FileViewSet.upload validated data",
                    original_filename=file.name,
                    custom_path=custom_path,
                    usage_value=usage_value,
                    file_size=file.size)

        try:
            usage = Usage(usage_value)
            LOGGER.debug("FileViewSet.upload usage parsed", usage=usage.value)
        except ValueError as e:
            LOGGER.warning("Invalid usage parameter in upload",
                          usage_value=usage_value,
                          error=str(e))
            raise ValidationError(f"Invalid usage: {usage_value}")

        allowed_usages = get_allowed_api_usages()
        if usage not in allowed_usages:
            LOGGER.warning("Upload attempted with disallowed usage",
                          usage=usage.value,
                          allowed_usages=[u.value for u in allowed_usages])
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        backend = self._get_backend(usage)

        # Determine file path
        if custom_path:
            # Use custom path if provided
            file_path = custom_path
            # Add extension from original filename if not present
            path_obj = PurePosixPath(file_path)
            if not path_obj.suffix and Path(file.name).suffix:
                file_path = f"{file_path}{Path(file.name).suffix}"
                LOGGER.debug("FileViewSet.upload added extension to custom path",
                            original_path=custom_path,
                            final_path=file_path)
        else:
            # Use original filename
            file_path = file.name
            LOGGER.debug("FileViewSet.upload using original filename", file_path=file_path)

        # Sanitize path to prevent directory traversal
        LOGGER.debug("FileViewSet.upload sanitizing path", unsanitized_path=file_path)
        file_path = sanitize_file_path(file_path)
        LOGGER.debug("FileViewSet.upload path sanitized", sanitized_path=file_path)

        # Save to backend
        LOGGER.debug("FileViewSet.upload reading file content", file_size=file.size)
        content = file.read()
        LOGGER.debug("FileViewSet.upload saving to backend",
                    backend=backend.__class__.__name__,
                    file_path=file_path,
                    content_size=len(content))
        backend.save_file(file_path, content)

        LOGGER.info("File uploaded successfully",
                   file_path=file_path,
                   usage=usage.value,
                   backend=backend.__class__.__name__,
                   size=len(content))

        return Response(self._build_file_response(file_path, backend, usage))

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                required=True,
                description="File path to delete",
            ),
            OpenApiParameter(
                name="usage",
                type=str,
                enum=[u.value for u in get_allowed_api_usages()],
                default=Usage.MEDIA.value,
                description="Usage type",
            ),
        ],
        responses={200: None},
    )
    @action(detail=False, methods=["DELETE"])
    def delete(self, request: Request) -> Response:
        """Delete file from storage backend"""
        file_path = request.query_params.get("name")
        usage_param = request.query_params.get("usage", Usage.MEDIA.value)

        LOGGER.debug("FileViewSet.delete called",
                    file_path=file_path,
                    usage_param=usage_param,
                    user=request.user.username if hasattr(request.user, 'username') else 'anonymous')

        if not file_path:
            LOGGER.warning("Delete attempted without file path")
            raise ValidationError("name parameter is required")

        LOGGER.debug("FileViewSet.delete stripping schema prefix", original_path=file_path)
        file_path = self._strip_schema_prefix(file_path)
        LOGGER.debug("FileViewSet.delete schema prefix stripped", file_path=file_path)

        LOGGER.debug("FileViewSet.delete sanitizing path", unsanitized_path=file_path)
        file_path = sanitize_file_path(file_path)
        LOGGER.debug("FileViewSet.delete path sanitized", sanitized_path=file_path)

        try:
            usage = Usage(usage_param)
            LOGGER.debug("FileViewSet.delete usage parsed", usage=usage.value)
        except ValueError as e:
            LOGGER.warning("Invalid usage parameter in delete",
                          usage_param=usage_param,
                          error=str(e))
            raise ValidationError(f"Invalid usage: {usage_param}")

        allowed_usages = get_allowed_api_usages()
        if usage not in allowed_usages:
            LOGGER.warning("Delete attempted with disallowed usage",
                          usage=usage.value,
                          allowed_usages=[u.value for u in allowed_usages])
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        backend = self._get_backend(usage)

        # Delete from backend
        LOGGER.debug("FileViewSet.delete deleting from backend",
                    backend=backend.__class__.__name__,
                    file_path=file_path)
        backend.delete_file(file_path)

        LOGGER.info("File deleted successfully",
                   file_path=file_path,
                   usage=usage.value,
                   backend=backend.__class__.__name__)

        return Response({"message": f"File {file_path} deleted successfully"})
