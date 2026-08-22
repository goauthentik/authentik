"""authentik core inlining template tags"""

import mimetypes
from base64 import b64encode
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


@register.filter(name="indent")
def indent_string(val, num_spaces=4):
    """Intent text by a given amount of spaces"""
    return val.replace("\n", "\n" + " " * num_spaces)
