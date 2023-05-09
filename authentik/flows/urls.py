"""flow urls"""
from django.urls import path

from authentik.flows.api.bindings import FlowStageBindingViewSet
from authentik.flows.api.flows import FlowViewSet
from authentik.flows.api.stages import StageViewSet
from authentik.flows.models import FlowDesignation
from authentik.flows.views.executor import (
    CancelView,
    ConfigureFlowInitView,
    FlowExecutorView,
    ToDefaultFlow,
)
from authentik.flows.views.inspector import FlowInspectorView

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
    path("-/cancel/", CancelView.as_view(), name="cancel"),
    path(
        "-/configure/<uuid:stage_uuid>/",
        ConfigureFlowInitView.as_view(),
        name="configure",
    ),
]

api_urlpatterns = [
    ("flows/instances", FlowViewSet),
    ("flows/bindings", FlowStageBindingViewSet),
    ("stages/all", StageViewSet),
    path(
        "flows/executor/<slug:flow_slug>/",
        FlowExecutorView.as_view(),
        name="flow-executor",
    ),
    path(
        "flows/inspector/<slug:flow_slug>/",
        FlowInspectorView.as_view(),
        name="flow-inspector",
    ),
]
