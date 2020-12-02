"""authentik audit urls"""
from django.urls import path

from authentik.audit.views import EventListView

urlpatterns = [
    # Audit Log
    path("audit/", EventListView.as_view(), name="log"),
]
