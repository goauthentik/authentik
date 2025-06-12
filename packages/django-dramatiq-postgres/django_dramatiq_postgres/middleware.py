from django.db import (
    close_old_connections,
    connections,
)
from dramatiq.middleware.middleware import Middleware

from django_dramatiq_postgres.conf import Conf


class DbConnectionMiddleware(Middleware):
    def _close_old_connections(self, *args, **kwargs):
        if Conf.test:
            return
        close_old_connections()

    before_process_message = _close_old_connections
    after_process_message = _close_old_connections

    def _close_connections(self, *args, **kwargs):
        connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections
