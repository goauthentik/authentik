"""authentik events urls"""
from django.urls import path

from authentik.events.views import EventListView

urlpatterns = [
    # Event Log
    path("log/", EventListView.as_view(), name="log"),
]
