"""Uvicorn worker"""

from uvicorn.workers import UvicornWorker

from authentik.lib.config import CONFIG


class DjangoUvicornWorker(UvicornWorker):
    """Custom configured Uvicorn Worker without lifespan"""

    CONFIG_KWARGS = {
        "loop": "uvloop",
        "http": "httptools",
        "lifespan": "off",
        "ws": "wsproto",
        "timeout_graceful_shutdown": CONFIG.get_optional_int(
            "gunicorn.timeout_graceful_shutdown",
            10,
        ),
    }

    _worker_id: int
