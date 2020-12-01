"""passbook URL Configuration"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from structlog import get_logger
from django.views.i18n import JavaScriptCatalog

from passbook.core.views import error
from passbook.lib.utils.reflection import get_apps
from passbook.root.monitoring import MetricsView

LOGGER = get_logger()
admin.autodiscover()
admin.site.login = RedirectView.as_view(
    pattern_name="passbook_flows:default-authentication"
)
admin.site.logout = RedirectView.as_view(
    pattern_name="passbook_flows:default-invalidation"
)

handler400 = error.BadRequestView.as_view()
handler403 = error.ForbiddenView.as_view()
handler404 = error.NotFoundView.as_view()
handler500 = error.ServerErrorView.as_view()

urlpatterns = []

for _passbook_app in get_apps():
    mountpoints = None
    base_url_module = _passbook_app.name + ".urls"
    if hasattr(_passbook_app, "mountpoint"):
        mountpoint = getattr(_passbook_app, "mountpoint")
        mountpoints = {base_url_module: mountpoint}
    if hasattr(_passbook_app, "mountpoints"):
        mountpoints = getattr(_passbook_app, "mountpoints")
    if not mountpoints:
        continue
    for module, mountpoint in mountpoints.items():
        namespace = _passbook_app.label + module.replace(base_url_module, "")
        _path = path(
            mountpoint,
            include(
                (module, _passbook_app.label),
                namespace=namespace,
            ),
        )
        urlpatterns.append(_path)
        LOGGER.debug(
            "Mounted URLs",
            app_name=_passbook_app.name,
            mountpoint=mountpoint,
            namespace=namespace,
        )

urlpatterns += [
    path("administration/django/", admin.site.urls),
    path("metrics/", MetricsView.as_view(), name="metrics"),
    path("-/jsi18n/", JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = (
        [
            path("-/debug/", include(debug_toolbar.urls)),
        ]
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        + urlpatterns
    )
