from os import environ
from socket import gethostname

from structlog.stdlib import get_logger

from authentik import authentik_build_hash, authentik_full_version, authentik_version
from authentik.lib.config import CONFIG

LOGGER = get_logger()


def start_debug_server(port_offset: int = 0, **kwargs) -> bool:
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
    port = int(port) + port_offset
    try:
        debugpy.listen((host, port), **kwargs)  # nosec
    except RuntimeError:
        LOGGER.warning("Could not start debug server. Continuing without")
        return False
    LOGGER.debug("Starting debug server", host=host, port=port)
    return True


def start_pyroscope(component: str, **tags: str) -> bool:
    """Attempt to start the pyroscope profiler in the current process.
    Must be called *after* forking, the profiler's agent threads do not survive fork().
    Returns true if the profiler was started, otherwise false"""
    server = environ.get("AUTHENTIK_PYROSCOPE_HOST")
    if not server:
        return False

    import pyroscope

    LOGGER.debug("Starting pyroscope profiler", server=server, component=component)
    pyroscope.configure(
        application_name="authentik",
        server_address=server,
        tags={
            "component": component,
            "hostname": gethostname(),
            "service_repository": "https://github.com/goauthentik/authentik",
            "service_git_ref": authentik_build_hash(),
            "authentik_version": authentik_version(),
            "authentik_full_version": authentik_full_version(),
            **tags,
        },
        mem_enabled=True,
    )
    return True
