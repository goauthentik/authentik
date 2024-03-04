"""root Websocket URLS"""

from importlib import import_module

from channels.routing import URLRouter
from django.urls import path
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.utils.reflection import get_apps

LOGGER = get_logger()

_websocket_urlpatterns = []
for _authentik_app in get_apps():
    try:
        api_urls = import_module(f"{_authentik_app.name}.urls")
    except ModuleNotFoundError:
        continue
    if not hasattr(api_urls, "websocket_urlpatterns"):
        continue
    urls: list = api_urls.websocket_urlpatterns
    _websocket_urlpatterns.extend(urls)
    LOGGER.debug(
        "Mounted Websocket URLs",
        app_name=_authentik_app.name,
    )

websocket_urlpatterns = [
    path(
        CONFIG.get("web.path", "/")[1:],
        URLRouter(_websocket_urlpatterns),
    ),
]
