"""passbook app_gw urls"""
from django.urls import path

from passbook.providers.app_gw.views import K8sManifestView

urlpatterns = [
    path('<int:provider>/k8s-manifest/', K8sManifestView.as_view(), name='k8s-manifest'),
]
