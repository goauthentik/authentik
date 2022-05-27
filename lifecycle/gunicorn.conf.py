"""Gunicorn config"""
import os
import pwd
from hashlib import sha512
from multiprocessing import cpu_count
from tempfile import gettempdir

import structlog
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME
from prometheus_client.values import MultiProcessValue

from authentik import get_full_version
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.reflection import get_env
from lifecycle.worker import DjangoUvicornWorker

bind = "127.0.0.1:8000"

try:
    pwd.getpwnam("authentik")
    user = "authentik"
    group = "authentik"
except KeyError:
    pass

worker_class = "lifecycle.worker.DjangoUvicornWorker"
worker_tmp_dir = gettempdir()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", worker_tmp_dir)

max_requests = 1000
max_requests_jitter = 50

_debug = CONFIG.y_bool("DEBUG", False)

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(),
                structlog.processors.StackInfoRenderer(),
            ],
        },
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True),
            "foreign_pre_chain": [
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(),
                structlog.processors.StackInfoRenderer(),
            ],
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json" if _debug else "console"},
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "gunicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# if we're running in kubernetes, use fixed workers because we can scale with more pods
# otherwise (assume docker-compose), use as much as we can
if SERVICE_HOST_ENV_NAME in os.environ:
    default_workers = 2
else:
    default_workers = max(cpu_count() * 0.25, 1) + 1  # Minimum of 2 workers

workers = int(os.environ.get("WORKERS", default_workers))
threads = int(os.environ.get("THREADS", 4))

# pylint: disable=unused-argument
def post_fork(server, worker: DjangoUvicornWorker):
    """Tell prometheus to use worker number instead of process ID for multiprocess"""
    from prometheus_client import values

    values.ValueClass = MultiProcessValue(lambda: worker.nr)


# pylint: disable=unused-argument
def worker_exit(server, worker: DjangoUvicornWorker):
    """Remove pid dbs when worker is shutdown"""
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.nr)


if not CONFIG.y_bool("disable_startup_analytics", False):
    env = get_env()
    should_send = env not in ["dev", "ci"]
    if should_send:
        try:
            get_http_session().post(
                "https://goauthentik.io/api/event",
                json={
                    "domain": "authentik",
                    "name": "pageview",
                    "referrer": get_full_version(),
                    "url": (
                        f"http://localhost/{env}?utm_source={get_full_version()}&utm_medium={env}"
                    ),
                },
                headers={
                    "User-Agent": sha512(str(CONFIG.y("secret_key")).encode("ascii")).hexdigest()[
                        :16
                    ],
                    "Content-Type": "application/json",
                },
                timeout=5,
            )
        # pylint: disable=bare-except
        except:  # nosec
            pass
