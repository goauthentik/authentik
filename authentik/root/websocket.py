"""root Websocket URLS"""
from importlib import import_module

from structlog.stdlib import get_logger

from authentik.lib.utils.reflection import get_apps

LOGGER = get_logger()

websocket_urlpatterns = []
for _authentik_app in get_apps():
    try:
        api_urls = import_module(f"{_authentik_app.name}.urls")
    except ModuleNotFoundError:
        continue
    if not hasattr(api_urls, "websocket_urlpatterns"):
        continue
    urls: list = getattr(api_urls, "websocket_urlpatterns")
    websocket_urlpatterns.extend(urls)
    LOGGER.debug(
        "Mounted Websocket URLs",
        app_name=_authentik_app.name,
    )
