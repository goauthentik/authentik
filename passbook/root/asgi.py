"""
ASGI config for passbook project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""
import os
import typing
from time import time
from typing import Any, ByteString, Dict

import django
from asgiref.compatibility import guarantee_single_callable
from channels.routing import get_default_application
from defusedxml import defuse_stdlib
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from structlog import get_logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "passbook.root.settings")

defuse_stdlib()
django.setup()

# See https://github.com/encode/starlette/blob/master/starlette/types.py
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]

ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

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
    send: Send

    scope: Scope
    headers: Dict[ByteString, Any]

    status_code: int
    start: float
    content_length: int

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.send = send
        self.scope = scope
        self.content_length = 0
        self.headers = dict(scope.get("headers", []))

        if self.headers.get(b"host", b"") == b"kubernetes-healthcheck-host":
            # Don't log kubernetes health/readiness requests
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": ""})
            return

        self.start = time()
        if scope["type"] == "lifespan":
            # https://code.djangoproject.com/ticket/31508
            # https://github.com/encode/uvicorn/issues/266
            return
        await self.app(scope, receive, self.send_hooked)

    async def send_hooked(self, message: Message) -> None:
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
        return await self.send(message)

    def _get_ip(self) -> str:
        client_ip, _ = self.scope.get("client", ("", 0))
        return client_ip

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
    guarantee_single_callable(SentryAsgiMiddleware(get_default_application()))
)
