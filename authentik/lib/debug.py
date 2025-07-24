from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


def start_debug_server(**kwargs) -> bool:
    """Attempt to start a debugpy server in the current process.
    Returns true if the server was started successfully, otherwise false"""
    if not CONFIG.get_bool("debug") and not CONFIG.get_bool("debugger"):
        return
    try:
        import debugpy
    except ImportError:
        LOGGER.warning(
            "Failed to import debugpy. debugpy is not included "
            "in the default release dependencies and must be installed manually"
        )
        return False

    listen: str = CONFIG.get("listen.listen_debug_py", "127.0.0.1:9901")
    host, _, port = listen.rpartition(":")
    debugpy.listen((host, int(port)), **kwargs)  # nosec
    LOGGER.debug("Starting debug server", host=host, port=port)
    return True
