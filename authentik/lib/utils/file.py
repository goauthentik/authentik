"""file utils"""

import os

from django.core.exceptions import SuspiciousOperation
from django.db.models import Model
from django.http import HttpResponseBadRequest
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


class FilePathSerializer(PassiveSerializer):
    """Serializer to upload file"""

    url = CharField()


def set_file(request: Request, obj: Model, field_name: str):
    """Upload file"""
    field = getattr(obj, field_name)
    file = request.FILES.get("file", None)
    clear = request.data.get("clear", "false").lower() == "true"

    # If clearing or replacing, delete the old file first
    if (clear or file) and field:
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

    if clear:
        # Save model after clearing
        obj.save()
        return Response({})

    if file:
        # Get the upload_to path from the model field
        upload_to = field.field.upload_to
        # If upload_to is set, ensure the file name includes the directory
        if upload_to:
            # Use basename to strip any path components from the filename
            base_name = os.path.basename(file.name)
            # Construct a clean path within the upload directory
            file.name = f"{upload_to}/{base_name}"
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
        return Response({})
    return Response({"error": "No file provided"}, status=400)


def set_file_url(request: Request, obj: Model, field: str):
    """Set file field to URL"""
    field = getattr(obj, field)
    url = request.data.get("url", None)
    if url is None:
        return HttpResponseBadRequest()
    field.name = url
    obj.save()
    return Response({})
