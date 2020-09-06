"""Gunicorn config"""
import multiprocessing

import structlog

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1

user = "passbook"
group = "passbook"

worker_class = "uvicorn.workers.UvicornWorker"

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
