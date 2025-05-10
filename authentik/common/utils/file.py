"""file utils"""

from django.db.models import Model
from django.http import HttpResponseBadRequest
from rest_framework.fields import BooleanField, CharField, FileField
from rest_framework.request import Request
from rest_framework.response import Response
from structlog import get_logger

from authentik.core.api.utils import PassiveSerializer

LOGGER = get_logger()


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
    if clear:
        # .delete() saves the model by default
        field.delete()
        return Response({})
    if file:
        setattr(obj, field_name, file)
        try:
            obj.save()
        except PermissionError as exc:
            LOGGER.warning("Failed to save file", exc=exc)
            return HttpResponseBadRequest()
        return Response({})
    return HttpResponseBadRequest()


def set_file_url(request: Request, obj: Model, field: str):
    """Set file field to URL"""
    field = getattr(obj, field)
    url = request.data.get("url", None)
    if url is None:
        return HttpResponseBadRequest()
    field.name = url
    obj.save()
    return Response({})
