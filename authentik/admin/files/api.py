from pathlib import Path, PurePosixPath

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from structlog.stdlib import get_logger

from authentik.admin.files.backend import Backend, Usage, get_allowed_api_usages
from authentik.admin.files.backends import PassthroughBackend, StaticBackend
from authentik.admin.files.factory import BackendFactory
from authentik.admin.files.utils import (
    add_schema_prefix,
    get_mime_from_filename,
    strip_schema_prefix,
)
from authentik.admin.files.validation import (
    sanitize_file_path,
    validate_file_size,
    validate_file_type,
)
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.events.models import Event, EventAction

LOGGER = get_logger()


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

    def _build_file_response(self, file_path: str, backend: Backend, usage: Usage) -> dict:
        """Build standardized file response with schema prefix for display.

        Args:
            file_path: Relative file path (e.g., "my-icon.png")
            backend: Storage backend instance
            usage: Usage type

        Returns:
            Dictionary with file information
        """
        # Only include schema prefix for manageable backends (MEDIA, REPORTS)
        # Non-manageable files (static, passthrough) are shared across tenants
        if backend.manageable:
            display_name = add_schema_prefix(file_path)
        else:
            display_name = file_path

        return {
            "name": display_name,
            "url": backend.file_url(file_path),
            "mime_type": get_mime_from_filename(file_path),
            "size": backend.file_size(file_path),
            "usage": usage.value,
        }

    def _build_paginated_response(self, results: list) -> dict:
        """Build standardized paginated response.

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
        """List files from storage backend."""
        usage_param = request.query_params.get("usage", Usage.MEDIA.value)
        search_query = request.query_params.get("search", "").strip().lower()
        include_static = request.query_params.get("includeStatic", "false").lower() == "true"

        try:
            usage = Usage(usage_param)
        except ValueError as e:
            LOGGER.warning(
                "Invalid usage parameter provided", usage_param=usage_param, error=str(e)
            )
            raise ValidationError(f"Invalid usage: {usage_param}") from e

        allowed_usages = get_allowed_api_usages()

        if usage not in allowed_usages:
            LOGGER.warning(
                "Usage not accessible via API",
                usage=usage.value,
                allowed_usages=[u.value for u in allowed_usages],
            )
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        backends = [BackendFactory.create(usage)]

        # For MEDIA usage, always include static and passthrough backends
        if usage == Usage.MEDIA:
            backends.append(StaticBackend(usage))
            backends.append(PassthroughBackend(usage))
        elif include_static:
            backends.append(StaticBackend(usage))

        # Backend is source of truth - list all files from storage
        files = []
        for backend in backends:
            for file_path in backend.list_files():
                # Apply search filter if provided
                if search_query and search_query not in file_path.lower():
                    continue

                files.append(self._build_file_response(file_path, backend, backend.usage))

        LOGGER.info(
            "Listed files",
            usage=usage.value,
            total_files=len(files),
            search_applied=bool(search_query),
            include_static=include_static,
        )
        return Response(self._build_paginated_response(files))

    @extend_schema(
        request=FileUploadRequestSerializer,
        responses={200: FileSerializer},
    )
    @action(detail=False, methods=["POST"])
    def upload(self, request: Request) -> Response:
        """Upload file to storage backend."""
        serializer = FileUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]
        custom_path = serializer.validated_data.get("path", "").strip()
        usage_value = serializer.validated_data.get("usage", Usage.MEDIA.value)

        # Validate file size and type
        validate_file_size(file.size)
        validate_file_type(file.content_type or "", usage_value)

        try:
            usage = Usage(usage_value)
        except ValueError as e:
            LOGGER.warning(
                "Invalid usage parameter in upload", usage_value=usage_value, error=str(e)
            )
            raise ValidationError(f"Invalid usage: {usage_value}") from e

        allowed_usages = get_allowed_api_usages()
        if usage not in allowed_usages:
            LOGGER.warning(
                "Upload attempted with disallowed usage",
                usage=usage.value,
                allowed_usages=[u.value for u in allowed_usages],
            )
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        backend = BackendFactory.create(usage)

        # Determine file path
        if custom_path:
            # Use custom path if provided
            file_path = custom_path
            # Add extension from original filename if not present
            path_obj = PurePosixPath(file_path)
            if not path_obj.suffix and Path(file.name).suffix:
                file_path = f"{file_path}{Path(file.name).suffix}"
        else:
            # Use original filename
            file_path = file.name

        # Sanitize path to prevent directory traversal
        file_path = sanitize_file_path(file_path)

        # Check if file already exists
        if backend.file_exists(file_path):
            LOGGER.warning(
                "File upload blocked - duplicate filename",
                file_path=file_path,
                backend=backend.__class__.__name__,
            )
            raise ValidationError(
                {
                    "path": [
                        (
                            f"A file with the name '{file_path}' already exists. "
                            "Please use a different name."
                        )
                    ]
                }
            )

        # Save to backend
        content = file.read()
        backend.save_file(file_path, content)

        LOGGER.info(
            "File uploaded",
            file_path=file_path,
            usage=usage.value,
            backend=backend.__class__.__name__,
            size=len(content),
        )

        # Audit log for file upload
        Event.new(
            EventAction.FILE_UPLOADED,
            file_path=file_path,
            usage=usage.value,
            backend=backend.__class__.__name__,
            size=len(content),
            mime_type=get_mime_from_filename(file_path),
        ).from_http(request)

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
        """Delete file from storage backend."""
        file_path = request.query_params.get("name")
        usage_param = request.query_params.get("usage", Usage.MEDIA.value)

        if not file_path:
            raise ValidationError("name parameter is required")

        file_path = strip_schema_prefix(file_path)
        file_path = sanitize_file_path(file_path)

        try:
            usage = Usage(usage_param)
        except ValueError as e:
            LOGGER.warning(
                "Invalid usage parameter in delete", usage_param=usage_param, error=str(e)
            )
            raise ValidationError(f"Invalid usage: {usage_param}") from e

        allowed_usages = get_allowed_api_usages()
        if usage not in allowed_usages:
            LOGGER.warning(
                "Delete attempted with disallowed usage",
                usage=usage.value,
                allowed_usages=[u.value for u in allowed_usages],
            )
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        backend = BackendFactory.create(usage)

        # Delete from backend
        backend.delete_file(file_path)

        LOGGER.info(
            "File deleted",
            file_path=file_path,
            usage=usage.value,
            backend=backend.__class__.__name__,
        )

        # Audit log for file deletion
        Event.new(
            EventAction.FILE_DELETED,
            file_path=file_path,
            usage=usage.value,
            backend=backend.__class__.__name__,
        ).from_http(request)

        return Response({"message": f"File {file_path} deleted successfully"})
