"""passbook audit urls"""
from django.urls import path

from passbook.audit.views import EventListView

urlpatterns = [
    # Audit Log
    path("audit/", EventListView.as_view(), name="log"),
]
