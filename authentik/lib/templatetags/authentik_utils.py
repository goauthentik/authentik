"""authentik lib Templatetags"""

from django import template
from django.db.models import Model
from structlog.stdlib import get_logger

register = template.Library()
LOGGER = get_logger()


@register.filter("fieldtype")
def fieldtype(field):
    """Return classname"""
    if isinstance(field.__class__, Model) or issubclass(field.__class__, Model):
        return verbose_name(field)
    return field.__class__.__name__


@register.filter(name="css_class")
def css_class(field, css):
    """Add css class to form field"""
    return field.as_widget(attrs={"class": css})


@register.filter
def verbose_name(obj) -> str:
    """Return Object's Verbose Name"""
    if not obj:
        return ""
    if hasattr(obj, "verbose_name"):
        return obj.verbose_name
    return obj._meta.verbose_name


@register.filter
def form_verbose_name(obj) -> str:
    """Return ModelForm's Object's Verbose Name"""
    if not obj:
        return ""
    return verbose_name(obj._meta.model)
