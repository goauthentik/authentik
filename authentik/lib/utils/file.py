"""file utils"""

import os
import uuid

from django.core.exceptions import SuspiciousOperation
from django.db.models import Model
from rest_framework.fields import BooleanField, CharField, FileField
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from authentik.core.api.utils import PassiveSerializer

LOGGER = get_logger()


class FileValidationError(SuspiciousOperation):
    """Custom exception for file validation errors."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.user_message = message


class FileUploadSerializer(PassiveSerializer):
    """Serializer to upload file"""

    file = FileField(required=False)
    clear = BooleanField(default=False)
    action = CharField(required=False, default="update")


class FilePathSerializer(PassiveSerializer):
    """Serializer to upload file"""

    url = CharField()
    action = CharField(required=False, default="update")


def set_file(request: Request, obj: Model, field_name: str):
    """Upload file"""
    # Use serializer for validation
    serializer = FileUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    field = getattr(obj, field_name)
    file = request.FILES.get("file", None)
    action = serializer.validated_data.get("action", "update")

    # Clear action - delete the file and return empty meta_icon
    if action == "clear" and field:
        try:
            LOGGER.debug(
                "Clearing file based on action=clear",
                field_name=field_name,
                old_file=field.name if field else None,
            )
            field.delete(save=False)
            obj.save()
            return Response({"meta_icon": None})
        except Exception as exc:
            LOGGER.warning("Failed to clear file", exc=exc)
            return Response({"error": f"Failed to clear file: {str(exc)}"}, status=500)

    # Update action - check for file upload
    if action == "update":
        # If replacing, delete the old file first
        if file and field:
            try:
                LOGGER.debug(
                    "Deleting old file before setting new one",
                    field_name=field_name,
                    old_file=field.name if field else None,
                )
                # Delete old file but don't save model yet
                field.delete(save=False)
            except Exception as exc:
                LOGGER.warning("Failed to delete old file", exc=exc)

        # For backward compatibility
        if serializer.validated_data.get("clear", False) and field:
            try:
                field.delete(save=False)
                obj.save()
                return Response({"meta_icon": None})
            except Exception as exc:
                LOGGER.warning("Failed to clear file using legacy method", exc=exc)

        if file:
            # Get the upload_to path from the model field
            upload_to = field.field.upload_to

            # If upload_to is set, ensure the file name includes the directory
            if upload_to:
                # Generate a unique filename to prevent conflicts
                filename, extension = os.path.splitext(os.path.basename(file.name))
                unique_filename = f"{filename}_{uuid.uuid4().hex[:8]}{extension}"
                # Construct a clean path within the upload directory
                file.name = f"{upload_to}/{unique_filename}"

            setattr(obj, field_name, file)
            try:
                obj.save()
            except FileValidationError as exc:
                LOGGER.warning(
                    "File validation failed",
                    error=exc.user_message,
                    status_code=exc.status_code,
                    field=field_name,
                )
                return Response({"error": exc.user_message}, status=exc.status_code)
            except PermissionError as exc:
                LOGGER.warning("Failed to save file", exc=exc)
                return Response({"error": "Permission denied saving file"}, status=403)
            except Exception as exc:
                LOGGER.error("Unexpected error saving file", exc=exc)
                return Response(
                    {"error": "An unexpected error occurred while saving the file"}, status=500
                )
            return Response(
                {
                    "meta_icon": (
                        getattr(obj, field_name).url
                        if hasattr(getattr(obj, field_name), "url")
                        else None
                    )
                }
            )
        return Response({"error": "No file provided for update action"}, status=400)

    # Invalid action
    return Response(
        {"error": f"Invalid action: {action}. Must be 'update' or 'clear'."}, status=400
    )


def set_file_url(request: Request, obj: Model, field: str):
    """Set file field to URL"""
    # Use serializer for validation
    serializer = FilePathSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    field_obj = getattr(obj, field)
    url = serializer.validated_data.get("url")
    action = serializer.validated_data.get("action", "update")

    # Clear action
    if action == "clear" and field_obj and field_obj.name:
        try:
            field_obj.delete(save=False)
            obj.save()
            return Response({"meta_icon": None})
        except Exception as exc:
            LOGGER.warning("Failed to clear file", exc=exc)
            return Response({"error": f"Failed to clear file: {str(exc)}"}, status=500)

    # Update action
    if action == "update":
        if url is None:
            return Response({"error": "URL is required for update action"}, status=400)

        # Delete old file if it exists
        if field_obj and field_obj.name:
            try:
                field_obj.delete(save=False)
            except Exception as exc:
                LOGGER.warning("Failed to delete old file", exc=exc)

        field_obj.name = url
        obj.save()
        return Response({"meta_icon": url})

    # Invalid action
    return Response(
        {"error": f"Invalid action: {action}. Must be 'update' or 'clear'."}, status=400
    )
