"""passbook core inlining template tags"""
import os
from pathlib import Path
from typing import Optional

from django import template
from django.contrib.staticfiles import finders

register = template.Library()


@register.simple_tag()
def inline_static_ascii(path: str) -> Optional[str]:
    """Inline static asset. Doesn't check file contents, plain text is assumed"""
    result = finders.find(path)
    if os.path.exists(result):
        with open(result) as _file:
            return _file.read()
    return None


@register.simple_tag()
def inline_static_binary(path: str) -> Optional[str]:
    """Inline static asset. Uses file extension for base64 block"""
    result = finders.find(path)
    suffix = Path(path).suffix
    if os.path.exists(result):
        with open(result) as _file:
            return f"data:image/{suffix};base64," + _file.read()
    return None
