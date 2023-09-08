"""logging helpers"""
import logging
from logging import Logger
from os import getpid

import structlog

from authentik.lib.config import CONFIG

LOG_PRE_CHAIN = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(),
    structlog.processors.StackInfoRenderer(),
]


def get_log_level():
    """Get log level, clamp trace to debug"""
    level = CONFIG.get("log_level").upper()
    # We could add a custom level to stdlib logging and structlog, but it's not easy or clean
    # https://stackoverflow.com/questions/54505487/custom-log-level-not-working-with-structlog
    # Additionally, the entire code uses debug as highest level
    # so that would have to be re-written too
    if level == "TRACE":
        level = "DEBUG"
    return level


def structlog_configure():
    """Configure structlog itself"""
    structlog.configure_once(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.contextvars.merge_contextvars,
            add_process_id,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.dict_tracebacks,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, get_log_level(), logging.WARNING)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger_config():
    """Configure python stdlib's logging"""
    debug = CONFIG.get_bool("debug")
    global_level = get_log_level()
    base_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(sort_keys=True),
                "foreign_pre_chain": LOG_PRE_CHAIN + [structlog.processors.dict_tracebacks],
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=debug),
                "foreign_pre_chain": LOG_PRE_CHAIN,
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "console" if debug else "json",
            },
        },
        "loggers": {},
    }

    handler_level_map = {
        "": global_level,
        "authentik": global_level,
        "django": "WARNING",
        "django.request": "ERROR",
        "celery": "WARNING",
        "selenium": "WARNING",
        "docker": "WARNING",
        "urllib3": "WARNING",
        "websockets": "WARNING",
        "daphne": "WARNING",
        "kubernetes": "INFO",
        "asyncio": "WARNING",
        "redis": "WARNING",
        "silk": "INFO",
        "fsevents": "WARNING",
        "uvicorn": "WARNING",
        "gunicorn": "INFO",
    }
    for handler_name, level in handler_level_map.items():
        base_config["loggers"][handler_name] = {
            "handlers": ["console"],
            "level": level,
            "propagate": False,
        }
    return base_config


def add_process_id(logger: Logger, method_name: str, event_dict):
    """Add the current process ID"""
    event_dict["pid"] = getpid()
    return event_dict
