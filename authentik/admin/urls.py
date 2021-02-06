"""authentik URL Configuration"""
from django.urls import path

from authentik.admin.views import (
    applications,
    certificate_key_pair,
    events_notifications_rules,
    events_notifications_transports,
    flows,
    groups,
    outposts,
    outposts_service_connections,
    overview,
    policies,
    policies_bindings,
    property_mappings,
    providers,
    sources,
    stages,
    stages_bindings,
    stages_invitations,
    stages_prompts,
    tasks,
    tokens,
    users,
)
from authentik.providers.saml.views import MetadataImportView

urlpatterns = [
    path(
        "overview/cache/flow/",
        overview.FlowCacheClearView.as_view(),
        name="overview-clear-flow-cache",
    ),
    path(
        "overview/cache/policy/",
        overview.PolicyCacheClearView.as_view(),
        name="overview-clear-policy-cache",
    ),
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
    path(
        "applications/<uuid:pk>/delete/",
        applications.ApplicationDeleteView.as_view(),
        name="application-delete",
    ),
    # Tokens
    path("tokens/", tokens.TokenListView.as_view(), name="tokens"),
    path(
        "tokens/<uuid:pk>/delete/",
        tokens.TokenDeleteView.as_view(),
        name="token-delete",
    ),
    # Sources
    path("sources/", sources.SourceListView.as_view(), name="sources"),
    path("sources/create/", sources.SourceCreateView.as_view(), name="source-create"),
    path(
        "sources/<uuid:pk>/update/",
        sources.SourceUpdateView.as_view(),
        name="source-update",
    ),
    path(
        "sources/<uuid:pk>/delete/",
        sources.SourceDeleteView.as_view(),
        name="source-delete",
    ),
    # Policies
    path("policies/", policies.PolicyListView.as_view(), name="policies"),
    path("policies/create/", policies.PolicyCreateView.as_view(), name="policy-create"),
    path(
        "policies/<uuid:pk>/update/",
        policies.PolicyUpdateView.as_view(),
        name="policy-update",
    ),
    path(
        "policies/<uuid:pk>/delete/",
        policies.PolicyDeleteView.as_view(),
        name="policy-delete",
    ),
    path(
        "policies/<uuid:pk>/test/",
        policies.PolicyTestView.as_view(),
        name="policy-test",
    ),
    # Policy bindings
    path(
        "policies/bindings/",
        policies_bindings.PolicyBindingListView.as_view(),
        name="policies-bindings",
    ),
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
    path(
        "policies/bindings/<uuid:pk>/delete/",
        policies_bindings.PolicyBindingDeleteView.as_view(),
        name="policy-binding-delete",
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
    path(
        "providers/<int:pk>/delete/",
        providers.ProviderDeleteView.as_view(),
        name="provider-delete",
    ),
    # Stages
    path("stages/", stages.StageListView.as_view(), name="stages"),
    path("stages/create/", stages.StageCreateView.as_view(), name="stage-create"),
    path(
        "stages/<uuid:pk>/update/",
        stages.StageUpdateView.as_view(),
        name="stage-update",
    ),
    path(
        "stages/<uuid:pk>/delete/",
        stages.StageDeleteView.as_view(),
        name="stage-delete",
    ),
    # Stage bindings
    path(
        "stages/bindings/",
        stages_bindings.StageBindingListView.as_view(),
        name="stage-bindings",
    ),
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
    path(
        "stages/bindings/<uuid:pk>/delete/",
        stages_bindings.StageBindingDeleteView.as_view(),
        name="stage-binding-delete",
    ),
    # Stage Prompts
    path(
        "stages/prompts/",
        stages_prompts.PromptListView.as_view(),
        name="stage-prompts",
    ),
    path(
        "stages/prompts/create/",
        stages_prompts.PromptCreateView.as_view(),
        name="stage-prompt-create",
    ),
    path(
        "stages/prompts/<uuid:pk>/update/",
        stages_prompts.PromptUpdateView.as_view(),
        name="stage-prompt-update",
    ),
    path(
        "stages/prompts/<uuid:pk>/delete/",
        stages_prompts.PromptDeleteView.as_view(),
        name="stage-prompt-delete",
    ),
    # Stage Invitations
    path(
        "stages/invitations/",
        stages_invitations.InvitationListView.as_view(),
        name="stage-invitations",
    ),
    path(
        "stages/invitations/create/",
        stages_invitations.InvitationCreateView.as_view(),
        name="stage-invitation-create",
    ),
    path(
        "stages/invitations/<uuid:pk>/delete/",
        stages_invitations.InvitationDeleteView.as_view(),
        name="stage-invitation-delete",
    ),
    # Flows
    path("flows/", flows.FlowListView.as_view(), name="flows"),
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
    path(
        "flows/<uuid:pk>/export/",
        flows.FlowExportView.as_view(),
        name="flow-export",
    ),
    path(
        "flows/<uuid:pk>/delete/",
        flows.FlowDeleteView.as_view(),
        name="flow-delete",
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
        "property-mappings/<uuid:pk>/delete/",
        property_mappings.PropertyMappingDeleteView.as_view(),
        name="property-mapping-delete",
    ),
    path(
        "property-mappings/<uuid:pk>/test/",
        property_mappings.PropertyMappingTestView.as_view(),
        name="property-mapping-test",
    ),
    # Users
    path("users/", users.UserListView.as_view(), name="users"),
    path("users/create/", users.UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/update/", users.UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", users.UserDeleteView.as_view(), name="user-delete"),
    path(
        "users/<int:pk>/disable/", users.UserDisableView.as_view(), name="user-disable"
    ),
    path("users/<int:pk>/enable/", users.UserEnableView.as_view(), name="user-enable"),
    path(
        "users/<int:pk>/reset/",
        users.UserPasswordResetView.as_view(),
        name="user-password-reset",
    ),
    # Groups
    path("groups/", groups.GroupListView.as_view(), name="groups"),
    path("groups/create/", groups.GroupCreateView.as_view(), name="group-create"),
    path(
        "groups/<uuid:pk>/update/",
        groups.GroupUpdateView.as_view(),
        name="group-update",
    ),
    path(
        "groups/<uuid:pk>/delete/",
        groups.GroupDeleteView.as_view(),
        name="group-delete",
    ),
    # Certificate-Key Pairs
    path(
        "crypto/certificates/",
        certificate_key_pair.CertificateKeyPairListView.as_view(),
        name="certificate_key_pair",
    ),
    path(
        "crypto/certificates/create/",
        certificate_key_pair.CertificateKeyPairCreateView.as_view(),
        name="certificatekeypair-create",
    ),
    path(
        "crypto/certificates/<uuid:pk>/update/",
        certificate_key_pair.CertificateKeyPairUpdateView.as_view(),
        name="certificatekeypair-update",
    ),
    path(
        "crypto/certificates/<uuid:pk>/delete/",
        certificate_key_pair.CertificateKeyPairDeleteView.as_view(),
        name="certificatekeypair-delete",
    ),
    # Outposts
    path(
        "outposts/",
        outposts.OutpostListView.as_view(),
        name="outposts",
    ),
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
    path(
        "outposts/<uuid:pk>/delete/",
        outposts.OutpostDeleteView.as_view(),
        name="outpost-delete",
    ),
    # Outpost Service Connections
    path(
        "outposts/service_connections/",
        outposts_service_connections.OutpostServiceConnectionListView.as_view(),
        name="outpost-service-connections",
    ),
    path(
        "outposts/service_connections/create/",
        outposts_service_connections.OutpostServiceConnectionCreateView.as_view(),
        name="outpost-service-connection-create",
    ),
    path(
        "outposts/service_connections/<uuid:pk>/update/",
        outposts_service_connections.OutpostServiceConnectionUpdateView.as_view(),
        name="outpost-service-connection-update",
    ),
    path(
        "outposts/service_connections/<uuid:pk>/delete/",
        outposts_service_connections.OutpostServiceConnectionDeleteView.as_view(),
        name="outpost-service-connection-delete",
    ),
    # Tasks
    path(
        "tasks/",
        tasks.TaskListView.as_view(),
        name="tasks",
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
    path(
        "events/transports/<uuid:pk>/delete/",
        events_notifications_transports.NotificationTransportDeleteView.as_view(),
        name="notification-transport-delete",
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
    path(
        "events/rules/<uuid:pk>/delete/",
        events_notifications_rules.NotificationRuleDeleteView.as_view(),
        name="notification-rule-delete",
    ),
]
