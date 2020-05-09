"""flow urls"""
from django.urls import path

from passbook.flows.views import FlowExecutorView, FlowPermissionDeniedView

urlpatterns = [
    path("denied/", FlowPermissionDeniedView.as_view(), name="denied"),
    path("<slug:flow_slug>/", FlowExecutorView.as_view(), name="flow-executor"),
]
