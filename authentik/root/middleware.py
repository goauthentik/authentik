"""Dynamically set SameSite depending if the upstream connection is TLS or not"""

from collections.abc import Callable
from hashlib import sha512
from ipaddress import ip_address
from time import perf_counter, time
from typing import Any

from channels.exceptions import DenyConnection
from django.conf import settings
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware as UpstreamSessionMiddleware
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseServerError
from django.middleware.csrf import CSRF_SESSION_KEY
from django.middleware.csrf import CsrfViewMiddleware as UpstreamCsrfViewMiddleware
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date
from jwt import PyJWTError, decode, encode
from sentry_sdk import Scope
from structlog.stdlib import get_logger

from authentik.core.models import Token, TokenIntents, User, UserTypes

LOGGER = get_logger("authentik.asgi")
ACR_AUTHENTIK_SESSION = "goauthentik.io/core/default"
SIGNING_HASH = sha512(settings.SECRET_KEY.encode()).hexdigest()


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
            if user_agent.startswith("goauthentik.io/outpost/") or (
                "safari" in user_agent.lower() and "chrome" not in user_agent.lower()
            ):
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
            session_payload = decode(key, SIGNING_HASH, algorithms=["HS256"])
            session_key = session_payload["sid"]
        except (KeyError, PyJWTError):
            pass
        return session_key

    def process_request(self, request: HttpRequest):
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
                if response.status_code != HttpResponseServerError.status_code:
                    try:
                        request.session.save()
                    except UpdateError:
                        raise SessionInterrupted(
                            "The request's session was deleted before the "
                            "request completed. The user may have logged "
                            "out in a concurrent request, for example."
                        ) from None
                    payload = {
                        "sid": request.session.session_key,
                        "iss": "authentik",
                        "sub": "anonymous",
                        "authenticated": request.user.is_authenticated,
                        "acr": ACR_AUTHENTIK_SESSION,
                    }
                    if request.user.is_authenticated:
                        payload["sub"] = request.user.uid
                    value = encode(payload=payload, key=SIGNING_HASH)
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


class CsrfViewMiddleware(UpstreamCsrfViewMiddleware):
    """Dynamically set secure depending if the upstream connection is TLS or not"""

    def _set_csrf_cookie(self, request: HttpRequest, response: HttpResponse):
        if settings.CSRF_USE_SESSIONS:
            if request.session.get(CSRF_SESSION_KEY) != request.META["CSRF_COOKIE"]:
                request.session[CSRF_SESSION_KEY] = request.META["CSRF_COOKIE"]
        else:
            secure = SessionMiddleware.is_secure(request)
            response.set_cookie(
                settings.CSRF_COOKIE_NAME,
                request.META["CSRF_COOKIE"],
                max_age=settings.CSRF_COOKIE_AGE,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=secure,
                httponly=settings.CSRF_COOKIE_HTTPONLY,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
            # Set the Vary header since content varies with the CSRF cookie.
            patch_vary_headers(response, ("Cookie",))


class ClientIPMiddleware:
    """Set a "known-good" client IP on the request, by default based off of x-forwarded-for
    which is set by the go proxy, but also allowing the remote IP to be overridden by an outpost
    for protocols like LDAP"""

    get_response: Callable[[HttpRequest], HttpResponse]
    outpost_remote_ip_header = "HTTP_X_AUTHENTIK_REMOTE_IP"
    outpost_token_header = "HTTP_X_AUTHENTIK_OUTPOST_TOKEN"  # nosec
    default_ip = "255.255.255.255"

    request_attr_client_ip = "client_ip"
    request_attr_outpost_user = "outpost_user"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.logger = get_logger().bind()

    def _get_client_ip_from_meta(self, meta: dict[str, Any]) -> str:
        """Attempt to get the client's IP by checking common HTTP Headers.
        Returns none if no IP Could be found

        No additional validation is done here as requests are expected to only arrive here
        via the go proxy, which deals with validating these headers for us"""
        headers = (
            "HTTP_X_FORWARDED_FOR",
            "REMOTE_ADDR",
        )
        try:
            for _header in headers:
                if _header in meta:
                    ips: list[str] = meta.get(_header).split(",")
                    # Ensure the IP parses as a valid IP
                    return str(ip_address(ips[0].strip()))
            return self.default_ip
        except ValueError as exc:
            self.logger.debug("Invalid remote IP", exc=exc)
            return self.default_ip

    # FIXME: this should probably not be in `root` but rather in a middleware in `outposts`
    # but for now it's fine
    def _get_outpost_override_ip(self, request: HttpRequest) -> str | None:
        """Get the actual remote IP when set by an outpost. Only
        allowed when the request is authenticated, by an outpost internal service account"""
        if (
            self.outpost_remote_ip_header not in request.META
            or self.outpost_token_header not in request.META
        ):
            return None
        delegated_ip = request.META[self.outpost_remote_ip_header]
        token = (
            Token.filter_not_expired(
                key=request.META.get(self.outpost_token_header), intent=TokenIntents.INTENT_API
            )
            .select_related("user")
            .first()
        )
        if not token:
            LOGGER.warning("Attempted remote-ip override without token", delegated_ip=delegated_ip)
            return None
        user: User = token.user
        if user.type != UserTypes.INTERNAL_SERVICE_ACCOUNT:
            LOGGER.warning(
                "Remote-IP override: user doesn't have permission",
                user=user,
                delegated_ip=delegated_ip,
            )
            return None
        # Update sentry scope to include correct IP
        sentry_user = Scope.get_isolation_scope()._user or {}
        sentry_user["ip_address"] = delegated_ip
        Scope.get_isolation_scope().set_user(sentry_user)
        # Set the outpost service account on the request
        setattr(request, self.request_attr_outpost_user, user)
        try:
            return str(ip_address(delegated_ip))
        except ValueError as exc:
            self.logger.debug("Invalid remote IP from Outpost", exc=exc)
            return None

    def _get_client_ip(self, request: HttpRequest | None) -> str:
        """Attempt to get the client's IP by checking common HTTP Headers.
        Returns none if no IP Could be found"""
        if not request:
            return self.default_ip
        override = self._get_outpost_override_ip(request)
        if override:
            return override
        return self._get_client_ip_from_meta(request.META)

    @staticmethod
    def get_outpost_user(request: HttpRequest) -> User | None:
        """Get outpost user that authenticated this request"""
        return getattr(request, ClientIPMiddleware.request_attr_outpost_user, None)

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """Get correct client IP, including any overrides from outposts that
        have the permission to do so"""
        if request and not hasattr(request, ClientIPMiddleware.request_attr_client_ip):
            ClientIPMiddleware(lambda request: request).set_ip(request)
        return getattr(
            request, ClientIPMiddleware.request_attr_client_ip, ClientIPMiddleware.default_ip
        )

    def set_ip(self, request: HttpRequest):
        """Set the IP"""
        setattr(request, self.request_attr_client_ip, self._get_client_ip(request))

    def __call__(self, request: HttpRequest) -> HttpResponse:
        self.set_ip(request)
        return self.get_response(request)


class ChannelsLoggingMiddleware:
    """Logging middleware for channels"""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        self.log(scope)
        try:
            return await self.inner(scope, receive, send)
        except DenyConnection:
            return await send({"type": "websocket.close"})
        except Exception as exc:
            if settings.DEBUG:
                raise exc
            LOGGER.warning("Exception in ASGI application", exc=exc)
            return await send({"type": "websocket.close"})

    def log(self, scope: dict, **kwargs):
        """Log request"""
        headers = dict(scope.get("headers", {}))
        LOGGER.info(
            scope["path"],
            scheme="ws",
            remote=headers.get(b"x-forwarded-for", b"").decode(),
            user_agent=headers.get(b"user-agent", b"").decode(),
            **kwargs,
        )


class LoggingMiddleware:
    """Logger middleware"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = perf_counter()
        response = self.get_response(request)
        status_code = response.status_code
        kwargs = {
            "request_id": getattr(request, "request_id", None),
        }
        kwargs.update(getattr(response, "ak_context", {}))
        self.log(request, status_code, int((perf_counter() - start) * 1000), **kwargs)
        return response

    def log(self, request: HttpRequest, status_code: int, runtime: int, **kwargs):
        """Log request"""
        LOGGER.info(
            request.get_full_path(),
            remote=ClientIPMiddleware.get_client_ip(request),
            method=request.method,
            scheme=request.scheme,
            status=status_code,
            runtime=runtime,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            **kwargs,
        )
