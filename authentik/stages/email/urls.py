"""Email stage url patterns"""
from django.urls import path

from authentik.stages.email.views import FromEmailView

urlpatterns = [
    path("from-email/<slug:flow_slug>/", FromEmailView.as_view(), name="from-email"),
]
