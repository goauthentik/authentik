from typing import Any
from uuid import UUID

from django.db.models.enums import ChoicesType
from django.utils.functional import Promise
from msgspec.json import Encoder
from rest_framework.renderers import BaseRenderer
from rest_framework.settings import api_settings


def enc_hook(obj: Any) -> Any:
    if isinstance(obj, dict):
        return dict(obj)
    if isinstance(obj, list):
        return list(obj)
    if isinstance(obj, (str, UUID, Promise, ChoicesType)):
        return str(obj)
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if hasattr(obj, "__iter__"):
        return list(item for item in obj)
    return None


_ENCODER = Encoder(
    enc_hook=enc_hook,
    decimal_format="string" if api_settings.COERCE_DECIMAL_TO_STRING else "number",
)


class MsgspecJSONRenderer(BaseRenderer):
    media_type = "application/json"
    format = "json"

    def render(self, data: Any, accepted_media_type=None, renderer_context=None) -> bytes:
        if data is None:
            return b""

        return _ENCODER.encode(data)
