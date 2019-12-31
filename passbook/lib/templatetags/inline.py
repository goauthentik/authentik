"""passbook core inlining template tags"""
import os

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag()
def inline_static(path):
    """Inline static asset. If file is binary, return b64 representation"""
    prefix = "data:image/svg+xml;utf8,"
    data = ""
    full_path = settings.STATIC_ROOT + "/" + path
    if os.path.exists(full_path):
        if full_path.endswith(".svg"):
            with open(full_path) as _file:
                data = _file.read()
    return prefix + data
