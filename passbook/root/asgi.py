"""
ASGI config for passbook project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""
import typing
from time import time
from typing import Any, ByteString, Dict

import django
from asgiref.compatibility import guarantee_single_callable
from channels.routing import ProtocolTypeRouter, URLRouter
from defusedxml import defuse_stdlib
from django.core.asgi import get_asgi_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from structlog import get_logger

# DJANGO_SETTINGS_MODULE is set in gunicorn.conf.py

defuse_stdlib()
django.setup()

# pylint: disable=wrong-import-position
from passbook.root import websocket  # noqa  # isort:skip


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

LOGGER = get_logger("passbook.asgi")


class ASGILoggerMiddleware:
    """Main ASGI Logger middleware, starts an ASGILogger for each request"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        responder = ASGILogger(self.app)
        await responder(scope, receive, send)
        return


class ASGILogger:
    """ASGI Logger, instantiated for each request"""

    app: ASGIApp

    scope: Scope
    headers: Dict[ByteString, Any]

    status_code: int
    start: float
    content_length: int

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.scope = scope
        self.content_length = 0
        self.headers = dict(scope.get("headers", []))

        async def send_hooked(message: Message) -> None:
            """Hooked send method, which records status code and content-length, and for the final
            requests logs it"""
            headers = dict(message.get("headers", []))

            if "status" in message:
                self.status_code = message["status"]

            if b"Content-Length" in headers:
                self.content_length += int(headers.get(b"Content-Length", b"0"))

            if message["type"] == "http.response.body" and not message["more_body"]:
                runtime = int((time() - self.start) * 10 ** 6)
                self.log(runtime)
            await send(message)

        if self.headers.get(b"host", b"") == b"passbook-healthcheck-host":
            # Don't log healthcheck/readiness requests
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": ""})
            return

        self.start = time()
        if scope["type"] == "lifespan":
            # https://code.djangoproject.com/ticket/31508
            # https://github.com/encode/uvicorn/issues/266
            return
        await self.app(scope, receive, send_hooked)

    def _get_ip(self) -> str:
        client_ip = None
        for header in ASGI_IP_HEADERS:
            if header in self.headers:
                client_ip = self.headers[header].decode()
        if not client_ip:
            client_ip, _ = self.scope.get("client", ("", 0))
        # Check if header has multiple values, and use the first one
        return client_ip.split(", ")[0]

    def log(self, runtime: float):
        """Outpot access logs in a structured format"""
        host = self._get_ip()
        query_string = ""
        if self.scope.get("query_string", b"") != b"":
            query_string = f"?{self.scope.get('query_string').decode()}"
        LOGGER.info(
            f"{self.scope.get('path', '')}{query_string}",
            host=host,
            method=self.scope.get("method", ""),
            scheme=self.scope.get("scheme", ""),
            status=self.status_code,
            size=self.content_length / 1000 if self.content_length > 0 else "-",
            runtime=runtime,
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
