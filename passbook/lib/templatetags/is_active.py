"""passbook lib navbar Templatetag"""
from django import template
from django.urls import reverse
from structlog import get_logger

register = template.Library()

LOGGER = get_logger()


@register.simple_tag(takes_context=True)
def is_active(context, *args, **kwargs):
    """Return whether a navbar link is active or not."""
    request = context.get('request')
    app_name = kwargs.get('app_name', None)
    if not request.resolver_match:
        return ''
    for url in args:
        short_url = url.split(':')[1] if ':' in url else url
        # Check if resolve_match matches
        if request.resolver_match.url_name.startswith(url) or \
                request.resolver_match.url_name.startswith(short_url):
            # Monkeypatch app_name: urls from core have app_name == ''
            # since the root urlpatterns have no namespace
            if app_name and request.resolver_match.app_name == app_name:
                return 'active'
            if app_name is None:
                return 'active'
    return ''


@register.simple_tag(takes_context=True)
def is_active_url(context, view, *args, **kwargs):
    """Return whether a navbar link is active or not."""

    matching_url = reverse(view, args=args, kwargs=kwargs)
    request = context.get('request')
    if not request.resolver_match:
        return ''
    if matching_url == request.path:
        return 'active'
    return ''


@register.simple_tag(takes_context=True)
def is_active_app(context, *args):
    """Return True if current link is from app"""

    request = context.get('request')
    if not request.resolver_match:
        return ''
    for app_name in args:
        if request.resolver_match.app_name == app_name:
            return 'active'
    return ''
