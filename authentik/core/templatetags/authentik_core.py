"""authentik core tags"""

from django import template
from django.templatetags.static import static as static_loader
from django.utils.safestring import mark_safe

from authentik import get_full_version

register = template.Library()


@register.simple_tag()
def versioned_script(path: str) -> str:
    """Wrapper around {% static %} tag that supports setting the version"""
    returned_lines = [
        (
            f'<script src="{static_loader(path.replace("%v", get_full_version()))}'
            '" type="module"></script>'
        ),
        # Legacy method of loading scripts used as a fallback, without the version in the filename
        # TODO: Remove after 2024.6 or later
        (
            f'<script src="{static_loader(path.replace("-%v", ""))}?'
            f'version={get_full_version()}" type="module"></script>'
        ),
    ]
    return mark_safe("".join(returned_lines))  # nosec
