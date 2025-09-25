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

    listen: str = CONFIG.get("listen.debug_py", "127.0.0.1:9901")
    host, _, port = listen.rpartition(":")
    try:
        debugpy.listen((host, int(port)), **kwargs)  # nosec
    except RuntimeError:
        LOGGER.warning("Could not start debug server. Continuing without")
        return False
    LOGGER.debug("Starting debug server", host=host, port=port)
    return True
