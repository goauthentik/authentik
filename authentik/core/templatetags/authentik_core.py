"""authentik core tags"""

from django import template
from django.templatetags.static import static as static_loader
from django.utils.safestring import mark_safe

from authentik import authentik_full_version

register = template.Library()


@register.simple_tag()
def versioned_script(path: str) -> str:
    """Wrapper around {% static %} tag that appends a version query parameter to the URL"""

    return static_loader(path) + "?v=" + authentik_full_version()
