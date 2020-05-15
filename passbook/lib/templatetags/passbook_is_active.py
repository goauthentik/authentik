"""passbook lib navbar Templatetag"""
from django import template
from structlog import get_logger

register = template.Library()

LOGGER = get_logger()
ACTIVE_STRING = "pf-m-current"


@register.simple_tag(takes_context=True)
def is_active(context, *args, **kwargs):
    """Return whether a navbar link is active or not."""
    request = context.get("request")
    app_name = kwargs.get("app_name", None)
    if not request.resolver_match:
        return ""
    for url in args:
        short_url = url.split(":")[1] if ":" in url else url
        # Check if resolver_match matches
        if request.resolver_match.url_name.startswith(
            url
        ) or request.resolver_match.url_name.startswith(short_url):
            # Monkeypatch app_name: urls from core have app_name == ''
            # since the root urlpatterns have no namespace
            if app_name and request.resolver_match.app_name == app_name:
                return ACTIVE_STRING
            if app_name is None:
                return ACTIVE_STRING
    return ""


@register.simple_tag(takes_context=True)
def is_active_url(context, view):
    """Return whether a navbar link is active or not."""
    request = context.get("request")
    current_full_url = (
        f"{request.resolver_match.app_name}:{request.resolver_match.url_name}"
    )

    if not request.resolver_match:
        return ""
    if current_full_url == view:
        return ACTIVE_STRING
    return ""


@register.simple_tag(takes_context=True)
def is_active_app(context, *args):
    """Return True if current link is from app"""

    request = context.get("request")
    if not request.resolver_match:
        return ""
    for app_name in args:
        if request.resolver_match.app_name == app_name:
            return ACTIVE_STRING
    return ""
