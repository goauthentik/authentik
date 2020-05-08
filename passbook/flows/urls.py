"""flow urls"""
from django.urls import path

from passbook.flows.views import FlowExecutorView

urlpatterns = [
    path("<slug:flow_slug>/", FlowExecutorView.as_view(), name="flow-executor"),
]
