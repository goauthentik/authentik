"""passbook URL Configuration"""
from django.urls import path

from passbook.admin.views import applications, overview, sources

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
    path('sources/', sources.SourceListView.as_view(), name='sources'),
    path('sources/create/', sources.SourceCreateView.as_view(), name='source-create'),
    path('sources/<uuid:pk>/update/', sources.SourceUpdateView.as_view(), name='source-update'),
    path('sources/<uuid:pk>/delete/', sources.SourceDeleteView.as_view(), name='source-delete'),
    # path('api/v1/', include('passbook.admin.api.v1.urls'))
]
