"""URL-related utils"""

from typing import Any
from urllib.parse import urlparse

from django.http import HttpResponse, QueryDict
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from structlog.stdlib import get_logger

LOGGER = get_logger()


def is_url_absolute(url: str | bytes | bytearray | None) -> bool:
    """Check if domain is absolute to prevent user from being redirect somewhere else"""
    return bool(urlparse(url).netloc)


def redirect_with_qs(view: str, qs: QueryDict | None = None, **kwargs: Any) -> HttpResponse:
    """Wrapper to redirect whilst keeping GET Parameters"""
    try:
        target = reverse(view, kwargs=kwargs)
    except NoReverseMatch:
        if not is_url_absolute(view):
            return redirect(view)
        LOGGER.warning("redirect target is not a valid view", view=view)
        raise
    if qs:
        target += "?" + qs.urlencode()
    return redirect(target)


def reverse_with_qs(view: str, qs: QueryDict | None = None, **kwargs: Any) -> str:
    """Reverse a view to it's url but include get params"""
    url = reverse(view, **kwargs)
    if qs:
        url += "?" + qs.urlencode()
    return url
