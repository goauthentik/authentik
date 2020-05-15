"""passbook URL Configuration"""
from django.urls import path

from passbook.admin.views import (
    applications,
    audit,
    certificate_key_pair,
    debug,
    flows,
    groups,
    inlets,
    invitations,
    outlets,
    overview,
    policies,
    property_mapping,
    stages,
    users,
)

urlpatterns = [
    path("", overview.AdministrationOverviewView.as_view(), name="overview"),
    # Applications
    path(
        "applications/", applications.ApplicationListView.as_view(), name="applications"
    ),
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
    # Inlets
    path("inlets/", inlets.InletListView.as_view(), name="inlets"),
    path("inlets/create/", inlets.InletCreateView.as_view(), name="inlet-create"),
    path(
        "inlets/<uuid:pk>/update/",
        inlets.InletUpdateView.as_view(),
        name="inlet-update",
    ),
    path(
        "inlets/<uuid:pk>/delete/",
        inlets.InletDeleteView.as_view(),
        name="inlet-delete",
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
    # Outlets
    path("outlets/", outlets.OutletListView.as_view(), name="outlets"),
    path("outlets/create/", outlets.OutletCreateView.as_view(), name="outlet-create",),
    path(
        "outlets/<int:pk>/update/",
        outlets.OutletUpdateView.as_view(),
        name="outlet-update",
    ),
    path(
        "outlets/<int:pk>/delete/",
        outlets.OutletDeleteView.as_view(),
        name="outlet-delete",
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
    # Flows
    path("flows/", flows.FlowListView.as_view(), name="flows"),
    path("flows/create/", flows.FlowCreateView.as_view(), name="flow-create",),
    path(
        "flows/<uuid:pk>/update/", flows.FlowUpdateView.as_view(), name="flow-update",
    ),
    path(
        "flows/<uuid:pk>/delete/", flows.FlowDeleteView.as_view(), name="flow-delete",
    ),
    # Property Mappings
    path(
        "property-mappings/",
        property_mapping.PropertyMappingListView.as_view(),
        name="property-mappings",
    ),
    path(
        "property-mappings/create/",
        property_mapping.PropertyMappingCreateView.as_view(),
        name="property-mapping-create",
    ),
    path(
        "property-mappings/<uuid:pk>/update/",
        property_mapping.PropertyMappingUpdateView.as_view(),
        name="property-mapping-update",
    ),
    path(
        "property-mappings/<uuid:pk>/delete/",
        property_mapping.PropertyMappingDeleteView.as_view(),
        name="property-mapping-delete",
    ),
    # Invitations
    path("invitations/", invitations.InvitationListView.as_view(), name="invitations"),
    path(
        "invitations/create/",
        invitations.InvitationCreateView.as_view(),
        name="invitation-create",
    ),
    path(
        "invitations/<uuid:pk>/delete/",
        invitations.InvitationDeleteView.as_view(),
        name="invitation-delete",
    ),
    # Users
    path("users/", users.UserListView.as_view(), name="users"),
    path("users/create/", users.UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/update/", users.UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", users.UserDeleteView.as_view(), name="user-delete"),
    path(
        "users/<int:pk>/reset/",
        users.UserPasswordResetView.as_view(),
        name="user-password-reset",
    ),
    # Groups
    path("group/", groups.GroupListView.as_view(), name="group"),
    path("group/create/", groups.GroupCreateView.as_view(), name="group-create"),
    path(
        "group/<uuid:pk>/update/", groups.GroupUpdateView.as_view(), name="group-update"
    ),
    path(
        "group/<uuid:pk>/delete/", groups.GroupDeleteView.as_view(), name="group-delete"
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
    # Audit Log
    path("audit/", audit.EventListView.as_view(), name="audit-log"),
    # Groups
    path("groups/", groups.GroupListView.as_view(), name="groups"),
    # Debug
    path("debug/request/", debug.DebugRequestView.as_view(), name="debug-request"),
]
