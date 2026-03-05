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

        if self.path == "/-/metrics/":
            from authentik.root.monitoring import monitoring_set

            monitoring_set.send_robust(self)
            self.send_response(200)
            self.end_headers()
        elif self.path == "/-/health/ready/":
            from django.db.utils import OperationalError

            try:
                self.check_db()
            except OperationalError:
                self.send_response(503)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


class UnixSocketServer(HTTPServer):
    address_family = AF_UNIX


def main(worker_id: int, socket_path: str | None):
    shutdown = Event()
    srv = None

    def immediate_shutdown(signum, frame):
        nonlocal srv
        if srv is not None:
            srv.shutdown()
            if socket_path:
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

    if socket_path:
        srv = UnixSocketServer(socket_path, HttpHandler)
        Thread(target=srv.serve_forever).start()

        # Notify rust process that we are ready
        os.kill(os.getppid(), signal.SIGUSR2)

    shutdown.wait()

    logger.info("Shutting down worker...")
    if srv is not None:
        srv.shutdown()
        if socket_path:
            os.remove(socket_path)
    # 5 secs if debug, 5 mins otherwise
    worker.stop(timeout=5_000 if CONFIG.get_bool("debug") else 600_000)
    broker.close()
    logger.info("Worker shut down.")


if __name__ == "__main__":
    if len(sys.argv) not in [2, 3]:
        print("USAGE: worker_process <worker_id> [SOCKET_PATH]")
        sys.exit(1)

    worker_id = int(sys.argv[1])
    socket_path = sys.argv[2] if len(sys.argv) == 3 else None

    from authentik.root.setup import setup

    setup()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

    import django

    django.setup()

    from django.core.management import execute_from_command_line

    if socket_path:
        from lifecycle.migrate import run_migrations

        run_migrations()

        if (
            "AUTHENTIK_BOOTSTRAP_PASSWORD" in os.environ
            or "AUTHENTIK_BOOTSTRAP_TOKEN" in os.environ
        ):
            try:
                execute_from_command_line(["", "apply_blueprint", "system/bootstrap.yaml"])
            except Exception as exc:
                sys.stderr.write(f"Failed to apply bootstrap blueprint: {exc}")

    main(worker_id, socket_path)
