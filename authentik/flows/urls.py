"""flow urls"""
from django.urls import path

from authentik.flows.models import FlowDesignation
from authentik.flows.views.executor import CancelView, ConfigureFlowInitView, ToDefaultFlow

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
