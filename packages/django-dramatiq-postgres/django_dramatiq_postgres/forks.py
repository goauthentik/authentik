import os
from signal import pause

from django.utils.module_loading import import_module

from django_dramatiq_postgres.conf import Conf


def worker_metrics():
    import_module(Conf().autodiscovery["setup_module"])

    from django_dramatiq_postgres.middleware import MetricsMiddleware

    MetricsMiddleware.run(
        os.getenv("dramatiq_prom_host", "0.0.0.0"),  # nosec
        int(os.getenv("dramatiq_prom_port", "9191")),
    )
    pause()
