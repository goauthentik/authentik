import os
from importlib import import_module
from signal import pause

from django_dramatiq_postgres.conf import Conf


def worker_metrics() -> None:
    import_module(Conf().autodiscovery["setup_module"])

    from django_dramatiq_postgres.middleware import MetricsMiddleware

    MetricsMiddleware.run(
        os.getenv("dramatiq_prom_host", "0.0.0.0"),  # nosec
        int(os.getenv("dramatiq_prom_port", "9191")),
    )
    pause()
