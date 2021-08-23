"""ASGI Error handler"""
from structlog.stdlib import get_logger

from authentik.root.asgi.types import ASGIApp, Receive, Scope, Send

LOGGER = get_logger("authentik.asgi")


class ASGIErrorHandler:
    """ASGI Error handler"""

    app: ASGIApp

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            return await self.app(scope, receive, send)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Fatal ASGI exception", exc=exc)
            return await self.error_handler(send)

    async def error_handler(self, send: Send) -> None:
        """Return a generic error message"""
        return await send(
            {
                "type": "http.request",
                "body": b"Internal server error",
                "more_body": False,
            }
        )
