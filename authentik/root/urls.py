"""authentik URL Configuration"""
from django.conf import settings
from django.urls import include, path
from structlog.stdlib import get_logger

from authentik.core.views import error
from authentik.lib.utils.reflection import get_apps
from authentik.root.monitoring import LiveView, MetricsView, ReadyView

LOGGER = get_logger()

handler400 = error.BadRequestView.as_view()
handler403 = error.ForbiddenView.as_view()
handler404 = error.NotFoundView.as_view()
handler500 = error.ServerErrorView.as_view()

urlpatterns = []

for _authentik_app in get_apps():
    mountpoints = None
    base_url_module = _authentik_app.name + ".urls"
    if hasattr(_authentik_app, "mountpoint"):
        mountpoint = getattr(_authentik_app, "mountpoint")
        mountpoints = {base_url_module: mountpoint}
    if hasattr(_authentik_app, "mountpoints"):
        mountpoints = getattr(_authentik_app, "mountpoints")
    if not mountpoints:
        continue
    for module, mountpoint in mountpoints.items():
        namespace = _authentik_app.label + module.replace(base_url_module, "")
        _path = path(
            mountpoint,
            include(
                (module, _authentik_app.label),
                namespace=namespace,
            ),
        )
        urlpatterns.append(_path)
        LOGGER.debug(
            "Mounted URLs",
            app_name=_authentik_app.name,
            app_mountpoint=mountpoint,
            namespace=namespace,
        )

urlpatterns += [
    path("-/metrics/", MetricsView.as_view(), name="metrics"),
    path("-/health/live/", LiveView.as_view(), name="health-live"),
    path("-/health/ready/", ReadyView.as_view(), name="health-ready"),
]

if settings.DEBUG:
    urlpatterns += [
        path("debug/silk/", include("silk.urls", namespace="silk")),
    ]
