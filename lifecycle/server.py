"""Single-process ASGI server for native macOS development.

Gunicorn's pre-fork workers cannot safely initialize Apple's networking APIs,
including DNS resolution used by Gravatar, after the application has loaded.
The Rust supervisor launches this module in a fresh Python process instead.
"""

import os
import signal
import sys
from socket import socket

from prometheus_client import multiprocess, values
from prometheus_client.values import MultiProcessValue
from uvicorn import Config, Server

from authentik.lib.debug import start_debug_server, start_pyroscope
from authentik.lib.logging import get_logger_config
from authentik.root.setup import setup
from lifecycle.migrate import run_migrations

WORKER_ID = 1


class DevelopmentServer(Server):
    """Keep the supervisor's readiness and metrics contracts without forking."""

    async def startup(self, sockets: list[socket] | None = None) -> None:
        await super().startup(sockets=sockets)
        if self.started:
            os.kill(os.getppid(), signal.SIGUSR1)

    async def shutdown(self, sockets: list[socket] | None = None) -> None:
        try:
            await super().shutdown(sockets=sockets)
        finally:
            multiprocess.mark_process_dead(WORKER_ID)


def main(socket_path: str) -> None:
    # Install the metrics worker ID before Django imports construct metrics.
    values.ValueClass = MultiProcessValue(lambda: WORKER_ID)
    setup()
    run_migrations()

    from authentik.root.asgi import application

    start_debug_server()
    start_pyroscope("server", worker_id=str(WORKER_ID))
    application.call_startup()
    DevelopmentServer(
        Config(
            application,
            uds=socket_path,
            workers=1,
            loop="uvloop",
            http="httptools",
            ws="wsproto",
            lifespan="off",
            log_config=get_logger_config(),
            access_log=False,
            timeout_graceful_shutdown=30,
        )
    ).run()


if __name__ == "__main__":
    if len(sys.argv) != 2:  # noqa: PLR2004
        sys.exit("USAGE: python -m lifecycle.server <socket_path>")
    main(sys.argv[1])
