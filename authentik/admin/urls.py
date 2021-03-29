"""authentik URL Configuration"""
from django.urls import path

from authentik.admin.views import (
    applications,
    events_notifications_rules,
    events_notifications_transports,
    flows,
    outposts,
    outposts_service_connections,
    policies,
    policies_bindings,
    property_mappings,
    providers,
    sources,
    stages,
    stages_bindings,
    stages_invitations,
    stages_prompts,
)
from authentik.providers.saml.views.metadata import MetadataImportView

urlpatterns = [
    # Applications
    path(
        "applications/create/",
        applications.ApplicationCreateView.as_view(),
        name="application-create",
    ),
    path(
        "applications/<uuid:pk>/update/",
        applications.ApplicationUpdateView.as_view(),
        name="application-update",
    ),
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
    path(
        "policies/<uuid:pk>/test/",
        policies.PolicyTestView.as_view(),
        name="policy-test",
    ),
    # Policy bindings
    path(
        "policies/bindings/create/",
        policies_bindings.PolicyBindingCreateView.as_view(),
        name="policy-binding-create",
    ),
    path(
        "policies/bindings/<uuid:pk>/update/",
        policies_bindings.PolicyBindingUpdateView.as_view(),
        name="policy-binding-update",
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
    # Stage bindings
    path(
        "stages/bindings/create/",
        stages_bindings.StageBindingCreateView.as_view(),
        name="stage-binding-create",
    ),
    path(
        "stages/bindings/<uuid:pk>/update/",
        stages_bindings.StageBindingUpdateView.as_view(),
        name="stage-binding-update",
    ),
    # Stage Prompts
    path(
        "stages_prompts/create/",
        stages_prompts.PromptCreateView.as_view(),
        name="stage-prompt-create",
    ),
    path(
        "stages_prompts/<uuid:pk>/update/",
        stages_prompts.PromptUpdateView.as_view(),
        name="stage-prompt-update",
    ),
    # Stage Invitations
    path(
        "stages/invitations/create/",
        stages_invitations.InvitationCreateView.as_view(),
        name="stage-invitation-create",
    ),
    # Flows
    path(
        "flows/create/",
        flows.FlowCreateView.as_view(),
        name="flow-create",
    ),
    path(
        "flows/import/",
        flows.FlowImportView.as_view(),
        name="flow-import",
    ),
    path(
        "flows/<uuid:pk>/update/",
        flows.FlowUpdateView.as_view(),
        name="flow-update",
    ),
    path(
        "flows/<uuid:pk>/execute/",
        flows.FlowDebugExecuteView.as_view(),
        name="flow-execute",
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
    path(
        "property-mappings/<uuid:pk>/test/",
        property_mappings.PropertyMappingTestView.as_view(),
        name="property-mapping-test",
    ),
    # Outposts
    path(
        "outposts/create/",
        outposts.OutpostCreateView.as_view(),
        name="outpost-create",
    ),
    path(
        "outposts/<uuid:pk>/update/",
        outposts.OutpostUpdateView.as_view(),
        name="outpost-update",
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
    # Event Notification Transpots
    path(
        "events/transports/create/",
        events_notifications_transports.NotificationTransportCreateView.as_view(),
        name="notification-transport-create",
    ),
    path(
        "events/transports/<uuid:pk>/update/",
        events_notifications_transports.NotificationTransportUpdateView.as_view(),
        name="notification-transport-update",
    ),
    # Event Notification Rules
    path(
        "events/rules/create/",
        events_notifications_rules.NotificationRuleCreateView.as_view(),
        name="notification-rule-create",
    ),
    path(
        "events/rules/<uuid:pk>/update/",
        events_notifications_rules.NotificationRuleUpdateView.as_view(),
        name="notification-rule-update",
    ),
]
