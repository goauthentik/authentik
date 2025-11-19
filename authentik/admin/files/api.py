from pathlib import Path, PurePosixPath

from botocore.exceptions import BotoCoreError, ClientError
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from structlog.stdlib import get_logger
from rest_framework.fields import CharField

from authentik.admin.files.backends.base import Backend
from authentik.admin.files.factory import BackendFactory
from authentik.admin.files.manager import FileManager
from authentik.admin.files.usage import FileUsage, MANAGE_API_USAGES
from authentik.admin.files.utils import (
    get_mime_from_filename,
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
        choices=[(u.value, u.value) for u in FileUsage],
        read_only=True,
    )


class FileUploadSerializer(PassiveSerializer):
    file = serializers.FileField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    usage = serializers.ChoiceField(
        choices=[(u.value, u.value) for u in MANAGE_API_USAGES],
        default=FileUsage.MEDIA.value,
        required=False,
    )


class FileViewSet(ViewSet):
    pagination_class = None
    serializer_class = FileSerializer
    parser_classes = [MultiPartParser]
    # Dummy queryset for permission checks
    queryset = User.objects.none()

    @extend_schema(
        responses={
            200: inline_serializer(
                "UsageSerializer",
                {
                    "label": CharField(required=True),
                    "value": CharField(required=True),
                },
                many=True,
            )
        }
    )
    @action(detail=False, methods=["GET"])
    def manage_api_usages(self, request: Request) -> Response:
        """Get usages that can be managed through this API"""
        usages = [{"value": u.value, "name": u.value.title()} for u in MANAGE_API_USAGES]
        return Response(usages)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="usage",
                type=str,
                enum=[u.value for u in MANAGE_API_USAGES],
                default=FileUsage.MEDIA.value,
                description="Usage type",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                required=False,
                description="Search for files by name (case-insensitive substring match)",
            ),
            OpenApiParameter(
                name="manageableOnly",
                type=bool,
                required=False,
                description="Only include manageable files",
            ),
        ],
        responses={
            200: inline_serializer(
                "FileSerializer",
                {
                    "name": CharField(required=True),
                    "mime_type": CharField(required=True),
                },
                many=True,
            )
        },
    )
    def list(self, request: Request) -> Response:
        """List files from storage backend."""
        # TODO: permissions
        usage_param = request.query_params.get("usage", FileUsage.MEDIA.value)
        search_query = request.query_params.get("search", "").strip().lower()
        manageable_only = request.query_params.get("manageableOnly", "false").lower() == "true"

        try:
            usage = FileUsage(usage_param)
        except ValueError as exc:
            raise ValidationError(f"Invalid usage parameter provided: {usage_param}") from exc

        if usage not in MANAGE_API_USAGES:
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        # Backend is source of truth - list all files from storage
        files = FileManager(usage).list_files(manageable_only=manageable_only)
        if search_query:
            files = filter(lambda file: search_query in file.lower(), files)
        files = [
            {
                "name": file,
                "mime_type": get_mime_from_filename(file),
            }
            for file in files
        ]

        return Response(files)

    @extend_schema(
        request=FileUploadSerializer,
        responses={200: None},
    )
    @action(detail=False, methods=["POST"])
    def upload(self, request: Request) -> Response:
        """Upload file to storage backend."""
        # TODO: permissions
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]
        name = serializer.validated_data.get("name", "").strip()
        usage_value = serializer.validated_data.get("usage", FileUsage.MEDIA.value)

        # Validate file size and type
        validate_file_size(file.size)
        validate_file_type(file.content_type or "", usage_value)

        try:
            usage = FileUsage(usage_value)
        except ValueError as exc:
            raise ValidationError(f"Invalid usage parameter provided: {usage_value}") from exc

        if usage not in MANAGE_API_USAGES:
            raise ValidationError(f"Usage {usage.value} not accessible via this API")

        # Determine file path
        if name:
            # Add extension from original filename if not present
            path_obj = PurePosixPath(name)
            if not path_obj.suffix and Path(file.name).suffix:
                name = f"{name}{Path(file.name).suffix}"
        else:
            # Use original filename
            name = file.name

        # Sanitize path to prevent directory traversal
        name = sanitize_file_path(name)

        manager = FileManager(usage)

        # Check if file already exists
        if manager.file_exists(name):
            raise ValidationError({"name": [("A file with this name already exists.")]})

        # Save to backend
        # TODO: make this work
        with manager.save_file_stream(name) as f:
            f.write(file.read())

        Event.new(
            EventAction.FILE_UPLOADED,
            name=name,
            usage=usage.value,
            mime_type=get_mime_from_filename(name),
        ).from_http(request)

        return Response()

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
        try:
            backend.delete_file(file_path)
        except (ClientError, BotoCoreError) as e:
            self._handle_storage_error(e, "delete file")

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
