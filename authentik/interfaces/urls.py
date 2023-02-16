"""Interface urls"""
from django.urls import path

from authentik.interfaces.views import InterfaceView

urlpatterns = [
    path(
        "<slug:if_name>/",
        InterfaceView.as_view(),
        kwargs={"flow_slug": None},
        name="if",
    ),
    path(
        "<slug:if_name>/<slug:flow_slug>/", InterfaceView.as_view(), name="if"
    ),
]
