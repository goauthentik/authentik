"""Dynamically set SameSite depending if the upstream connection is TLS or not"""
from functools import lru_cache
from hashlib import sha512
from time import time
from timeit import default_timer
from typing import Callable

from django.conf import settings
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware as UpstreamSessionMiddleware
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date
from jwt import PyJWTError, decode, encode
from structlog.stdlib import get_logger

from authentik.lib.utils.http import get_client_ip
from authentik.root.install_id import get_install_id

LOGGER = get_logger("authentik.asgi")
ACR_AUTHENTIK_SESSION = "goauthentik.io/core/default"


@lru_cache
def get_signing_hash():
    """Get cookie JWT signing hash"""
    return sha512(get_install_id().encode()).hexdigest()


class SessionMiddleware(UpstreamSessionMiddleware):
    """Dynamically set SameSite depending if the upstream connection is TLS or not"""

    @staticmethod
    def is_secure(request: HttpRequest) -> bool:
        """Check if request is TLS'd or localhost"""
        if request.is_secure():
            return True
        host, _, _ = request.get_host().partition(":")
        if host == "localhost" and settings.DEBUG:
            # Since go does not consider localhost with http a secure origin
            # we can't set the secure flag.
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            if user_agent.startswith("goauthentik.io/outpost/") or "safari" in user_agent.lower():
                return False
            return True
        return False

    @staticmethod
    def decode_session_key(key: str) -> str:
        """Decode raw session cookie, and parse JWT"""
        # We need to support the standard django format of just a session key
        # for testing setups, where the session is directly set
        session_key = key if settings.TEST else None
        try:
            session_payload = decode(key, get_signing_hash(), algorithms=["HS256"])
            session_key = session_payload["sid"]
        except (KeyError, PyJWTError):
            pass
        return session_key

    def process_request(self, request):
        raw_session = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        session_key = SessionMiddleware.decode_session_key(raw_session)
        request.session = self.SessionStore(session_key)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response
        # Set SameSite based on whether or not the request is secure
        secure = SessionMiddleware.is_secure(request)
        same_site = "None" if secure else "Lax"
        # First check if we need to delete this cookie.
        # The session should be deleted only if the session is entirely empty.
        if settings.SESSION_COOKIE_NAME in request.COOKIES and empty:
            response.delete_cookie(
                settings.SESSION_COOKIE_NAME,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=same_site,
            )
            patch_vary_headers(response, ("Cookie",))
        else:
            if accessed:
                patch_vary_headers(response, ("Cookie",))
            if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time() + max_age
                    expires = http_date(expires_time)
                # Save the session data and refresh the client cookie.
                # Skip session save for 500 responses, refs #3881.
                if response.status_code != 500:
                    try:
                        request.session.save()
                    except UpdateError:
                        raise SessionInterrupted(
                            "The request's session was deleted before the "
                            "request completed. The user may have logged "
                            "out in a concurrent request, for example."
                        )
                    payload = {
                        "sid": request.session.session_key,
                        "iss": "authentik",
                        "sub": "anonymous",
                        "authenticated": request.user.is_authenticated,
                        "acr": ACR_AUTHENTIK_SESSION,
                    }
                    if request.user.is_authenticated:
                        payload["sub"] = request.user.uid
                    value = encode(payload=payload, key=get_signing_hash())
                    if settings.TEST:
                        value = request.session.session_key
                    response.set_cookie(
                        settings.SESSION_COOKIE_NAME,
                        value,
                        max_age=max_age,
                        expires=expires,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=secure,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=same_site,
                    )
        return response


class ChannelsLoggingMiddleware:
    """Logging middleware for channels"""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        self.log(scope)
        return await self.inner(scope, receive, send)

    def log(self, scope: dict, **kwargs):
        """Log request"""
        headers = dict(scope.get("headers", {}))
        LOGGER.info(
            scope["path"],
            scheme="ws",
            remote=scope.get("client", [""])[0],
            user_agent=headers.get(b"user-agent", b"").decode(),
            **kwargs,
        )


class LoggingMiddleware:
    """Logger middleware"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = default_timer()
        response = self.get_response(request)
        status_code = response.status_code
        kwargs = {
            "request_id": request.request_id,
        }
        kwargs.update(getattr(response, "ak_context", {}))
        self.log(request, status_code, int((default_timer() - start) * 1000), **kwargs)
        return response

    def log(self, request: HttpRequest, status_code: int, runtime: int, **kwargs):
        """Log request"""
        LOGGER.info(
            request.get_full_path(),
            remote=get_client_ip(request),
            method=request.method,
            scheme=request.scheme,
            status=status_code,
            runtime=runtime,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            **kwargs,
        )
