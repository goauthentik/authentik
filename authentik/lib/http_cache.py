"""Shared HTTP-cache TTLs and directive helpers for anonymous-redirect responses.

Used by ``authentik/core/views/interface.py`` and
``authentik/flows/views/{executor,interface}.py`` to mark anonymous-visitor
redirects as cacheable at shared edge caches (CDN / reverse proxy).
"""

# How long shared HTTP caches may serve the anonymous ``GET /`` -> login flow
# redirect and the ``/flows/-/default/<designation>/`` redirect. Both responses
# are deterministic per host for anonymous users — depend only on the brand's
# configured default authentication flow — so edge caching absorbs flood
# traffic before it reaches PostgreSQL.
ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS = 60


def anonymous_redirect_cache_control(
    seconds: int = ANONYMOUS_ROOT_REDIRECT_CACHE_SECONDS,
) -> str:
    """``Cache-Control`` value for anonymous-redirect endpoints.

    Returns ``"public, s-maxage=N, max-age=0"``:

    - ``public`` + ``s-maxage=N`` lets shared caches (CDN, reverse proxy)
      serve the response for N seconds. Per RFC 7234 §5.2.2.9, ``s-maxage``
      overrides ``max-age`` for shared caches.
    - ``max-age=0`` makes browsers treat the response as immediately stale,
      so they don't serve it back to their own user.

    The ``max-age=0`` is critical: without it, a user who completes login
    within the cache window would have their browser serve the stale
    anonymous redirect on the post-login navigation to ``/``, bouncing them
    back into the auth flow they just finished. Edge caching still absorbs
    flood traffic; browsers just stop participating in the cache.
    """
    return f"public, s-maxage={seconds}, max-age=0"
