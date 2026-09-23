from typing import Any

from django.conf import settings
from msgspec import DecodeError
from msgspec.json import Decoder
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser

_DECODER = Decoder()


class MsgspecJSONParser(BaseParser):
    media_type = "application/json"

    def parse(self, stream, media_type=None, parser_context: dict[str, Any] | None = None):
        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return _DECODER.decode(data)
        except DecodeError as exc:
            raise ParseError(f"JSON parse error - {exc}") from exc
