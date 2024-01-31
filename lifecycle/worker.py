"""Uvicorn worker"""

from uvicorn.workers import UvicornWorker


class DjangoUvicornWorker(UvicornWorker):
    """Custom configured Uvicorn Worker without lifespan"""

    CONFIG_KWARGS = {
        "loop": "uvloop",
        "http": "httptools",
        "lifespan": "off",
        "ws": "wsproto",
    }
