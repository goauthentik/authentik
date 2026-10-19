"""Runs authentik's applications in the processes the authentik binary forks for them, which
hands them connections directly."""

import asyncio
import os
import platform
import signal
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
        # Set by `post_fork()`, once `authentik.root.wsgi` is importable. Ordinary HTTP
        # requests are dispatched to this directly, from whichever thread the
        # embedding binary calls it on, instead of through the ASGI app above.
        self.wsgi_application = None
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


def preload():
    """Load authentik's applications once, before the server forks the processes that run them"""
    from authentik.lib.tracing.common import TRACER_DEFER_POSTFORK_ENV_VAR

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
    # Tracing backends start threads, which don't survive the fork, so they are set up in
    # `post_fork` instead
    os.environ[TRACER_DEFER_POSTFORK_ENV_VAR] = "true"
    # libpq can try Kerberos/GSS on macOS, and urllib can consult the system's proxy settings,
    # neither of which is fork-safe
    if platform.system() == "Darwin":
        os.environ.setdefault("PGGSSENCMODE", "disable")
        os.environ.setdefault("NO_PROXY", "*")
        os.environ.setdefault("no_proxy", "*")

    # The server waits for its forked processes to exit with `sigwait`, which never sees SIGCHLD
    # on macOS while it is ignored, as it is by default
    signal.signal(signal.SIGCHLD, lambda *_: None)

    from django.db import connections

    import authentik.root.asgi  # noqa: F401
    import authentik.root.wsgi  # noqa: F401

    send_startup_analytics()
    # Forked processes must open their own
    connections.close_all()


def post_fork(worker_id: int) -> Server:
    """Start serving in a process forked after `preload`"""
    import uvloop

    from authentik.lib.config import CONFIG
    from authentik.lib.debug import start_debug_server, start_pyroscope
    from authentik.root.asgi import application
    from authentik.root.wsgi import application as wsgi_application

    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    if CONFIG.get_bool("error_reporting.enabled", False):
        from authentik.lib.tracing import setup_post_fork

        setup_post_fork()
    start_pyroscope("server", worker_id=str(worker_id))

    server = Server(application, uvloop.new_event_loop())
    server.wsgi_application = wsgi_application
    # Only once, startup code needed in every process doesn't use this signal
    if worker_id == 1:
        start_debug_server()
        application.call_startup()
    LOGGER.info("Started server process", worker_id=worker_id)
    return server
