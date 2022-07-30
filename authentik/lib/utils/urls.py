"""URL-related utils"""
from typing import Optional
from urllib.parse import urlparse

from django.http import HttpResponse, QueryDict
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils.http import urlencode
from structlog.stdlib import get_logger

LOGGER = get_logger()


def is_url_absolute(url):
    """Check if domain is absolute to prevent user from being redirect somewhere else"""
    return bool(urlparse(url).netloc)


def redirect_with_qs(
    view: str, get_query_set: Optional[QueryDict] = None, **kwargs
) -> HttpResponse:
    """Wrapper to redirect whilst keeping GET Parameters"""
    try:
        target = reverse(view, kwargs=kwargs)
    except NoReverseMatch:
        if not is_url_absolute(view):
            return redirect(view)
        LOGGER.warning("redirect target is not a valid view", view=view)
        raise
    else:
        if get_query_set:
            target += "?" + urlencode(get_query_set.items())
        return redirect(target)


def reverse_with_qs(view: str, query: Optional[QueryDict] = None, **kwargs) -> str:
    """Reverse a view to it's url but include get params"""
    url = reverse(view, **kwargs)
    if query:
        url += "?" + urlencode(query.items())
    return url
