"""passbook app_gw urls"""
from django.urls import path

from passbook.providers.app_gw.views import NginxCheckView

urlpatterns = [
    path('nginx/', NginxCheckView.as_view())
]
