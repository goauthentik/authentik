"""Gunicorn config"""
import os
import warnings
from multiprocessing import cpu_count

import structlog
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

bind = "127.0.0.1:8000"

user = "authentik"
group = "authentik"

worker_class = "uvicorn.workers.UvicornWorker"
# Docker containers don't have /tmp as tmpfs
worker_tmp_dir = "/dev/shm"  # nosec

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ],
        }
    },
    "handlers": {
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
        },
        "console": {"class": "logging.StreamHandler", "formatter": "json_formatter"},
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "gunicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# if we're running in kubernetes, use fixed workers because we can scale with more pods
# otherwise (assume docker-compose), use as much as we can
if SERVICE_HOST_ENV_NAME in os.environ:
    workers = 2
else:
    default_workers = max(cpu_count() * 0.25, 1) + 1  # Minimum of 2 workers
    workers = int(os.environ.get("WORKERS", default_workers))
threads = 4

warnings.filterwarnings(
    "ignore",
    message="defusedxml.lxml is no longer supported and will be removed in a future release.",
)
warnings.filterwarnings(
    "ignore",
    message="defusedxml.cElementTree is deprecated, import from defusedxml.ElementTree instead.",
)
warnings.filterwarnings(
    "ignore",
    message=(
        "'django_prometheus' defines default_app_config = 'django_prometheus.apps.DjangoPromethe"
        "usConfig'. Django now detects this configuration automatically. You can remove d"
        "efault_app_config."
    ),
)
warnings.filterwarnings(
    "ignore",
    message=(
        "'dbbackup' defines default_app_config = 'dbbackup.apps.DbbackupConfig'. Django now det"
        "ects this configuration automatically. You can remove default_app_config."
    ),
)
warnings.simplefilter("once")
