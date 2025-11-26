import mimetypes

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.admin.files.manager import FileManager
from authentik.admin.files.usage import FileApiUsage
from authentik.admin.files.validation import validate_upload_file_name
from authentik.core.api.utils import PassiveSerializer
from authentik.events.models import Event, EventAction
from authentik.rbac.permissions import HasPermission

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB


def get_mime_from_filename(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


class FileUploadSerializer(PassiveSerializer):
    file = serializers.FileField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    usage = serializers.CharField(required=False, default=FileApiUsage.MEDIA.value)


class FileView(APIView):
    pagination_class = None
    parser_classes = [MultiPartParser]

    def get_permissions(self):
        return [
            HasPermission(
                "authentik_rbac.view_files"
                if self.request.method in SAFE_METHODS
                else "authentik_rbac.manage_files"
            )()
        ]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="usage",
                type=str,
                enum=list(FileApiUsage),
                default=FileApiUsage.MEDIA.value,
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
                    "url": CharField(required=True),
                },
                many=True,
            )
        },
    )
    def get(self, request: Request) -> Response:
        """List files from storage backend."""
        usage_param = request.query_params.get("usage", FileApiUsage.MEDIA.value)
        search_query = request.query_params.get("search", "").strip().lower()
        manageable_only = request.query_params.get("manageableOnly", "false").lower() == "true"

        try:
            usage = FileApiUsage(usage_param)
        except ValueError as exc:
            raise ValidationError(f"Invalid usage parameter provided: {usage_param}") from exc

        # Backend is source of truth - list all files from storage
        manager = FileManager(usage)
        files = manager.list_files(manageable_only=manageable_only)
        if search_query:
            files = filter(lambda file: search_query in file.lower(), files)
        files = [
            {
                "name": file,
                "url": manager.file_url(file),
                "mime_type": get_mime_from_filename(file),
            }
            for file in files
        ]

        return Response(files)

    @extend_schema(
        request=FileUploadSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        """Upload file to storage backend."""
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]
        name = serializer.validated_data.get("name", "").strip()
        usage_value = serializer.validated_data.get("usage", FileApiUsage.MEDIA.value)

        # Validate file size and type
        if file.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                {
                    "file": [
                        _(
                            f"File size ({file.size}B) exceeds maximum allowed "
                            f"size ({MAX_FILE_SIZE_BYTES}B)."
                        )
                    ]
                }
            )

        try:
            usage = FileApiUsage(usage_value)
        except ValueError as exc:
            raise ValidationError(f"Invalid usage parameter provided: {usage_value}") from exc

        # Use original filename
        if not name:
            name = file.name

        # Sanitize path to prevent directory traversal
        validate_upload_file_name(name, ValidationError)

        manager = FileManager(usage)

        # Check if file already exists
        if manager.file_exists(name):
            raise ValidationError({"name": ["A file with this name already exists."]})

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
                description="File to delete",
            ),
            OpenApiParameter(
                name="usage",
                type=str,
                enum=list(FileApiUsage),
                default=FileApiUsage.MEDIA.value,
                description="Usage type",
            ),
        ],
        responses={200: None},
    )
    def delete(self, request: Request) -> Response:
        """Delete file from storage backend."""
        name = request.query_params.get("name", "")
        usage_param = request.query_params.get("usage", FileApiUsage.MEDIA.value)

        validate_upload_file_name(name, ValidationError)

        try:
            usage = FileApiUsage(usage_param)
        except ValueError as exc:
            raise ValidationError(f"Invalid usage parameter provided: {usage_param}") from exc

        manager = FileManager(usage)

        # Delete from backend
        manager.delete_file(name)

        # Audit log for file deletion
        Event.new(
            EventAction.FILE_DELETED,
            name=name,
            usage=usage.value,
        ).from_http(request)

        return Response()
