#!/usr/bin/env python3
import os
import random
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socket import AF_UNIX
from tempfile import gettempdir
from threading import Event, Thread
from typing import Any

from dramatiq import Worker, get_broker
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()
INITIAL_WORKER_ID = 1000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/-/metrics/":
            from authentik.root.monitoring import monitoring_set

            monitoring_set.send_robust(self)
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


class UnixSocketServer(HTTPServer):
    address_family = AF_UNIX


def main(worker_id: int):
    socket_path = os.path.join(gettempdir(), "authentik-worker.sock")
    shutdown = Event()
    srv = None

    def immediate_shutdown(signum, frame):
        nonlocal srv
        if srv is not None:
            srv.shutdown()
            os.remove(socket_path)
        sys.exit(0)

    def graceful_shutdown(signum, frame):
        nonlocal shutdown
        shutdown.set()

    signal.signal(signal.SIGHUP, immediate_shutdown)
    signal.signal(signal.SIGINT, immediate_shutdown)
    signal.signal(signal.SIGQUIT, immediate_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    random.seed()

    logger = LOGGER.bind(worker_id=worker_id)

    logger.debug("Loading broker...")
    broker = get_broker()
    broker.emit_after("process_boot")

    logger.debug("Starting worker threads...")
    queues = None  # all queues
    worker = Worker(broker, queues=queues, worker_threads=CONFIG.get_int("worker.threads"))
    worker.worker_id = worker_id
    worker.start()
    logger.info("Worker process is ready for action.")

    if worker_id == INITIAL_WORKER_ID:
        srv = UnixSocketServer(socket_path, HttpHandler)
        Thread(target=srv.serve_forever).start()

        # Notify rust process that we are ready
        os.kill(os.getppid(), signal.SIGUSR2)

    shutdown.wait()

    logger.info("Shutting down worker...")
    if srv is not None:
        srv.shutdown()
        os.remove(socket_path)
    # 5 secs if debug, 5 mins otherwise
    worker.stop(timeout=5_000 if CONFIG.get_bool("debug") else 600_000)
    broker.close()
    logger.info("Worker shut down.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: worker_process <worker_id>")
        sys.exit(1)

    worker_id = int(sys.argv[1])

    from authentik.root.setup import setup

    setup()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

    import django

    django.setup()

    if worker_id == INITIAL_WORKER_ID:
        from lifecycle.migrate import run_migrations

        run_migrations()

    main(worker_id)
