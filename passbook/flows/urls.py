"""flow urls"""
from django.urls import path

from passbook.flows.models import FlowDesignation
from passbook.flows.views import (
    CancelView,
    FlowExecutorShellView,
    FlowExecutorView,
    ToDefaultFlow,
)

urlpatterns = [
    path(
        "-/default/authentication/",
        ToDefaultFlow.as_view(designation=FlowDesignation.AUTHENTICATION),
        name="default-authentication",
    ),
    path(
        "-/default/invalidation/",
        ToDefaultFlow.as_view(designation=FlowDesignation.INVALIDATION),
        name="default-invalidation",
    ),
    path(
        "-/default/recovery/",
        ToDefaultFlow.as_view(designation=FlowDesignation.RECOVERY),
        name="default-recovery",
    ),
    path(
        "-/default/enrollment/",
        ToDefaultFlow.as_view(designation=FlowDesignation.ENROLLMENT),
        name="default-enrollment",
    ),
    path(
        "-/default/unenrollment/",
        ToDefaultFlow.as_view(designation=FlowDesignation.UNRENOLLMENT),
        name="default-unenrollment",
    ),
    path("-/cancel/", CancelView.as_view(), name="cancel"),
    path("b/<slug:flow_slug>/", FlowExecutorView.as_view(), name="flow-executor"),
    path(
        "<slug:flow_slug>/", FlowExecutorShellView.as_view(), name="flow-executor-shell"
    ),
]
