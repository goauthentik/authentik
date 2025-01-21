"""SSF provider URLs"""

from django.urls import path

from authentik.enterprise.providers.ssf.api.providers import SSFProviderViewSet
from authentik.enterprise.providers.ssf.api.streams import SSFStreamViewSet
from authentik.enterprise.providers.ssf.views.configuration import ConfigurationView
from authentik.enterprise.providers.ssf.views.jwks import JWKSview
from authentik.enterprise.providers.ssf.views.stream import StreamView

urlpatterns = [
    path(
        "application/ssf/<slug:application_slug>/ssf-jwks/",
        JWKSview.as_view(),
        name="jwks",
    ),
    path(
        ".well-known/ssf-configuration/<slug:application_slug>",
        ConfigurationView.as_view(),
        name="configuration",
    ),
    path(
        "application/ssf/<slug:application_slug>/stream/",
        StreamView.as_view(),
        name="stream",
    ),
]

api_urlpatterns = [
    ("providers/ssf", SSFProviderViewSet),
    ("ssf/streams", SSFStreamViewSet),
]
