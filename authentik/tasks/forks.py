from signal import pause

from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


def worker_status():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import WorkerStatusMiddleware

    WorkerStatusMiddleware.worker_status()


def worker_metrics():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import MetricsMiddleware

    addr, _, port = CONFIG.get("listen.listen_metrics").rpartition(":")

    try:
        port = int(port)
        MetricsMiddleware.run(addr, port)
    except ValueError:
        LOGGER.error(f"Invalid port entered: {port}")
        pause()
