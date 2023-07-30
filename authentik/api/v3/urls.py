"""api v3 urls"""
from importlib import import_module

from django.urls import path
from django.urls.resolvers import URLPattern
from django.views.decorators.cache import cache_page
from drf_spectacular.views import SpectacularAPIView
from rest_framework import routers
from structlog.stdlib import get_logger

from authentik.api.v3.config import ConfigView
from authentik.api.views import APIBrowserView
from authentik.lib.utils.reflection import get_apps

LOGGER = get_logger()

router = routers.DefaultRouter()
router.include_format_suffixes = False

_other_urls = []
for _authentik_app in get_apps():
    try:
        api_urls = import_module(f"{_authentik_app.name}.urls")
    except (ModuleNotFoundError, ImportError) as exc:
        LOGGER.warning("Could not import app's URLs", app_name=_authentik_app.name, exc=exc)
        continue
    if not hasattr(api_urls, "api_urlpatterns"):
        LOGGER.debug(
            "App does not define API URLs",
            app_name=_authentik_app.name,
        )
        continue
    urls: list = getattr(api_urls, "api_urlpatterns")
    for url in urls:
        if isinstance(url, URLPattern):
            _other_urls.append(url)
        else:
            router.register(*url)
    LOGGER.debug(
        "Mounted API URLs",
        app_name=_authentik_app.name,
    )


urlpatterns = (
    [
        path("", APIBrowserView.as_view(), name="schema-browser"),
    ]
    + router.urls
    + _other_urls
    + [
        path("root/config/", ConfigView.as_view(), name="config"),
        path("schema/", cache_page(86400)(SpectacularAPIView.as_view()), name="schema"),
    ]
)
