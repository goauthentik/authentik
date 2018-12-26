"""passbook URL Configuration"""
from django.urls import include, path
from rest_framework_swagger.views import get_swagger_view

from passbook.admin.views import (applications, audit, groups, invitations,
                                  overview, providers, rules, sources, users)

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
    # Rules
    path('rules/', rules.RuleListView.as_view(), name='rules'),
    path('rules/create/', rules.RuleCreateView.as_view(), name='rule-create'),
    path('rules/<uuid:pk>/update/', rules.RuleUpdateView.as_view(), name='rule-update'),
    path('rules/<uuid:pk>/delete/', rules.RuleDeleteView.as_view(), name='rule-delete'),
    path('rules/<uuid:pk>/test/', rules.RuleTestView.as_view(), name='rule-test'),
    # Providers
    path('providers/', providers.ProviderListView.as_view(), name='providers'),
    path('providers/create/',
         providers.ProviderCreateView.as_view(), name='provider-create'),
    path('providers/<int:pk>/update/',
         providers.ProviderUpdateView.as_view(), name='provider-update'),
    path('providers/<int:pk>/delete/',
         providers.ProviderDeleteView.as_view(), name='provider-delete'),
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
