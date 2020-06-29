"""password stage URLs"""
from django.urls import path

from passbook.stages.password.views import ChangeFlowInitView

urlpatterns = [
    path("<uuid:stage_uuid>/change/", ChangeFlowInitView.as_view(), name="change")
]
