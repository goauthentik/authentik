#!/usr/bin/env python3

import os
import random
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socket import AF_UNIX
from threading import Event, Thread
from typing import Any

from dramatiq import Worker, get_broker
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()
INITIAL_WORKER_ID = 1000


class HttpHandler(BaseHTTPRequestHandler):
    def check_db(self):
        from django.db import connections

        for db_conn in connections.all():
            # Force connection reload
            db_conn.connect()
            _ = db_conn.cursor()

    def do_GET(self):
        from django.db import DatabaseError, InterfaceError, OperationalError, connections
        from psycopg.errors import AdminShutdown

        from authentik.root.monitoring import monitoring_set

        DATABASE_ERRORS = (
            AdminShutdown,
            InterfaceError,
            DatabaseError,
            OperationalError,
        )

        if self.path == "/-/metrics/":
            try:
                monitoring_set.send(self)
            except DATABASE_ERRORS as exc:
                LOGGER.warning("failed to send monitoring_set", exc=exc)
                for db_conn in connections.all():
                    db_conn.close()
                self.send_response(503)
            else:
                self.send_response(200)
            self.end_headers()
        elif self.path == "/-/health/ready/":
            try:
                self.check_db()
            except DATABASE_ERRORS as exc:
                LOGGER.warning("failed to check database health", exc=exc)
                for db_conn in connections.all():
                    db_conn.close()
                self.send_response(503)
            else:
                self.send_response(200)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


class UnixSocketServer(HTTPServer):
    address_family = AF_UNIX


def main(worker_id: int, socket_path: str):
    shutdown = Event()
    try:
        os.remove(socket_path)
    except OSError, FileNotFoundError:
        pass
    srv = UnixSocketServer(socket_path, HttpHandler)

    def immediate_shutdown(signum, frame):
        nonlocal srv
        srv.shutdown()
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

    Thread(target=srv.serve_forever).start()

    # Notify rust process that we are ready
    os.kill(os.getppid(), signal.SIGUSR2)

    shutdown.wait()

    logger.info("Shutting down worker...")

    # 5 secs if debug, 5 mins otherwise
    worker.stop(timeout=5_000 if CONFIG.get_bool("debug") else 600_000)

    srv.shutdown()

    broker.close()
    logger.info("Worker shut down.")


if __name__ == "__main__":
    if len(sys.argv) != 3:  # noqa: PLR2004
        print("USAGE: worker_process <worker_id> <socket_path>")
        sys.exit(1)

    worker_id = int(sys.argv[1])
    socket_path = sys.argv[2]

    from authentik.root.setup import setup

    setup()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

    import django

    django.setup()

    if worker_id == INITIAL_WORKER_ID:
        from lifecycle.migrate import run_migrations

        run_migrations()

    main(worker_id, socket_path)
