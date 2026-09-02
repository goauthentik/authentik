"""Helpers for responses which shared caches may serve to anonymous clients."""

from django.http import HttpResponse
from django.utils.cache import patch_cache_control, patch_vary_headers

ANONYMOUS_SHARED_CACHE_SECONDS = 60


def patch_anonymous_shared_cache(
    response: HttpResponse,
    *vary: str,
    seconds: int = ANONYMOUS_SHARED_CACHE_SECONDS,
) -> None:
    """Allow shared caching without letting browsers reuse anonymous responses."""
    patch_cache_control(response, public=True, s_maxage=seconds, max_age=0)
    # The origin cannot enforce a cache bypass for authenticated requests. Cookie must
    # remain part of the cache key so an anonymous response is never served to one.
    patch_vary_headers(response, ("Cookie", *vary))
