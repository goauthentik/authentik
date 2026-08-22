"""authentik core inlining template tags"""

import mimetypes
from base64 import b64encode
from enum import Enum
from pathlib import Path

from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@register.simple_tag()
def inline_static_ascii(path: str) -> str:
    """Inline static asset. Doesn't check file contents, plain text is assumed.
    If no file could be found, original path is returned"""
    result = finders.find(path)

    if result is None:
        return path

    result = Path(result)

    if result:
        with open(result, encoding="utf8") as _file:
            return _file.read()
    return path


@register.simple_tag()
def inline_static_binary(path: str) -> str:
    """Inline static asset. Uses file extension for base64 block. If no file could be found,
    path is returned."""
    result = finders.find(path)

    if result is None:
        return path

    result = Path(result)

    if result.is_file():
        type, _ = mimetypes.guess_file_type(result)

        if type is None:
            type = "application/octet-stream"

        with open(result, "rb") as _file:
            b64content = b64encode(_file.read())
            return f"data:{type};base64,{b64content.decode('utf-8')}"

    return path


class AttachmentType(Enum):
    IMAGE = "image"


@register.simple_tag(takes_context=True)
def attach_image(context, path: str) -> str:
    """Attach a static image as an RFC 2392 resource."""
    if path in context["attachments"]:
        return context["attachments"][path]["content_id"]

    id_count = context.get("content_id_counter", 0)
    context.set_upward("content_id_counter", id_count + 1)
    content_id = f"attach_{id_count}@{context.get('domain')}"
    context["attachments"][path] = {"content_id": content_id, "type": AttachmentType.IMAGE}

    return f"cid:{content_id}"


@register.filter(name="indent")
def indent_string(val, num_spaces=4):
    """Intent text by a given amount of spaces"""
    return val.replace("\n", "\n" + " " * num_spaces)
