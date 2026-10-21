"""URL-related utils"""

from urllib.parse import urlparse

from django.http import HttpResponse, QueryDict
from django.shortcuts import redirect
from django.urls import NoReverseMatch, URLPattern, URLResolver, reverse
from django.urls.resolvers import RoutePattern
from structlog.stdlib import get_logger

LOGGER = get_logger()


class hot_path(URLPattern):  # noqa: N801
    """Drop-in for `path()` for frequently requested views, sorted before other patterns
    by `sort_hot` so they resolve without walking every other pattern first."""

    def __init__(self, route: str, view, kwargs: dict | None = None, name: str | None = None):
        super().__init__(RoutePattern(route, name=name, is_endpoint=True), view, kwargs, name)


def is_hot(pattern: URLPattern | URLResolver) -> bool:
    """Check if a pattern is a `hot_path` or an `include()` containing one"""
    if isinstance(pattern, URLResolver):
        return any(is_hot(sub_pattern) for sub_pattern in pattern.url_patterns)
    return isinstance(pattern, hot_path)


def sort_hot(patterns: list) -> list:
    """Move `hot_path` patterns (and includes containing them) to the front,
    keeping relative order otherwise"""
    return sorted(patterns, key=lambda pattern: not is_hot(pattern))


def is_url_absolute(url):
    """Check if domain is absolute to prevent user from being redirect somewhere else"""
    return bool(urlparse(url).netloc)


def redirect_with_qs(view: str, get_query_set: QueryDict | None = None, **kwargs) -> HttpResponse:
    """Wrapper to redirect whilst keeping GET Parameters"""
    try:
        target = reverse(view, kwargs=kwargs)
    except NoReverseMatch:
        if not is_url_absolute(view):
            return redirect(view)
        LOGGER.warning("redirect target is not a valid view", view=view)
        raise
    if get_query_set:
        target += "?" + get_query_set.urlencode()
    return redirect(target)


def reverse_with_qs(view: str, query: QueryDict | None = None, **kwargs) -> str:
    """Reverse a view to it's url but include get params"""
    url = reverse(view, **kwargs)
    if query:
        url += "?" + query.urlencode()
    return url
