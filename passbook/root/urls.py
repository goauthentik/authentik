"""passbook URL Configuration"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from structlog import get_logger

from passbook.core.views import error
from passbook.lib.utils.reflection import get_apps
from passbook.root.monitoring import MetricsView

LOGGER = get_logger()
admin.autodiscover()
admin.site.login = RedirectView.as_view(pattern_name="passbook_flows:default-auth")
admin.site.logout = RedirectView.as_view(
    pattern_name="passbook_flows:default-invalidate"
)

handler400 = error.BadRequestView.as_view()
handler403 = error.ForbiddenView.as_view()
handler404 = error.NotFoundView.as_view()
handler500 = error.ServerErrorView.as_view()

urlpatterns = []

for _passbook_app in get_apps():
    if hasattr(_passbook_app, "mountpoint"):
        _path = path(
            _passbook_app.mountpoint,
            include(
                (_passbook_app.name + ".urls", _passbook_app.label),
                namespace=_passbook_app.label,
            ),
        )
        urlpatterns.append(_path)
        LOGGER.debug(
            "Mounted URLs",
            app_name=_passbook_app.name,
            mountpoint=_passbook_app.mountpoint,
        )

urlpatterns += [
    # Administration
    path("administration/django/", admin.site.urls),
    path("metrics/", MetricsView.as_view(), name="metrics"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("-/debug/", include(debug_toolbar.urls)),] + urlpatterns
