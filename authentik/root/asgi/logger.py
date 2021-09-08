"""ASGI Logger"""
from time import time

from structlog.stdlib import get_logger

from authentik.core.middleware import RESPONSE_HEADER_ID
from authentik.root.asgi.types import ASGIApp, Message, Receive, Scope, Send

ASGI_IP_HEADERS = (
    b"x-forwarded-for",
    b"x-real-ip",
)

LOGGER = get_logger("authentik.asgi")


class ASGILogger:
    """ASGI Logger, instantiated for each request"""

    app: ASGIApp

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        content_length = 0
        status_code = 0
        request_id = ""
        location = ""
        start = time()

        async def send_hooked(message: Message) -> None:
            """Hooked send method, which records status code and content-length, and for the final
            requests logs it"""

            headers = dict(message.get("headers", []))
            if "status" in message:
                nonlocal status_code
                status_code = message["status"]

            if b"Content-Length" in headers:
                nonlocal content_length
                content_length += int(headers.get(b"Content-Length", b"0"))

            if message["type"] == "http.response.start":
                response_headers = dict(message["headers"])
                nonlocal request_id
                nonlocal location
                request_id = response_headers.get(RESPONSE_HEADER_ID.encode(), b"").decode()
                location = response_headers.get(b"Location", b"").decode()

            if message["type"] == "http.response.body" and not message.get("more_body", True):
                nonlocal start
                runtime = int((time() - start) * 1000)
                kwargs = {"request_id": request_id}
                if location != "":
                    kwargs["location"] = location
                self.log(scope, runtime, content_length, status_code, **kwargs)
            await send(message)

        if scope["type"] == "lifespan":
            # https://code.djangoproject.com/ticket/31508
            # https://github.com/encode/uvicorn/issues/266
            return
        return await self.app(scope, receive, send_hooked)

    def _get_ip(self, headers: dict[str, str], scope: Scope) -> str:
        client_ip = None
        for header in ASGI_IP_HEADERS:
            if header in headers:
                client_ip = headers[header].decode()
        if not client_ip:
            client_ip, _ = scope.get("client", ("", 0))
        # Check if header has multiple values, and use the first one
        return client_ip.split(", ")[0]

    def log(self, scope: Scope, content_length: int, runtime: float, status_code: int, **kwargs):
        """Outpot access logs in a structured format"""
        headers = dict(scope.get("headers", []))
        host = self._get_ip(headers, scope)
        query_string = ""
        if scope.get("query_string", b"") != b"":
            query_string = f"?{scope.get('query_string').decode()}"
        LOGGER.info(
            f"{scope.get('path', '')}{query_string}",
            host=host,
            method=scope.get("method", ""),
            scheme=scope.get("scheme", ""),
            status=status_code,
            size=content_length / 1000 if content_length > 0 else 0,
            runtime=runtime,
            user_agent=headers.get(b"user-agent", b"").decode(),
            **kwargs,
        )
