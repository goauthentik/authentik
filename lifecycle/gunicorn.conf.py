"""Gunicorn config"""
import os
import pwd
from multiprocessing import cpu_count

import structlog
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

bind = "127.0.0.1:8000"
reload = True

try:
    pwd.getpwnam("authentik")
    user = "authentik"
    group = "authentik"
except KeyError:
    pass

worker_class = "uvicorn.workers.UvicornWorker"
# Docker containers don't have /tmp as tmpfs
if os.path.exists("/dev/shm"):  # nosec
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
threads = int(os.environ.get("THREADS", 4))
