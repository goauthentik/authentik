"""
ASGI config for authentik project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""
import typing
from time import time

import django
from asgiref.compatibility import guarantee_single_callable
from channels.routing import ProtocolTypeRouter, URLRouter
from defusedxml import defuse_stdlib
from django.core.asgi import get_asgi_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from structlog.stdlib import get_logger

from authentik.core.middleware import RESPONSE_HEADER_ID

# DJANGO_SETTINGS_MODULE is set in gunicorn.conf.py

defuse_stdlib()
django.setup()

# pylint: disable=wrong-import-position
from authentik.root import websocket  # noqa  # isort:skip


# See https://github.com/encode/starlette/blob/master/starlette/types.py
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]

ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

ASGI_IP_HEADERS = (
    b"x-forwarded-for",
    b"x-real-ip",
)

LOGGER = get_logger("authentik.asgi")


class ASGILogger:
    """ASGI Logger, instantiated for each request"""

    app: ASGIApp

    status_code: int
    start: float

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        content_length = 0
        request_id = ""

        async def send_hooked(message: Message) -> None:
            """Hooked send method, which records status code and content-length, and for the final
            requests logs it"""
            headers = dict(message.get("headers", []))
            if "status" in message:
                self.status_code = message["status"]

            if b"Content-Length" in headers:
                nonlocal content_length
                content_length += int(headers.get(b"Content-Length", b"0"))

            if message["type"] == "http.response.start":
                response_headers = dict(message["headers"])
                nonlocal request_id
                request_id = response_headers.get(
                    RESPONSE_HEADER_ID.encode(), b""
                ).decode()

            if message["type"] == "http.response.body" and not message.get(
                "more_body", True
            ):
                runtime = int((time() - self.start) * 1000)
                self.log(scope, runtime, content_length, request_id=request_id)
            await send(message)

        self.start = time()
        if scope["type"] == "lifespan":
            # https://code.djangoproject.com/ticket/31508
            # https://github.com/encode/uvicorn/issues/266
            return
        await self.app(scope, receive, send_hooked)

    def _get_ip(self, scope: Scope) -> str:
        client_ip = None
        headers = dict(scope.get("headers", []))
        for header in ASGI_IP_HEADERS:
            if header in headers:
                client_ip = headers[header].decode()
        if not client_ip:
            client_ip, _ = scope.get("client", ("", 0))
        # Check if header has multiple values, and use the first one
        return client_ip.split(", ")[0]

    def log(self, scope: Scope, content_length: int, runtime: float, **kwargs):
        """Outpot access logs in a structured format"""
        host = self._get_ip(scope)
        query_string = ""
        if scope.get("query_string", b"") != b"":
            query_string = f"?{scope.get('query_string').decode()}"
        LOGGER.info(
            f"{scope.get('path', '')}{query_string}",
            host=host,
            method=scope.get("method", ""),
            scheme=scope.get("scheme", ""),
            status=self.status_code,
            size=content_length / 1000 if content_length > 0 else 0,
            runtime=runtime,
            **kwargs,
        )


application = ASGILogger(
    guarantee_single_callable(
        SentryAsgiMiddleware(
            ProtocolTypeRouter(
                {
                    "http": get_asgi_application(),
                    "websocket": URLRouter(websocket.websocket_urlpatterns),
                }
            )
        )
    )
)
