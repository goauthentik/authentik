"""passbook URL Configuration"""
from django.urls import include, path
from rest_framework_swagger.views import get_swagger_view

from passbook.admin.views import (applications, audit, factors, groups,
                                  invitations, overview, policy, providers,
                                  sources, users)

schema_view = get_swagger_view(title='passbook Admin Internal API')


urlpatterns = [
    path('', overview.AdministrationOverviewView.as_view(), name='overview'),
    # Applications
    path('applications/', applications.ApplicationListView.as_view(),
         name='applications'),
    path('applications/create/', applications.ApplicationCreateView.as_view(),
         name='application-create'),
    path('applications/<uuid:pk>/update/',
         applications.ApplicationUpdateView.as_view(), name='application-update'),
    path('applications/<uuid:pk>/delete/',
         applications.ApplicationDeleteView.as_view(), name='application-delete'),
    # Sources
    path('sources/', sources.SourceListView.as_view(), name='sources'),
    path('sources/create/', sources.SourceCreateView.as_view(), name='source-create'),
    path('sources/<uuid:pk>/update/', sources.SourceUpdateView.as_view(), name='source-update'),
    path('sources/<uuid:pk>/delete/', sources.SourceDeleteView.as_view(), name='source-delete'),
    # Policies
    path('policies/', policy.PolicyListView.as_view(), name='policies'),
    path('policies/create/', policy.PolicyCreateView.as_view(), name='policy-create'),
    path('policies/<uuid:pk>/update/', policy.PolicyUpdateView.as_view(), name='policy-update'),
    path('policies/<uuid:pk>/delete/', policy.PolicyDeleteView.as_view(), name='policy-delete'),
    path('policies/<uuid:pk>/test/', policy.PolicyTestView.as_view(), name='policy-test'),
    # Providers
    path('providers/', providers.ProviderListView.as_view(), name='providers'),
    path('providers/create/',
         providers.ProviderCreateView.as_view(), name='provider-create'),
    path('providers/<int:pk>/update/',
         providers.ProviderUpdateView.as_view(), name='provider-update'),
    path('providers/<int:pk>/delete/',
         providers.ProviderDeleteView.as_view(), name='provider-delete'),
    # Factors
    path('factors/', factors.FactorListView.as_view(), name='factors'),
    path('factors/create/',
         factors.FactorCreateView.as_view(), name='factor-create'),
    path('factors/<uuid:pk>/update/',
         factors.FactorUpdateView.as_view(), name='factor-update'),
    path('factors/<uuid:pk>/delete/',
         factors.FactorDeleteView.as_view(), name='factor-delete'),
    # Invitations
    path('invitations/', invitations.InvitationListView.as_view(), name='invitations'),
    path('invitations/create/',
         invitations.InvitationCreateView.as_view(), name='invitation-create'),
    path('invitations/<uuid:pk>/delete/',
         invitations.InvitationDeleteView.as_view(), name='invitation-delete'),
    # Users
    path('users/', users.UserListView.as_view(),
         name='users'),
    path('users/<int:pk>/update/',
         users.UserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/delete/',
         users.UserDeleteView.as_view(), name='user-delete'),
    # Audit Log
    path('audit/', audit.AuditEntryListView.as_view(), name='audit-log'),
    # Groups
    path('groups/', groups.GroupListView.as_view(), name='groups'),
    # API
    path('api/', schema_view),
    path('api/v1/', include('passbook.admin.api.v1.urls'))
]
