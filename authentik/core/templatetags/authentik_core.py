"""authentik core tags"""

from django import template
from django.templatetags.static import static as static_loader

from authentik import get_full_version

register = template.Library()


@register.simple_tag()
def versioned_script(path: str) -> str:
    """Wrapper around {% static %} tag that supports setting the version"""
    return static_loader(path.replace("%v", get_full_version()))
