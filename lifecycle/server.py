"""Runs the ASGI application inside the authentik binary, which hands it connections directly."""

import asyncio
import os
from collections.abc import Callable
from hashlib import sha512
from threading import Thread
from typing import Any

from structlog.stdlib import get_logger

LOGGER = get_logger()

Message = dict[str, Any]


def send_startup_analytics():
    from authentik import authentik_full_version
    from authentik.lib.config import CONFIG
    from authentik.lib.utils.http import get_http_session
    from authentik.lib.utils.reflection import get_env
    from authentik.root.install_id import get_install_id_raw

    if CONFIG.get_bool("disable_startup_analytics", False):
        return
    env = get_env()
    if env in ["dev", "ci"]:
        return
    try:
        get_http_session().post(
            "https://goauthentik.io/api/event",
            json={
                "domain": "authentik",
                "name": "pageview",
                "referrer": authentik_full_version(),
                "url": (
                    f"http://localhost/{env}?utm_source={authentik_full_version()}&utm_medium={env}"
                ),
            },
            headers={
                "User-Agent": sha512(get_install_id_raw().encode("ascii")).hexdigest()[:16],
                "Content-Type": "application/json",
            },
            timeout=5,
        )
    except Exception:  # nosec # noqa
        pass


class Server:
    """An ASGI application, running on an event loop in its own thread"""

    def __init__(self, application, loop: asyncio.AbstractEventLoop):
        self.application = application
        self.loop = loop
        Thread(target=self.loop.run_forever, name="asgi", daemon=True).start()

    def is_alive(self) -> bool:
        return self.loop.is_running()

    def handle(
        self, scope: Message, send: Callable[[Message | None], None]
    ) -> Callable[[Message], None]:
        """Start handling a connection.

        `send` gets every message the application sends, and `None` once it is done.
        Returns the function to hand the application the messages it receives."""
        queue: asyncio.Queue[Message] = asyncio.Queue()

        async def receive() -> Message:
            return await queue.get()

        async def _send(message: Message):
            send(message)

        async def run():
            try:
                await self.application(scope, receive, _send)
            except Exception as exc:  # noqa: BLE001, the loop must survive a failing request
                LOGGER.warning("ASGI application failed", exc=exc, path=scope.get("path"))
            finally:
                send(None)

        asyncio.run_coroutine_threadsafe(run(), self.loop)
        return lambda message: self.loop.call_soon_threadsafe(queue.put_nowait, message)

    def shutdown(self):
        """The loop keeps running, so that requests still in flight can finish"""
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(os.getpid())


def load() -> Server:
    """Load authentik's ASGI application"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
    import uvloop

    from authentik.lib.debug import start_debug_server, start_pyroscope
    from authentik.root.asgi import application

    server = Server(application, uvloop.new_event_loop())
    send_startup_analytics()
    start_debug_server()
    start_pyroscope("server", worker_id="1")
    application.call_startup()
    return server
