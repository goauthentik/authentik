import mimetypes

from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, ChoiceField, FileField
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

    class FileListParameters(PassiveSerializer):
        usage = ChoiceField(choices=list(FileApiUsage), default=FileApiUsage.MEDIA.value)
        search = CharField(required=False)
        manageable_only = BooleanField(required=False, default=False)

    class FileListSerializer(PassiveSerializer):
        name = CharField()
        mime_type = CharField()
        url = CharField()

    @extend_schema(
        parameters=[FileListParameters],
        responses={200: FileListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        """List files from storage backend."""
        params = FileView.FileListParameters(data=request.query_params)
        params.is_valid(raise_exception=True)
        params = params.validated_data

        try:
            usage = FileApiUsage(params.get("usage", FileApiUsage.MEDIA.value))
        except ValueError as exc:
            raise ValidationError(
                f"Invalid usage parameter provided: {params.get('usage')}"
            ) from exc

        # Backend is source of truth - list all files from storage
        manager = FileManager(usage)
        files = manager.list_files(manageable_only=params.get("manageable_only", False))
        search_query = params.get("search", "")
        if search_query:
            files = filter(lambda file: search_query in file.lower(), files)
        files = [
            FileView.FileListSerializer(
                {
                    "name": file,
                    "url": manager.file_url(file),
                    "mime_type": get_mime_from_filename(file),
                }
            )
            for file in files
        ]
        for file in files:
            file.is_valid()

        return Response([file.data for file in files])

    class FileUploadSerializer(PassiveSerializer):
        file = FileField(required=True)
        name = CharField(required=False, allow_blank=True)
        usage = CharField(required=False, default=FileApiUsage.MEDIA.value)

    @extend_schema(
        request=FileUploadSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        """Upload file to storage backend."""
        serializer = FileView.FileUploadSerializer(data=request.data)
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
        with manager.save_file_stream(name) as f:
            f.write(file.read())

        Event.new(
            EventAction.FILE_UPLOADED,
            name=name,
            usage=usage.value,
            mime_type=get_mime_from_filename(name),
        ).from_http(request)

        return Response()

    class FileDeleteParameters(PassiveSerializer):
        name = CharField()
        usage = ChoiceField(choices=list(FileApiUsage), default=FileApiUsage.MEDIA.value)

    @extend_schema(
        parameters=[FileDeleteParameters],
        responses={200: None},
    )
    def delete(self, request: Request) -> Response:
        """Delete file from storage backend."""
        params = FileView.FileDeleteParameters(data=request.query_params)
        params.is_valid(raise_exception=True)
        params = params.validated_data
        # name = request.query_params.get("name", "")
        # usage_param = request.query_params.get("usage", FileApiUsage.MEDIA.value)

        validate_upload_file_name(params.get("name", ""), ValidationError)

        try:
            usage = FileApiUsage(params.get("usage", FileApiUsage.MEDIA.value))
        except ValueError as exc:
            raise ValidationError(
                f"Invalid usage parameter provided: {params.get('usage')}"
            ) from exc

        manager = FileManager(usage)

        # Delete from backend
        manager.delete_file(params.get("name"))

        # Audit log for file deletion
        Event.new(
            EventAction.FILE_DELETED,
            name=params.get("name"),
            usage=usage.value,
        ).from_http(request)

        return Response()
