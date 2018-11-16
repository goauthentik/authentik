"""passbook URL Configuration"""
from django.urls import include, path

from passbook.admin.views import applications, overview, sources

urlpatterns = [
    path('', overview.AdministrationOverviewView.as_view(), name='overview'),
    path('applications/', applications.ApplicationListView.as_view(),
        name='applications'),
    path('applications/create/', applications.ApplicationCreateView.as_view(),
         name='application-create'),
    path('sources/', sources.SourceListView.as_view(),
         name='sources'),
    path('sources/create/', sources.SourceCreateView.as_view(),
         name='source-create'),
    path('sources/<uuid:pk>/', sources.SourceUpdateView.as_view(),
         name='source-update'),
    # path('api/v1/', include('passbook.admin.api.v1.urls'))
]
