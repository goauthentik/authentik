"""authentik core tags"""

from django import template
from django.templatetags.static import static as static_loader

from authentik import __version__

register = template.Library()


@register.simple_tag()
def static(path: str) -> str:
    """Wrapper around {% static %} tag that supports setting the version"""
    return static_loader(path.replace("%v", __version__))
