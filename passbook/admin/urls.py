"""passbook URL Configuration"""
from django.urls import path

from passbook.admin.views import applications, overview

urlpatterns = [
    path('', overview.AdministrationOverviewView.as_view(), name='admin-overview'),
    path('applications/', applications.ApplicationListView.as_view(), name='admin-applications'),
    path('applications/create/', applications.ApplicationCreateView.as_view(),
         name='admin-application-create'),
]
