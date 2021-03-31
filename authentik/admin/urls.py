"""authentik URL Configuration"""
from django.urls import path

from authentik.admin.views import (
    outposts_service_connections,
    policies,
    property_mappings,
    providers,
    sources,
    stages,
)
from authentik.providers.saml.views.metadata import MetadataImportView

urlpatterns = [
    # Sources
    path("sources/create/", sources.SourceCreateView.as_view(), name="source-create"),
    path(
        "sources/<uuid:pk>/update/",
        sources.SourceUpdateView.as_view(),
        name="source-update",
    ),
    # Policies
    path("policies/create/", policies.PolicyCreateView.as_view(), name="policy-create"),
    path(
        "policies/<uuid:pk>/update/",
        policies.PolicyUpdateView.as_view(),
        name="policy-update",
    ),
    # Providers
    path(
        "providers/create/",
        providers.ProviderCreateView.as_view(),
        name="provider-create",
    ),
    path(
        "providers/create/saml/from-metadata/",
        MetadataImportView.as_view(),
        name="provider-saml-from-metadata",
    ),
    path(
        "providers/<int:pk>/update/",
        providers.ProviderUpdateView.as_view(),
        name="provider-update",
    ),
    # Stages
    path("stages/create/", stages.StageCreateView.as_view(), name="stage-create"),
    path(
        "stages/<uuid:pk>/update/",
        stages.StageUpdateView.as_view(),
        name="stage-update",
    ),
    # Property Mappings
    path(
        "property-mappings/create/",
        property_mappings.PropertyMappingCreateView.as_view(),
        name="property-mapping-create",
    ),
    path(
        "property-mappings/<uuid:pk>/update/",
        property_mappings.PropertyMappingUpdateView.as_view(),
        name="property-mapping-update",
    ),
    # Outpost Service Connections
    path(
        "outpost_service_connections/create/",
        outposts_service_connections.OutpostServiceConnectionCreateView.as_view(),
        name="outpost-service-connection-create",
    ),
    path(
        "outpost_service_connections/<uuid:pk>/update/",
        outposts_service_connections.OutpostServiceConnectionUpdateView.as_view(),
        name="outpost-service-connection-update",
    ),
]
