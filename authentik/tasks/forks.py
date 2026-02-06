from signal import pause

from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


def worker_healthcheck():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import WorkerHealthcheckMiddleware

    host, _, port = CONFIG.get("listen.http").rpartition(":")

    try:
        port = int(port)
    except ValueError:
        LOGGER.error(f"Invalid port entered: {port}")
        return

    if CONFIG.get_bool("debug"):
        port += 1
        LOGGER.debug("Debug mode: offsetting worker healthcheck port", port=port)

    WorkerHealthcheckMiddleware.run(host, port)
    pause()


def worker_status():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import WorkerStatusMiddleware

    WorkerStatusMiddleware.run()


def worker_metrics():
    import authentik.tasks.setup  # noqa
    from authentik.tasks.middleware import MetricsMiddleware

    addr, _, port = CONFIG.get("listen.metrics").rpartition(":")

    try:
        port = int(port)
    except ValueError:
        LOGGER.error(f"Invalid port entered: {port}")

    MetricsMiddleware.run(addr, port)
    pause()
