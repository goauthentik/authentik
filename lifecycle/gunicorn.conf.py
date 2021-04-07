"""Gunicorn config"""
import os
import warnings
from multiprocessing import cpu_count

import structlog
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

bind = "0.0.0.0:8000"

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
    workers = cpu_count() * 2 + 1
threads = 4

warnings.simplefilter("once")
