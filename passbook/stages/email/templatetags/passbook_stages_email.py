"""passbook core inlining template tags"""
from pathlib import Path

from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@register.simple_tag()
def inline_static_ascii(path: str) -> str:
    """Inline static asset. Doesn't check file contents, plain text is assumed"""
    result = finders.find(path)
    with open(result) as _file:
        return _file.read()


@register.simple_tag()
def inline_static_binary(path: str) -> str:
    """Inline static asset. Uses file extension for base64 block"""
    result = finders.find(path)
    suffix = Path(path).suffix
    with open(result) as _file:
        return f"data:image/{suffix};base64," + _file.read()
