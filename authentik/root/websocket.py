"""root Websocket URLS"""
from importlib import import_module

from structlog.stdlib import get_logger

from authentik.lib.utils.reflection import get_apps

LOGGER = get_logger()

websocket_urlpatterns = []
for _authentik_app in get_apps():
    mountpoint = getattr(_authentik_app, "ws_mountpoint", None)
    if not mountpoint:
        continue
    ws_paths = import_module(mountpoint)
    websocket_urlpatterns.extend(getattr(ws_paths, "websocket_urlpatterns"))
    LOGGER.debug(
        "Mounted URLs",
        app_name=_authentik_app.name,
        app_mountpoint=mountpoint,
    )
