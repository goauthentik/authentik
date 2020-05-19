"""passbook lib navbar Templatetag"""
from django import template
from django.http import HttpRequest
from structlog import get_logger

register = template.Library()

LOGGER = get_logger()
ACTIVE_STRING = "pf-m-current"


@register.simple_tag(takes_context=True)
def is_active(context, *args: str, **_) -> str:
    """Return whether a navbar link is active or not."""
    request: HttpRequest = context.get("request")
    if not request.resolver_match:
        return ""
    match = request.resolver_match
    for url in args:
        if ":" in url:
            app_name, url = url.split(":")
            if match.app_name == app_name and match.url_name == url:
                return ACTIVE_STRING
        else:
            if match.url_name == url:
                return ACTIVE_STRING
    return ""


@register.simple_tag(takes_context=True)
def is_active_url(context, view: str) -> str:
    """Return whether a navbar link is active or not."""
    request: HttpRequest = context.get("request")
    if not request.resolver_match:
        return ""

    match = request.resolver_match
    current_full_url = f"{match.app_name}:{match.url_name}"

    if current_full_url == view:
        return ACTIVE_STRING
    return ""


@register.simple_tag(takes_context=True)
def is_active_app(context, *args: str) -> str:
    """Return True if current link is from app"""

    request: HttpRequest = context.get("request")
    if not request.resolver_match:
        return ""
    for app_name in args:
        if request.resolver_match.app_name == app_name:
            return ACTIVE_STRING
    return ""
